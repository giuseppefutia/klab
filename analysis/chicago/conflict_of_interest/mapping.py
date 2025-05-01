entity_mappings = {
    "Person": {
        "uri": "http://xmlns.com/foaf/0.1/Person"
    }
}

data_property_mappings = {
    "Person": {
        "name": {
            "uri": "http://xmlns.com/foaf/0.1/name",
            "type": "str"
        }
    }
}

object_property_mappings = {
    "IS_RELATED_TO": {
        "src_uri": "http://xmlns.com/foaf/0.1/Person",
        "rel_uri": "https://schema.org/relatedTo",
        "dst_uri": "http://xmlns.com/foaf/0.1/Person",
        "query": """
                MATCH 
                (p2:Person)<-[:RECORD_RESOLVED_TO]-(:PersonRecord)-[:WORKS_FOR_DEPARTMENT]->(dept1:Department)-[:IS_SIMILAR_TO]->(dept2:Department)-[:ASSIGNS_CONTRACT]->(:Contract)<-[:INCLUDED_IN_CONTRACT]-(:ContractRecord)-[:HAS_VENDOR]->(vendor1:Organization)-[:BELONGS_TO_ORG_GROUP]-(orgGroup:OrganizationGroup)<-[:BELONGS_TO_ORG_GROUP]-(vendor2:Organization)<-[:WORKS_FOR_ORG]-(p1:Person)
                WHERE 
                vendor1 <> vendor2
                AND p1 <> p2
                AND p1.name <> p2.name
                AND split(toLower(p1.name), " ")[-1] = split(toLower(p2.name), " ")[-1]
                RETURN DISTINCT elementId(p1) as src_id, elementId(p2) as dst_id
        """
    }
}

namespaces = {
    "schema": "http://schema.org/",
    "foaf": "http://xmlns.com/foaf/0.1/"
}