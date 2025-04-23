from rdflib import Namespace, URIRef, Literal, Graph
from rdflib.namespace import RDF, XSD
from tqdm import tqdm

from database.neo4j_db import Neo4jGraphDB


class Neo4jToRDFConverter:
    def __init__(self, entity_mappings,
                       data_property_mappings,
                       computed_data_property_mappings,
                       object_property_mappings,
                       namespaces):
        self.entity_mappings = entity_mappings
        self.data_property_mappings = data_property_mappings
        self.computed_data_property_mappings = computed_data_property_mappings
        self.object_property_mappings = object_property_mappings
        self.namespaces = namespaces
        self.batch_size = 5000

        self.graph = Graph()
        self.driver = Neo4jGraphDB()._driver
        self._bind_namespaces(self.graph)

    def _bind_namespaces(self, graph):
        for prefix, uri in self.namespaces.items():
            graph.bind(prefix, Namespace(uri))

    def _get_node_count(self, session, label, filter_clause=None, query=None):
        if query:
            cypher = f"""
            CALL () {{
                {query}
            }}
            RETURN count(*) AS total
            """
        else:
            cypher = f"MATCH (n:{label})"
            if filter_clause:
                cypher += f" {filter_clause}"
            cypher += " RETURN count(n) AS total"

        result = session.run(cypher)
        return result.single()["total"]

    def _fetch_nodes_batch(self, session, label, offset, filter_clause=None, query=None):
        if query:
            cypher = f"""
            CALL () {{
                {query}
            }}
            RETURN n
            SKIP $offset
            LIMIT $limit
            """
        else:
            cypher = f"""
            MATCH (n:{label})
            {filter_clause or ""}
            RETURN n
            SKIP $offset
            LIMIT $limit
            """

        return list(session.run(cypher, offset=offset, limit=self.batch_size))

    def _add_node_to_graph(self, session, node_label, node_data, base_uri, graph):
        node_id = node_data.element_id
        subject_uri = URIRef(f"{base_uri}/{node_id}")

        graph.add((subject_uri, RDF.type, URIRef(base_uri)))

        for prop, prop_info in self.data_property_mappings.get(node_label, {}).items():
            if prop not in node_data._properties:
                continue

            value = node_data._properties[prop]
            predicate_uri = URIRef(prop_info["uri"])

            if prop_info["type"] == "list" and isinstance(value, list):
                for item in value:
                    graph.add((subject_uri, predicate_uri, Literal(item)))
            elif prop_info["type"] == "date":
                graph.add((subject_uri, predicate_uri, Literal(value, datatype=XSD.date)))
            else:
                graph.add((subject_uri, predicate_uri, Literal(value)))

        self._handle_computed_properties(session, node_label, node_id, subject_uri, graph)

    def _handle_computed_properties(self, session, node_label, node_id, subject_uri, graph):
        for full_key, mapping in self.computed_data_property_mappings.items():
            label, prop = full_key.split(".")

            if label != node_label:
                continue

            predicate_uri = URIRef(mapping["uri"])
            cypher_query = mapping["query"]
            data_type = mapping["type"]

            result = session.run(cypher_query, node_id=node_id)

            for record in result:
                value = record["value"]
                if value is not None:
                    if data_type == "float":
                        graph.add((subject_uri, predicate_uri, Literal(value, datatype=XSD.float)))
                    elif data_type == "date":
                        graph.add((subject_uri, predicate_uri, Literal(value, datatype=XSD.date)))
                    else:
                        graph.add((subject_uri, predicate_uri, Literal(value)))

    def _handle_object_properties(self, session, output_file=None, serialization_format="turtle"):
        for relation, mapping in self.object_property_mappings.items():
            src_base_uri = mapping["src_uri"]
            rel_uri = mapping["rel_uri"]
            dst_base_uri = mapping["dst_uri"]
            cypher_query = mapping["query"]

            count_query = f"""
            CALL () {{ WITH *
                {cypher_query}
            }}
            RETURN count(*) AS total
            """

            total = session.run(count_query).single()["total"]
            offset = 0

            with tqdm(total=total, desc=f"Processing relation {relation}", unit="rel") as pbar:
                while offset < total:
                    paginated_query = f"""
                    CALL () {{ WITH *
                        {cypher_query}
                    }}
                    RETURN src_id, dst_id
                    SKIP $offset
                    LIMIT $limit
                    """

                    result = session.run(paginated_query, offset=offset, limit=self.batch_size)

                    batch_graph = Graph()
                    self._bind_namespaces(batch_graph)

                    count = 0
                    for record in result:
                        src_id = record["src_id"]
                        dst_id = record["dst_id"]

                        if not src_id or not dst_id:
                            continue

                        subject_uri = URIRef(f"{src_base_uri}/{src_id}")
                        predicate_uri = URIRef(rel_uri)
                        object_uri = URIRef(f"{dst_base_uri}/{dst_id}")

                        batch_graph.add((subject_uri, predicate_uri, object_uri))
                        count += 1

                    if output_file:
                        with open(output_file, "a", encoding="utf-8") as f:
                            f.write(batch_graph.serialize(format=serialization_format))

                    offset += self.batch_size
                    pbar.update(count)

    def convert(self, output_file=None, serialization_format="turtle") -> Graph:
        with self.driver.session() as session:
            for label, mapping in self.entity_mappings.items():
                base_uri = mapping["uri"] if isinstance(mapping, dict) else mapping
                filter_clause = mapping.get("filter", "") if isinstance(mapping, dict) else ""
                query = mapping.get("query", None) if isinstance(mapping, dict) else None

                total = self._get_node_count(session, label, filter_clause, query)
                offset = 0

                with tqdm(total=total, desc=f"Processing {label}", unit="node") as pbar:
                    while True:
                        records = self._fetch_nodes_batch(session, label, offset, filter_clause, query)
                        if not records:
                            break

                        batch_graph = Graph()
                        self._bind_namespaces(batch_graph)

                        for record in records:
                            self._add_node_to_graph(session, label, record["n"], base_uri, batch_graph)

                        if output_file:
                            with open(output_file, "ab") as f:
                                f.write(batch_graph.serialize(format=serialization_format).encode("utf-8"))

                        offset += self.batch_size
                        pbar.update(len(records))

            self._handle_object_properties(session, output_file=output_file, serialization_format=serialization_format)

        return self.graph

    def serialize(self, format="turtle") -> str:
        return self.graph.serialize(format=format)