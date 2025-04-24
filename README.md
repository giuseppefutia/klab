# KLAB

The Knowledge Laboratory (KLAB) - A hub for learning, conducting research, and building community on knowledge technologies.

## Building a Hybrid Knowledge Graph System

Integrating LPG, RDF, and LLMs for Advanced Analytics.

### Create and Activate your Virtual Environment

```bash
virtualenv -p python3 venv
source venv/bin/activate
```

### Install the Requirements

```bash
pip install -r requirements.lock
```

### Create the Chicago Knowledge Graph (CKG)

To create the CKG, you can run the following command:

```bash
./run_chicago_factory.sh
```

Or you can run the following scripts, one by one:

```bash
python -m factory.chicago.owner --backend neo4j --file Business_Owners_20240103.csv # Ingest owner data
python -m factory.chicago.employee --backend neo4j --file Employees_20250422.csv # Ingest employee data
python -m factory.chicago.people_cluster --backend neo4j # Cluster similar people
python -m factory.chicago.contract --backend neo4j --file Contracts_20240103.csv # Ingest contract data
python -m factory.chicago.license --backend neo4j --file Business_Licenses_20240103.csv # Ingest license data
python -m factory.chicago.org_cluster --backend neo4j # Cluster similar organizations
python -m factory.chicago.dept_similarity --backend neo4j # Create similarity between departments
```

If you want to delete the CKG and starts everything from scratch, you could run the following command:

```bash
python -m factory.chicago.delete --backend neo4j
```

### Extract RDF data from the LPG Database

To convert a subset of the CKG into an RDF graph, run the following command:

```bash
python -m factory.chicago.rdf_mapper --backend neo4j
```