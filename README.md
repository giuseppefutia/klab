# KLAB

The Knowledge Laboratory (KLAB) - A hub for learning, conducting research, and building community on knowledge technologies.

## Building a Hybrid Knowledge Graph System

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

To create the CKG, you can run the following scripts:

```bash
python -m factory.chicago.owner --backend neo4j --file Business_Owners_20240103.csv # Ingest owner data
python -m factory.chicago.owner_cluster --backend neo4j # Cluster similar owners
python -m factory.chicago.contract --backend neo4j --file Contracts_20240103.csv # Ingest contract data
python -m factory.chicago.license --backend neo4j --file Business_Licenses_20240103.csv # Ingest license data
python -m factory.chicago.org_cluster --backend neo4j # Cluster similar organizations
```

If you want to delete the CKG and starts everything from scratch, you could run the following command:

```bash
python -m factory.chicago.delete --backend neo4j
```