SHACL_PROMPTS = {
    "rdf_schema": 
        """@prefix foaf: <http://xmlns.com/foaf/0.1/> .
           @prefix pc: <http://purl.org/procurement/public-contracts#> .
           @prefix schema: <https://schema.org/> .
           @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

           # Assume: foaf:Person, foaf:name (xsd:string), schema:relatedTo, pc:hasSupplier (foaf:Person -> pc:Contract)
        """,

    "message":
        """
        Define a SHACL NodeShape named <#SupplierShape> for persons (foaf:Person) to ensure that they have a pc:hasSupplier link.
        - Constraint: The maximum number of pc:hasSupplier relationships must be 0.
        - Message: "A person is associated to a contract via pc:hasSupplier."
        """,

    "template":
        """
        You are an expert in SHACL and RDF validation.

        Given the following RDF schema:
        {rdf_schema}

        And the following instruction:
        "{message}"

        Write only the SHACL NodeShape in Turtle syntax.

        Important formatting rules:
        - Use exactly the NodeShape URI <#SuppliersShape>.
        - Include all necessary prefixes.
        - Do NOT add any ```turtle, ``` or other code block markers.
        - Do NOT add any extra text, explanation, or comments.
        - Start directly with prefixes, followed by the SHACL shape.
        - Output must be pure Turtle syntax, as it would appear inside an RDF file.

        Only output the pure content. Nothing else.
        """
}


AGENT_PROMPTS = {
    "explain":
        """
        Please perform the following tasks:

        0. Based on the RDF schema and the message describing the validation goal, generate a SHACL NodeShape in Turtle syntax. 
        Use the provided RDF schema and message:
        {rdf_schema}
        {message}

        1. Run SHACL validation using the generated NodeShape. This SHACL validation is useful just for reporting reasons, not to raise any issue.

        2. List all detected RDF nodes (subjects).

        3. For each detected node:
            a. Run a Cypher query to gather additional related details from the graph database, including the type of relationship if available.
            b. Use the gathered information to expand the details about the detected nodes.
        
        4. Prioritize and highlight:
            - Map the Person (listing all the fullNames) to the correct related ContractRecord.
            - Details about ALL ContractRecord amounts and the total amount.
        """
}
