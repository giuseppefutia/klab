entity_mappings = {
    "Contract": {
        "uri": "http://purl.org/procurement/public-contracts#Contract",
        "query": """
            MATCH (n:Contract)<-[:INCLUDED_IN_CONTRACT]-(:ContractRecord)-[:HAS_VENDOR]->(:Organization)-[:BELONGS_TO_ORG_GROUP]->(o:OrganizationGroup)
            WHERE elementId(o) STARTS WITH "4:abd68729-dd06-4625-953e-eb0794c34b91:272" OR
                  elementId(o) STARTS WITH "4:abd68729-dd06-4625-953e-eb0794c34b91:271"
            RETURN DISTINCT n
            """
    },
    "OrganizationGroup": {
        "uri": "http://purl.org/goodrelations/v1#BusinessEntity",
        "query": """
            MATCH (n:OrganizationGroup)
            WHERE elementId(n) STARTS WITH "4:abd68729-dd06-4625-953e-eb0794c34b91:272" OR
                  elementId(n) STARTS WITH "4:abd68729-dd06-4625-953e-eb0794c34b91:271"
            RETURN DISTINCT n
            """
    },
    "LicenseRecord": {
        "uri": "http://purl.org/goodrelations/v1#License",
        "query": """
            MATCH (n:LicenseRecord)<-[:ORG_HAS_LICENSE]-(:Organization)-[:BELONGS_TO_ORG_GROUP]->(o:OrganizationGroup)
            WHERE elementId(o) STARTS WITH "4:abd68729-dd06-4625-953e-eb0794c34b91:272" OR
                  elementId(o) STARTS WITH "4:abd68729-dd06-4625-953e-eb0794c34b91:271"
            RETURN DISTINCT n"""

    }
}

data_property_mappings = {
    "Contract": {
        "name": {
            "uri": "http://purl.org/dc/terms/title",
            "type": "str"
        },
        "startDate": {
            "uri": "http://purl.org/procurement/public-contracts#startDate",
            "type": "date"
        },
        "endDate": {
            "uri": "http://purl.org/procurement/public-contracts#actualEndDate",
            "type": "date"
        }
    },
    "LicenseRecord": {
        "name": {
            "uri": "http://purl.org/dc/terms/title",
            "type": "str"
        }
    },
    "OrganizationGroup": {
        "name": {
            "uri": "http://purl.org/dc/terms/title",
            "type": "str"
        }
    }
}

computed_data_property_mappings = {
    "Contract.amount": {
        "uri": "http://purl.org/procurement/public-contracts#contractPrice",
        "type": "float",
        "query": """
            MATCH (c:Contract)<-[:INCLUDED_IN_CONTRACT]-(r:ContractRecord) 
            WHERE elementId(c) = $node_id
            RETURN sum(r.amount) as value
        """
    },
    "LicenseRecord.startDate": {
        "uri": "http://purl.org/procurement/public-contracts#startDate",
        "type": "date",
        "query": """
            MATCH (l:LicenseRecord)
            WHERE elementId(l) = $node_id
            RETURN toString(apoc.date.format(
                apoc.date.parse(l.startDate, "ms", "MM/dd/yyyy"),
                "ms",
                "yyyy-MM-dd"
            )) AS value
        """
    },
    "LicenseRecord.endDate": {
        "uri": "http://purl.org/procurement/public-contracts#actualEndDate",
        "type": "date",
        "query": """
            MATCH (l:LicenseRecord)
            WHERE elementId(l) = $node_id
            RETURN toString(apoc.date.format(
                apoc.date.parse(l.endDate, "ms", "MM/dd/yyyy"),
                "ms",
                "yyyy-MM-dd"
            )) AS value
        """
    }
}

object_property_mappings = {
    "HAS_VENDOR": {
        "src_uri": "http://purl.org/procurement/public-contracts#Contract",
        "rel_uri": "http://purl.org/procurement/public-contracts#bidder",
        "dst_uri": "http://purl.org/goodrelations/v1#BusinessEntity",
        "query": """
            MATCH (c:Contract)<-[:INCLUDED_IN_CONTRACT]-(:ContractRecord)-[:HAS_VENDOR]->(:Organization)-[:BELONGS_TO_ORG_GROUP]->(o:OrganizationGroup)
            WHERE elementId(o) STARTS WITH "4:abd68729-dd06-4625-953e-eb0794c34b91:272" OR
                  elementId(o) STARTS WITH "4:abd68729-dd06-4625-953e-eb0794c34b91:271"
            RETURN DISTINCT elementId(c) as src_id, elementId(o) as dst_id
        """
    },
    "HAS_LICENSE": {
        "src_uri": "http://purl.org/goodrelations/v1#BusinessEntity",
        "rel_uri": "http://purl.org/goodrelations/v1#hasLicense",
        "dst_uri": "http://purl.org/goodrelations/v1#License",
        "query": """
            MATCH (l:LicenseRecord)<-[:ORG_HAS_LICENSE]-(:Organization)-[:BELONGS_TO_ORG_GROUP]->(o:OrganizationGroup)
            WHERE elementId(o) STARTS WITH "4:abd68729-dd06-4625-953e-eb0794c34b91:272" OR
                  elementId(o) STARTS WITH "4:abd68729-dd06-4625-953e-eb0794c34b91:271"
            RETURN DISTINCT elementId(o) as src_id, elementId(l) as dst_id
        """
    }
}

namespaces = {
    "pc": "http://purl.org/procurement/public-contracts#",
    "dc": "http://purl.org/dc/terms/",
    "adms": "http://www.w3.org/ns/adms#",
    "schema": "http://schema.org/",
    "gr": "http://purl.org/goodrelations/v1#"
}