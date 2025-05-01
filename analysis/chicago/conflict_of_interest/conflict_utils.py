object_property_mappings = {
        "IS_RELATED_TO": {
            "src_uri": "http://xmlns.com/foaf/0.1/Person",
            "rel_uri": "https://schema.org/relatedTo",
            "dst_uri": "http://xmlns.com/foaf/0.1/Person",
            "query": """
                MATCH 
                    (p2:Person)<-[:RECORD_RESOLVED_TO]-(:PersonRecord)
                    -[:WORKS_FOR_DEPARTMENT]->(dept1:Department)
                    -[:IS_SIMILAR_TO]->(dept2:Department)
                    -[:ASSIGNS_CONTRACT]->(:Contract)<-[:INCLUDED_IN_CONTRACT]-(c:ContractRecord)
                    -[:HAS_VENDOR]->(vendor1:Organization)
                    -[:BELONGS_TO_ORG_GROUP]->(orgGroup:OrganizationGroup)<-[:BELONGS_TO_ORG_GROUP]-
                    (vendor2:Organization)<-[:WORKS_FOR_ORG]-(p1:Person)
                WHERE 
                    (
                        elementId(p2) = $node_id OR 
                        elementId(p1) = $node_id
                    )
                    AND vendor1 <> vendor2
                    AND p1 <> p2
                    AND toLower(p1.name) <> toLower(p2.name)
                    AND split(toLower(p1.name), " ")[-1] = split(toLower(p2.name), " ")[-1]
                RETURN DISTINCT 
                    p1 AS personWorkingForDepartment, 
                    dept2 AS department, 
                    p2 AS personWorkingForOrganization, 
                    collect(DISTINCT c.id + " - " + c.name + " - Amount: " + toString(c.amount) + "$") AS contractRecordDetails, 
                    vendor2 AS organization

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
