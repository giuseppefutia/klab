def chi_people_similarity_factory(base_importer_cls, backend: str):
    import logging

    class ChicagoPeopleSimilarity(base_importer_cls):
        def __init__(self):
            super().__init__()
            self.backend = backend
            self.batch_size = 500

        def get_record_rows(self, nodes=None):
            query = """
            MATCH (n:PersonRecord)
            WHERE NOT (n.fullName IS NULL OR n.fullName = " " OR n.fullName = "?") AND
                  NOT n:RecordProcessed AND
                  ($nodes IS NULL OR elementId(n) in $nodes)
            RETURN n.id as id
            """
            with self._driver.session() as session:
                result = session.run(query, {"nodes": nodes})
                for record in iter(result):
                    yield dict(record)

        def count_record_rows(self, nodes=None):
            query = """
            MATCH (n:PersonRecord)
            WHERE NOT (n.fullName IS NULL OR n.fullName = " " OR n.fullName = "?") AND
                  NOT n:RecordProcessed AND
                  ($nodes IS NULL OR elementId(n) in $nodes)
            RETURN COUNT(*) as rows
            """
            with self._driver.session() as session:
                return session.run(query, {"nodes": nodes}).single()["rows"]

        def get_cluster_rows(self):
            query = """MATCH (n:Person) RETURN DISTINCT n.clusterId as id"""
            with self._driver.session() as session:
                result = session.run(query)
                for record in iter(result):
                    yield dict(record)

        def count_cluster_rows(self):
            query = """MATCH (n:Person) RETURN COUNT(DISTINCT n.clusterId) as rows"""
            with self._driver.session() as session:
                return session.run(query).single()["rows"]

        def create_people_similarity(self, nodes=None):
            query = """
            UNWIND $batch as item
            MATCH (p:PersonRecord {id: item.id})
            SET p:RecordProcessed
            WITH p, p.fullName as name,
                 apoc.text.split(apoc.text.replace(p.fullName ,'[^a-zA-Z0-9\\s]', ''), "\\s+") as name_words
            WHERE size(name_words) > 0
            CALL db.index.fulltext.queryNodes(
                "person_record_fullName",
                apoc.text.join([x IN name_words | trim(x) + "~0.65"], " AND ")
            )
            YIELD node, score
            WITH p, name, node
            WHERE p <> node
            WITH p, node, apoc.text.sorensenDiceSimilarity(name, node.fullName) as simil
            WHERE simil > 0.695
            MERGE (node)-[r:IS_SIMILAR_TO {method: "SIMILAR_NAME"}]->(p)
            ON CREATE SET r.score = simil
            """
            size = self.count_record_rows(nodes)
            self.batch_store(query, self.get_record_rows(nodes), size=size)

        def project_wcc_graph(self):
            query = """
            CALL gds.graph.project('personWcc', ['PersonRecord'], ['IS_SIMILAR_TO'])
            YIELD graphName, nodeCount, relationshipCount
            RETURN graphName, nodeCount, relationshipCount
            """
            with self._driver.session() as session:
                session.run(query)

        def run_wcc(self):
            query = """
            CALL gds.wcc.write('personWcc', { writeProperty: 'componentId' })
            YIELD nodePropertiesWritten, componentCount;
            """
            with self._driver.session() as session:
                session.run(query)

        def delete_wcc_projection(self):
            query = "CALL gds.graph.drop('personWcc')"
            with self._driver.session() as session:
                session.run(query)

        def create_record_clusters(self):
            query = """
            CALL apoc.periodic.iterate(
                "MATCH (n:PersonRecord) RETURN DISTINCT n.componentId as id",
                "MERGE (n:Person {clusterId: id})",
                {batchSize:10000})
            YIELD batches, total RETURN batches, total
            """
            with self._driver.session() as session:
                session.run(query)

        def create_connections_to_clusters(self):
            query = """
            UNWIND $batch as item
            MATCH (p:PersonRecord {componentId: item.id})
            MATCH (c:Person {clusterId: item.id})
            MERGE (p)-[:RECORD_RESOLVED_TO]->(c)
            SET c.fullNames = coalesce(c.fullNames, []) + p.fullName,
                c.employerIds = coalesce(c.employerIds, []) + p.employerId,
                c.titles = coalesce(c.titles, []) + p.title
            """
            size = self.count_cluster_rows()
            self.batch_store(query, self.get_cluster_rows(), size=size)

        def create_final_names_of_clusters(self):
            query = """
            UNWIND $batch as item
            MATCH (c:Person {clusterId: item.id})
            WITH c, reduce(shortest = head(c.fullNames), name IN c.fullNames |
                           CASE WHEN size(name) < size(shortest) THEN name ELSE shortest END) AS shortestName
            SET c.name = shortestName
            """
            size = self.count_cluster_rows()
            self.batch_store(query, self.get_cluster_rows(), size=size)

        def project_louvain_graph(self):
            query = """
            MATCH (source:PersonRecord)-[r:IS_SIMILAR_TO]->(target:PersonRecord)
            RETURN gds.graph.project(
                'personLouvain',
                source,
                target,
                { relationshipProperties: r { .score } },
                { undirectedRelationshipTypes: ['*'] }
            )
            """
            with self._driver.session() as session:
                session.run(query)

        def run_louvain(self):
            query = """
            CALL gds.louvain.write('personLouvain', {
                relationshipWeightProperty: 'score',
                writeProperty: 'louvainIntermediateCommunities',
                includeIntermediateCommunities: true
            })
            YIELD communityCount, modularity, modularities
            """
            with self._driver.session() as session:
                session.run(query)

        def set_louvain_cluster(self):
            query = """
            MATCH (p:PersonRecord)
            SET p.louvain = toIntegerList(p.louvainIntermediateCommunities)[0]
            """
            with self._driver.session() as session:
                session.run(query)

        def delete_louvain_projection(self):
            query = "CALL gds.graph.drop('personLouvain')"
            with self._driver.session() as session:
                session.run(query)
        
        def apply_updates(self):
            logging.info("Creating similarity IS_SIMILAR_TO relationships...")
            self.create_people_similarity()
            
            logging.info("Creating WCC graph projection...")
            self.project_wcc_graph()
            
            logging.info("Running WCC algorithm...")
            self.run_wcc()
            
            logging.info("Deleting WCC projection...")
            self.delete_wcc_projection()
            
            logging.info("Creating person clusters...")
            self.create_record_clusters()

            logging.info("Creating connections to clusters...")
            self.create_connections_to_clusters()
            
            logging.info("Creating cluster names...")
            self.create_final_names_of_clusters()
            
            logging.info("Creating Louvain projection....")
            self.project_louvain_graph()
            
            logging.info("Running Louvain algorithm...")
            self.run_louvain()
            
            logging.info("Set Louvain cluster...")
            self.set_louvain_cluster()
            
            logging.info("Deleting Louvain projection...")
            self.delete_louvain_projection()

    return ChicagoPeopleSimilarity

if __name__ == '__main__':
    from util.cli_entry import run_backend_importer

    run_backend_importer(
        chi_people_similarity_factory,
        description="Run Chicago People Similarity pipeline with selected backend.",
        file_help="No file needed.",
        default_base_path="./data/chicago/",
        require_file=False
    )