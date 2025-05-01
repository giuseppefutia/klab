SHACL_PROMPTS = {
    
    "rdf_schema": 
        """@prefix foaf: <http://xmlns.com/foaf/0.1/> .
           @prefix schema: <https://schema.org/> .
           @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

           # Assume: foaf:Person, foaf:name (xsd:string), schema:relatedTo
        """,

    
    "message":
        """
        Define a SHACL NodeShape named <#DisconnectedPeopleShape> for persons (foaf:Person) to ensure they are not connected to another person via schema:relatedTo.
        - Constraint: The maximum number of schema:relatedTo relationships must be 0.
        - Message: "A person must not be connected to another person via schema:relatedTo. It means a potential conflict of interest.
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
        - Use exactly the NodeShape URI <#DisconnectedPeopleShape>.
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

        - Important refinement: 
        The validation is about potential conflict of interest through the `schema:relatedTo` property connecting people with the same surname. 

        1. Run SHACL validation using the generated NodeShape. Summarize any SHACL validation issues found.

        2. For each validation issue:
            a. Explain why the issue occurred.
            b. Suggest a way to fix the issue.

        3. List all affected RDF nodes (subjects).

        4. For each affected node:
            a. Execute a Cypher query on the affected nodes to gather additional related details from the graph database, including the type of relationship if available.
            b. Use the gathered information to expand on why the issue was triggered, considering the nature of the relationship.
        
        5. Prioritize and highlight:
            - Details about all Person nodes (show their names) and the Department/Organization they work for.
        """
}