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

### Extract RDF Data from the LPG Database

To convert a subset of the CKG into an RDF graph, run the following command:

```bash
python -m factory.chicago.rdf_mapper --backend neo4j
```

## Unlocking Graph Neural Networks: A Hands-on Journey from Basics to Breakthroughs

## Theory
* [Traditional Graph-based Features](https://colab.research.google.com/drive/1ycjxFUqmV9K1UO15969QZvU3IJo3IgCD?usp=sharing)
* [Graph Isomorphism](https://colab.research.google.com/drive/1gNjJUkZpmBh1Arlu-02PI0bkztLJ1s5H?usp=sharing)
* [Permutation Invariance and Equivariance](https://colab.research.google.com/drive/11gPY7z3tV2zIOQbRUmk-6kQAlmBqzE0N?usp=sharing)
* [Shift Equivariance](https://colab.research.google.com/drive/1HQmmhjwKzkf7GQ5Vq7Gb-TAnA6bDac3X?usp=sharing#scrollTo=_NzyDw2Tvwy0)

## Layers
* [Graph Convolutional Networks (GCNs)](https://colab.research.google.com/drive/1dac3u8PBk_oEXvGbQUJWQc8vGDyI6PEh?usp=sharing)
* [GraphSAGE](https://colab.research.google.com/drive/1BGgmyn8SnEBWUnfe9wxNhm06KjD87xNP?usp=sharing)
* [Graph Attention Networks (GATs)](https://colab.research.google.com/drive/12lRj9qnGneYrGaueOy3Wi5b3hsaXxLkx?usp=sharing#scrollTo=w0jBUU_QU4GS)

## Applications
* [Node Classification in Bitcoin Using PyG for Anti-Money Laundering](https://colab.research.google.com/drive/1D72FAxMUDy8VDJHgWGwwGX57J-iBaxvE?usp=sharing)
* [Link Prediction in MovieLens Using PyG for Recommendation Systems](https://colab.research.google.com/drive/1MsPfrN1yUeRWI3TSH3oiCAVBfcpJx4rF?usp=sharing) 
* [(Experimental) - G-Retriever using PyG for Chatting With Your Graph](https://colab.research.google.com/drive/1dJUYq5VbuskVnLeWrZXT4t-jz2vdr5Gl?usp=sharing)
