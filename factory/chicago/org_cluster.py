def chi_orgs_similarity_factory(base_importer_cls, backend: str):
    import logging
    
    class ChicagoOrgsSimilarity(base_importer_cls):
        def __init__(self):
            super().__init__()
            self.backend = backend

        def get_record_rows(self, nodes=None):
            query = """
            MATCH (n:Organization)
            WHERE NOT (n.name IS NULL OR n.name = " " OR n.name = "?") AND
                  NOT n:RecordProcessed AND
                  ($nodes IS NULL OR elementId(n) in $nodes)
            RETURN n.id as id
            """
            with self._driver.session(database=self.database) as session:
                result = session.run(query, {"nodes": nodes})
                for record in iter(result):
                    yield dict(record)

        def count_record_rows(self, nodes=None):
            query = """
            MATCH (n:Organization)
            WHERE NOT (n.name IS NULL OR n.name = " " OR n.name = "?") AND
                  NOT n:RecordProcessed AND
                  ($nodes IS NULL OR elementId(n) in $nodes)
            RETURN COUNT(*) as rows
            """
            with self._driver.session(database=self.database) as session:
                return session.run(query, {"nodes": nodes}).single()["rows"]

        def get_cluster_rows(self):
            query = "MATCH (n:OrganizationGroup) RETURN DISTINCT n.clusterId as id"
            with self._driver.session(database=self.database) as session:
                result = session.run(query)
                for record in iter(result):
                    yield dict(record)

        def count_cluster_rows(self):
            query = "MATCH (n:OrganizationGroup) RETURN COUNT(DISTINCT n.clusterId) as rows"
            with self._driver.session(database=self.database) as session:
                return session.run(query).single()["rows"]

        def create_org_similarity_by_address(self, nodes=None):
            query = """
            UNWIND $batch as item
            MATCH (o:Organization {id: item.id})
            SET o:RecordProcessed
            WITH o,
                trim(apoc.text.replace(o.name, '(?i)\\b(?:co|ltd|inc|corp|llc|llp|pvt|gmbh|s.a.|s.l.|and|not)\\b', '')) as clean_name
            WITH o, clean_name,
                apoc.text.split(apoc.text.replace(clean_name, '[^a-zA-Z0-9\\s]', ''), "\\s+") as name_words
            WITH o, clean_name,
                [x IN name_words WHERE size(trim(x)) > 2 AND trim(x) IS NOT NULL AND NOT toLower(x) IN ['and', 'not']] as valid_name_words
            WHERE size(valid_name_words) > 0
            CALL db.index.fulltext.queryNodes(
                "organization_name",
                apoc.text.join([x IN valid_name_words | trim(x) + "~0.3"], " AND ")
            )
            YIELD node, score
            WHERE node <> o AND NOT EXISTS ((node)-[:IS_SIMILAR_TO]-(o))
            WITH o, clean_name, node,
                trim(apoc.text.replace(node.name, '(?i)\\b(?:co|ltd|inc|corp|llc|llp|pvt|gmbh|s.a.|s.l.|and|not)\\b', '')) as clean_node_name
            WITH o, clean_name, node, clean_node_name,
                apoc.text.sorensenDiceSimilarity(clean_name, clean_node_name) as simil
            WHERE simil > 0.3
            MATCH (o)-[:HAS_ADDRESS]->(a:Address)<-[:HAS_ADDRESS]-(node)
            MERGE (node)-[r:IS_SIMILAR_TO {method: "SIMILAR_NAME+SAME_ADDRESS"}]->(o)
            ON CREATE SET r.score = simil
            """
            size = self.count_record_rows()
            self.batch_store(query, self.get_record_rows(nodes), size=size)

        def project_graph(self, node_label='Organization'):
            query = """
            CALL gds.graph.project(
                'organizationResolved',
                [$node_label],
                ['IS_SIMILAR_TO']
            )
            YIELD graphName, nodeCount, relationshipCount
            RETURN graphName, nodeCount, relationshipCount
            """
            with self._driver.session(database=self.database) as session:
                session.run(query, {"node_label": node_label})

        def run_wcc(self):
            query = """
            CALL gds.wcc.write('organizationResolved', { writeProperty: 'componentId' })
            YIELD nodePropertiesWritten, componentCount;
            """
            with self._driver.session(database=self.database) as session:
                session.run(query)

        def delete_projection(self):
            query = "CALL gds.graph.drop('organizationResolved')"
            with self._driver.session(database=self.database) as session:
                session.run(query)

        def create_record_clusters(self):
            query = """
            CALL apoc.periodic.iterate(
                \"MATCH (n:Organization) RETURN DISTINCT n.componentId as id\",
                \"MERGE (n:OrganizationGroup {clusterId: id})\",
                {batchSize:10000})
            YIELD batches, total RETURN batches, total
            """
            with self._driver.session(database=self.database) as session:
                session.run(query)

        def create_connections_to_clusters(self):
            query = """
            UNWIND $batch as item
            MATCH (p:Organization {componentId: item.id})
            MATCH (c:OrganizationGroup {clusterId: item.id})
            MERGE (p)-[:BELONGS_TO_ORG_GROUP]->(c)
            SET c.ids = apoc.coll.toSet(coalesce(c.ids, []) + coalesce(toString(p.id), [])),
                c.names = apoc.coll.toSet(coalesce(c.names, []) + coalesce(p.name, [])),
                c.sources = apoc.coll.toSet(coalesce(c.sources, []) + coalesce(p.source, []))
            """
            size = self.count_cluster_rows()
            self.batch_store(query, self.get_cluster_rows(), size=size)

        def create_final_names_of_clusters(self):
            query = """
            UNWIND $batch as item
            MATCH (c:OrganizationGroup {clusterId: item.id})
            WITH c, reduce(shortest = head(c.names), name IN c.names | CASE WHEN size(name) < size(shortest) THEN name ELSE shortest END) AS shortestName
            SET c.name = shortestName
            """
            size = self.count_cluster_rows()
            self.batch_store(query, self.get_cluster_rows(), size=size)
        
        def apply_updates(self):
                logging.info("Creating similarity IS_SIMILAR_TO relationships...")
                self.create_org_similarity_by_address()
                
                logging.info("Creating graph projection...")
                self.project_graph()
                
                logging.info("Running WCC algorithm...")
                self.run_wcc()
                
                logging.info("Deleting projection...")
                self.delete_projection()
                
                logging.info("Creating organization clusters...")
                self.create_record_clusters()
                
                logging.info("Creating connections to clusters...")
                self.create_connections_to_clusters()
                
                logging.info("Creating cluster names...")
                self.create_final_names_of_clusters()

    return ChicagoOrgsSimilarity

if __name__ == '__main__':
    from util.cli_entry import run_backend_importer

    run_backend_importer(
        chi_orgs_similarity_factory,
        description="Run Chicago Organization Similarity pipeline with selected backend.",
        file_help="No file needed.",
        default_base_path="./data/chicago/",
        require_file=False
    )
