
# KLAB: The Knowledge Laboratory

**The Knowledge Laboratory (KLAB)** is a hub for learning, conducting research, and building community around cutting-edge knowledge technologies.

1. [Building a Hybrid Knowledge Graph System](#-building-a-hybrid-knowledge-graph-system)  
   - [Create and Activate Your Virtual Environment](#-step-1-create-and-activate-your-virtual-environment)  
   - [Install Required Dependencies](#-step-2-install-required-dependencies)  
   - [Download the Data](#-step-3-download-the-data)  
   - [Build the Chicago Knowledge Graph (CKG)](#-step-4-build-the-chicago-knowledge-graph-ckg)  
   - [Extract RDF from the LPG Database](#-step-5-extract-rdf-from-the-lpg-database)  
   - [Use Case Analysis](#-step-6-use-case-analysis)

2. [Unlocking Graph Neural Networks](#-unlocking-graph-neural-networks)  
   - [Theory](#-theory)  
   - [Layers](#-layers)  
   - [Applications](#-applications)

---

## 🚀 Building a Hybrid Knowledge Graph System

*Integrating LPG, RDF, and LLMs for Advanced Analytics*

* Knowledge Graph Conference 2025 - [SLIDES](https://docs.google.com/presentation/d/1thQqO6_IPzIa6ZPc_SkRHjbHcpRGHx0J/edit?usp=sharing&ouid=112517546961694752607&rtpof=true&sd=true)

### 🧪 Step 1: Create and Activate Your Virtual Environment

```bash
virtualenv -p python3 venv
source venv/bin/activate
```

### 📦 Step 2: Install Required Dependencies

```bash
pip install -r requirements.lock
```

### 📁 Step 3: Download the Data

Download the dataset from [this Google Drive folder](https://drive.google.com/drive/folders/1ixLVq2xwdFMGfUBt8u2aVp5nZQnjseOW?usp=sharing) and place the files in:

```
data/chicago/
```

Alternatively, download `neo4.dump` from the same folder to load into your Neo4j database (version `5.26.4` enterprise edition recommended).

### 🧱 Step 4: Build the Chicago Knowledge Graph (CKG)

To build the KG, you have to update the `config.ini` file in the root folder (neo4j access).

Run the full setup script:

```bash
./run_chicago_factory.sh
```

<details>
  <summary>Or manually execute each step:</summary>

```bash
python -m factory.chicago.owner --backend neo4j --file Business_Owners_20240103.csv
python -m factory.chicago.employee --backend neo4j --file Employees_20250422.csv
python -m factory.chicago.people_cluster --backend neo4j
python -m factory.chicago.contract --backend neo4j --file Contracts_20240103.csv
python -m factory.chicago.license --backend neo4j --file Business_Licenses_20240103.csv
python -m factory.chicago.org_cluster --backend neo4j
python -m factory.chicago.dept_similarity --backend neo4j
```

</details>

To delete and reset the graph:

```bash
python -m factory.chicago.delete --backend neo4j
```

### 🔁 Step 5: Extract RDF from the LPG Database

The RDF generation is currently performed **manually**. Look at the `mapping.py` files in the `regulatory_compliance/`, `conflict_of_interest/`, `three_sixty_degree_view` folders within the `analysis` and adjust the queries accordingly based on your Neo4j node ids.

```bash
python -m analysis.chicago.regulatory_compliance.rdf_mapper --backend neo4j
python -m analysis.chicago.conflict_of_interest.mapper --backend neo4j
python -m analysis.chicago.three_sixty_degree_view.mapper --backend neo4j
```

### 🔍 Step 6: Use Case Analysis

To build the KG, you have to update the `config.ini` file in the root folder (openai api-key).

- 📘 [Regulatory Compliance](analysis/chicago/01_regulatory_compliance.ipynb)
- 🧭 [Conflict of Interest](analysis/chicago/02_conflict_of_interest.ipynb)
- 🕸️ [360-Degree View](analysis/chicago/03_three_sixty_degree_view.ipynb)

Run the following queries to check the results of your agent.

<details>
  <summary>Regulatory Compliance Test Query</summary>
```cypher
MATCH path=(c:Contract)<-[:INCLUDED_IN_CONTRACT]-(contractRecord:ContractRecord)-[:HAS_VENDOR]->(contractOrg:Organization)-[:BELONGS_TO_ORG_GROUP]->(o:OrganizationGroup)<-[:BELONGS_TO_ORG_GROUP]-(licenseOrg:Organization)-[:ORG_HAS_LICENSE]->(license:LicenseRecord)
WHERE licenseOrg.name = "Stage Left, Inc."
RETURN path
```
</details>

<details>
  <summary>Conflict of Interest Test Query - Example 1</summary>

```cypher
 MATCH 
   path=(p2:Person)<-[:RECORD_RESOLVED_TO]-(:PersonRecord)
   -[:WORKS_FOR_DEPARTMENT]->(dept1:Department)
   -[:IS_SIMILAR_TO]->(dept2:Department)
   -[:ASSIGNS_CONTRACT]->(:Contract)<-[:INCLUDED_IN_CONTRACT]-(c:ContractRecord)
   -[:HAS_VENDOR]->(vendor1:Organization)
   -[:BELONGS_TO_ORG_GROUP]->(orgGroup:OrganizationGroup)<-[:BELONGS_TO_ORG_GROUP]-
   (vendor2:Organization)<-[:WORKS_FOR_ORG]-(p1:Person)
WHERE 
   (
      elementId(p2) = "4:5bc9e9e3-9f8e-4060-84df-00fa505e2753:527380"OR 
      elementId(p1) = "4:5bc9e9e3-9f8e-4060-84df-00fa505e2753:520260"
   )
   AND vendor1 <> vendor2
   AND p1 <> p2
   AND toLower(p1.name) <> toLower(p2.name)
   AND split(toLower(p1.name), " ")[-1] = split(toLower(p2.name), " ")[-1]
RETURN path
LIMIT 5
```
</details>

<details>
  <summary>Conflict of Interest Test Query - Example 2</summary>
```cypher
 MATCH 
   path=(p2:Person)<-[:RECORD_RESOLVED_TO]-(:PersonRecord)
   -[:WORKS_FOR_DEPARTMENT]->(dept1:Department)
   -[:IS_SIMILAR_TO]->(dept2:Department)
   -[:ASSIGNS_CONTRACT]->(:Contract)<-[:INCLUDED_IN_CONTRACT]-(c:ContractRecord)
   -[:HAS_VENDOR]->(vendor1:Organization)
   -[:BELONGS_TO_ORG_GROUP]->(orgGroup:OrganizationGroup)<-[:BELONGS_TO_ORG_GROUP]-
   (vendor2:Organization)<-[:WORKS_FOR_ORG]-(p1:Person)
WHERE 
   (
      elementId(p2) = "4:5bc9e9e3-9f8e-4060-84df-00fa505e2753:527206"OR 
      elementId(p1) = "4:5bc9e9e3-9f8e-4060-84df-00fa505e2753:486091"
   )
   AND vendor1 <> vendor2
   AND p1 <> p2
   AND toLower(p1.name) <> toLower(p2.name)
   AND split(toLower(p1.name), " ")[-1] = split(toLower(p2.name), " ")[-1]
RETURN path
LIMIT 5
```
<details>
  <summary>360-Degree View Test Query</summary>

```cypher
MATCH path=(pr:PersonRecord)-[:RECORD_RESOLVED_TO]->(p:Person)
                -[:WORKS_FOR_ORG]->(:Organization)
                -[:BELONGS_TO_ORG_GROUP]->(:OrganizationGroup)<-[:BELONGS_TO_ORG_GROUP]-
                (o:Organization)<-[:HAS_VENDOR]-(c:ContractRecord)-[:INCLUDED_IN_CONTRACT]->(x:Contract)
WHERE p.name = "Sister Marie Valerie Chaillou"
AND c.amount <> 0

RETURN path
LIMIT 10
```
</details>

---

## 🤖  Unlocking Graph Neural Networks

*A Hands-on Journey from Basics to Breakthroughs*

* Knowledge Graph Conference 2025 - [SLIDES](https://docs.google.com/presentation/d/12eKedtbKRJGI9hOUJ_AEE5BN00J30MN6/edit?usp=sharing&ouid=112517546961694752607&rtpof=true&sd=true)

### 📚 Theory

- 🧩 [Traditional Graph-based Features](https://colab.research.google.com/drive/1ycjxFUqmV9K1UO15969QZvU3IJo3IgCD?usp=sharing)
- 🔄 [Graph Isomorphism](https://colab.research.google.com/drive/1gNjJUkZpmBh1Arlu-02PI0bkztLJ1s5H?usp=sharing)
- 🔁 [Permutation Invariance & Equivariance](https://colab.research.google.com/drive/11gPY7z3tV2zIOQbRUmk-6kQAlmBqzE0N?usp=sharing)
- 🔃 [Shift Equivariance](https://colab.research.google.com/drive/1HQmmhjwKzkf7GQ5Vq7Gb-TAnA6bDac3X?usp=sharing#scrollTo=_NzyDw2Tvwy0)

### 🧱 Layers

- 📡 [Graph Convolutional Networks (GCNs)](https://colab.research.google.com/drive/1dac3u8PBk_oEXvGbQUJWQc8vGDyI6PEh?usp=sharing)
- 🌱 [GraphSAGE](https://colab.research.google.com/drive/1BGgmyn8SnEBWUnfe9wxNhm06KjD87xNP?usp=sharing)
- 🧿 [Graph Attention Networks (GATs)](https://colab.research.google.com/drive/12lRj9qnGneYrGaueOy3Wi5b3hsaXxLkx?usp=sharing#scrollTo=w0jBUU_QU4GS)

### 🎯 Applications

- 💰 [Node Classification in Bitcoin (AML)](https://colab.research.google.com/drive/1D72FAxMUDy8VDJHgWGwwGX57J-iBaxvE?usp=sharing)
- 🎬 [Link Prediction in MovieLens](https://colab.research.google.com/drive/1MsPfrN1yUeRWI3TSH3oiCAVBfcpJx4rF?usp=sharing)
- 🧪 [(Experimental) G-Retriever Chat with Graphs](https://colab.research.google.com/drive/1dJUYq5VbuskVnLeWrZXT4t-jz2vdr5Gl?usp=sharing)
