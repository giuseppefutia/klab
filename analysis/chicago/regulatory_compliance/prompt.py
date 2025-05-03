SHACL_PROMPTS = {
    "rdf_schema":
        """@prefix gr: <http://purl.org/goodrelations/v1#> .
           @prefix pco: <http://purl.org/procurement/public-contracts#> .
           @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

           # Assume: gr:BusinessEntity, gr:hasLicense, pco:actualEndDate, pco:bidder, pco:startDate
        """,

    "message":
        """
        - Find organizations (?this) where the end date of their latest license is earlier than the start date of their earliest contract.
        - For each organization, get the maximum pco:actualEndDate from licenses linked by gr:hasLicense and the minimum pco:startDate from contracts linked by pco:bidder.
        - Use subqueries to calculate these values, including ?this and the aggregated date (MAX or MIN) in both the SELECT and WHERE clauses of each subquery.
        - Only return organizations where the newest license end date is before the oldest contract start date.
        - Make sure to follow the correct relationship directions.
        - Use the full URLs within the generated SPARQL query.
        """,

    "template":
        """You are an expert in SHACL and SPARQL.

        Given the following RDF schema (Turtle format):
        {rdf_schema}

        And the given message:
        "{message}"

        Write only the SPARQL SELECT query that enforces this rule. 
        Do not include any explanations, comments, SHACL syntax, sparql or RDF prefixes.
        Do not include any sparql quote. 
        Output only the raw SPARQL query, starting directly with SELECT.
        """
}


AGENT_PROMPTS = {
    "explain":
        """ "Please perform the following:\n"
        "0. Based on the RDF schema and a message of the validation goal, generate a SPARQL query for SHACL validation. {rdf_schema}, {message}\n"
        "   a. Report also the generated SPARQL query for SHACL validation.\n"
        "1. Run the SHACL validation and summarize the SHACL validation issues.\n"
        "2. Explain how each issue can be fixed.\n"
        "3. List the id of all the affected nodes.\n"
        "4. For each node:\n"
        "   a. Execute Cypher query on the Neo4j database to gather additional details.\n"
        "   b. Use the results to expand on why the issue was triggered.\n"
        "5. Report the details about all the nodes: prioritize `ContractRecord` and `LicenseRecord` details and the names of `contractOrg` and `licenseOrg`.\n"
        "Pay special attention to relevant date fields and information that helps explain the reason for the validation error.\n\n" """
}
