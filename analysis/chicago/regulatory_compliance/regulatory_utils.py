object_property_mappings = {
        "HAS_VENDOR": {
            "dst_uri": "http://purl.org/goodrelations/v1#BusinessEntity",
            "query": """MATCH path=(c:Contract)<-[:INCLUDED_IN_CONTRACT]-(contractRecord:ContractRecord)-[:HAS_VENDOR]->(contractOrg:Organization)-[:BELONGS_TO_ORG_GROUP]->(o:OrganizationGroup)
                        WHERE elementId(o) = $node_id
                        RETURN DISTINCT contractRecord, contractOrg"""
        },
        "HAS_LICENSE": {
            "dst_uri": "http://purl.org/goodrelations/v1#BusinessEntity",
            "query": """MATCH path=(licenseRecord:LicenseRecord)<-[:ORG_HAS_LICENSE]-(licenseOrg:Organization)-[:BELONGS_TO_ORG_GROUP]->(o:OrganizationGroup)
                        WHERE elementId(o) = $node_id
                        RETURN DISTINCT licenseRecord, licenseOrg"""
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
