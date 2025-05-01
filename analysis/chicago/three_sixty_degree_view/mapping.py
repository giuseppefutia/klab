entity_mappings = {
    "Person": {
        "uri": "http://xmlns.com/foaf/0.1/Person",
        "query": f"""
            MATCH (pr:PersonRecord)-[:RECORD_RESOLVED_TO]->(n:Person)
                -[:WORKS_FOR_ORG]->(:Organization)
                -[:BELONGS_TO_ORG_GROUP]->(:OrganizationGroup)<-[:BELONGS_TO_ORG_GROUP]-
                (o:Organization)<-[:HAS_VENDOR]-(c:ContractRecord)-[:INCLUDED_IN_CONTRACT]->(:Contract)
            WHERE NOT n.name IN ["R Patel", "Li Ji", "Ali Ali", "Kathleen"]
            AND c.amount <> 0
            RETURN DISTINCT n
            LIMIT 5
        """
    },
    "Contract": {
        "uri": "http://purl.org/procurement/public-contracts#Contract",
        "query": f"""
            MATCH (pr:PersonRecord)-[:RECORD_RESOLVED_TO]->(p:Person)
                -[:WORKS_FOR_ORG]->(:Organization)
                -[:BELONGS_TO_ORG_GROUP]->(:OrganizationGroup)<-[:BELONGS_TO_ORG_GROUP]-
                (o:Organization)<-[:HAS_VENDOR]-(c:ContractRecord)-[:INCLUDED_IN_CONTRACT]->(n:Contract)
            WHERE NOT p.name IN ["R Patel", "Li Ji", "Ali Ali", "Kathleen"]
            AND c.amount <> 0
            RETURN DISTINCT n
            LIMIT 5
        """
    }
}

data_property_mappings = {
    "Person": {
        "name": {
            "uri": "http://xmlns.com/foaf/0.1/name",
            "type": "str"
        }
    },
    "Contract": {
        "name": {
            "uri": "http://purl.org/dc/terms/title",
            "type": "str"
        }
    }
}

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
            WHERE NOT p.name IN ["R Patel", "Li Ji", "Ali Ali", "Kathleen"]
            AND c.amount <> 0
            RETURN DISTINCT elementId(p) as src_id, elementId(x) as dst_id
            LIMIT 5
                
        """
    }
}

namespaces = {
    "schema": "https://schema.org/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "pc": "http://purl.org/procurement/public-contracts#",
    "dc": "http://purl.org/dc/terms/"
}