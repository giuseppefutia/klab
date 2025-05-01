object_property_mappings = {
        "IS_RELATED_TO": {
            "src_uri": "http://xmlns.com/foaf/0.1/Person",
            "rel_uri": "http://purl.org/procurement/public-contracts#hasSupplier",
            "dst_uri": "http://purl.org/procurement/public-contracts#Contract",
            "query": """
                MATCH (pr:PersonRecord)-[:RECORD_RESOLVED_TO]->(p:Person)
                -[:WORKS_FOR_ORG]->(:Organization)
                -[:BELONGS_TO_ORG_GROUP]->(:OrganizationGroup)<-[:BELONGS_TO_ORG_GROUP]-
                (o:Organization)<-[:HAS_VENDOR]-(c:ContractRecord)-[:INCLUDED_IN_CONTRACT]->(x:Contract)

                WHERE elementId(p) = $node_id
                AND c.amount <> 0
                WITH 
                p.name AS personName,
                collect(DISTINCT pr.fullName) AS fullNames,
                collect(DISTINCT o.name) AS orgNames,
                collect(DISTINCT 
                    c.id + " - " + c.name + " - Amount: " + toString(c.amount) + "$"
                ) AS contractRecordDetails,
                toString(sum(DISTINCT c.amount)) + "$" AS totalAmount

                RETURN 
                personName,
                fullNames,
                orgNames,
                contractRecordDetails,
                totalAmount
                LIMIT 10
            """
        }
    }

def run_explainability_query(neo4j_graph, nodes_with_issues):
    enriched_results = []
    with neo4j_graph._driver.session() as session:
        for full_uri in nodes_with_issues:
            # Safely extract node_id
            if isinstance(full_uri, dict) and "focus_node" in full_uri:
                node_id = full_uri["focus_node"].split("/")[-1]
            elif isinstance(full_uri, str):
                node_id = full_uri.split("/")[-1]
            else:
                continue  # or raise an error

            context = {"node": node_id, "results": []}
            for mapping_name, mapping in object_property_mappings.items():
                query = mapping["query"]
                result = session.run(query, node_id=node_id)
                context["results"].append({
                    "mapping": mapping_name,
                    "query": query,
                    "data": [r.data() for r in result]
                })

            enriched_results.append(context)
    return enriched_results
