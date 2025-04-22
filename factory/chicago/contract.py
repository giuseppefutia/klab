
def chi_contracts_importer_factory(base_importer_cls, backend: str):
    import logging

    class ChicagoContractsImporter(base_importer_cls):
        def __init__(self):
            super().__init__()
            self.backend = backend

        @staticmethod
        def get_csv_size(contracts_file, encoding="utf-8"):
            return sum(1 for _ in ChicagoContractsImporter.get_rows(contracts_file))

        @staticmethod
        def get_rows(contracts_file):
            import pandas as pd
            import numpy as np
            contracts = pd.read_csv(contracts_file, low_memory=False)
            contracts['DATA_SOURCE'] = "CONTRACTS"
            contracts['RECORD_TYPE'] = "CONTRACT"
            if 'RECORD_ID' not in contracts:
                contracts.insert(0, 'RECORD_ID', range(0, len(contracts)))
            contracts.replace({np.nan: None}, inplace=True)
            for _, row in contracts.iterrows():
                yield row.to_dict()

        def set_constraints(self):
            queries = [
                "CREATE CONSTRAINT contract_record_id IF NOT EXISTS FOR (node:ContractRecord) REQUIRE node.id IS UNIQUE",
                "CREATE INDEX contract_record_contract_id IF NOT EXISTS FOR (node:ContractRecord) ON (node.contractId)",
                "CREATE CONSTRAINT contract_id IF NOT EXISTS FOR (node:Contract) REQUIRE node.id IS UNIQUE",
                "CREATE CONSTRAINT procurement_type_id IF NOT EXISTS FOR (node:ProcurementType) REQUIRE node.id IS UNIQUE",
                "CREATE CONSTRAINT department_id IF NOT EXISTS FOR (node:Department) REQUIRE node.id IS UNIQUE",
                "CREATE CONSTRAINT contract_type IF NOT EXISTS FOR (node:ContractType) REQUIRE node.id IS UNIQUE",
                "CREATE CONSTRAINT organization_id IF NOT EXISTS FOR (node:Organization) REQUIRE node.id IS UNIQUE",
                "CREATE CONSTRAINT address_id IF NOT EXISTS FOR (node:Address) REQUIRE node.id IS UNIQUE",
                "CREATE FULLTEXT INDEX organization_name IF NOT EXISTS FOR (node:Organization) ON EACH [node.name]"
            ]
            for query in queries:
                with self._driver.session(database=self.database) as session:
                    session.run(query)

        def import_contract_records(self, contracts_file):
            query = """
            UNWIND $batch as item
            MERGE (n:ContractRecord {id: item.RECORD_ID})
            SET n.name = item.`Purchase Order Description`,
                n.amount = item.`Award Amount`,
                n.startDate = item.`Start Date`,
                n.endDate = item.`End Date`,
                n.approvalDate = item.`Approval Date`,
                n.pdfFile = item.`Contract PDF`,
                n.vendorId = item.`Vendor ID`,
                n.contractId = item.`Purchase Order (Contract) Number`,
                n.specificationId = item.`Specification Number`,
                n.source = item.DATA_SOURCE
            """
            size = self.get_csv_size(contracts_file)
            self.batch_store(query, self.get_rows(contracts_file), size=size)

        def merge_vendors_and_orders(self, contracts_file):
            query = """
            UNWIND $batch AS item
            MERGE (n:ContractRecord {contractId: item.`Purchase Order (Contract) Number`})
            MERGE (m:Contract {id: item.`Purchase Order (Contract) Number`})
            SET m.names = apoc.coll.toSet(coalesce(m.names, []) + coalesce(item.`Purchase Order Description`, []))

            WITH item, n, m,
                CASE WHEN n.startDate IS NOT NULL AND n.startDate <> '' 
                    THEN date(datetime({epochMillis: apoc.date.parse(n.startDate, 'ms', 'MM/dd/yyyy')}))
                    ELSE NULL END AS safeStartDate,
                CASE WHEN n.endDate IS NOT NULL AND n.endDate <> '' 
                    THEN date(datetime({epochMillis: apoc.date.parse(n.endDate, 'ms', 'MM/dd/yyyy')}))
                    ELSE NULL END AS safeEndDate

            WITH item, n, m,
                [d IN [safeStartDate] WHERE d IS NOT NULL] AS startDates,
                [d IN [safeEndDate] WHERE d IS NOT NULL] AS endDates

            SET m.startDate = toString(coalesce(apoc.coll.min(startDates), m.startDate)),
                m.endDate = toString(coalesce(apoc.coll.max(endDates), m.endDate))

            MERGE (o:Organization {id: item.`Vendor ID`})
            SET o.names = apoc.coll.toSet(coalesce(o.names, []) + coalesce(item.`Vendor Name`, [])),
                o.source = item.DATA_SOURCE,
                o.addresses = apoc.coll.toSet(coalesce(o.addresses, []) + coalesce(item.`Address 1`, []) + coalesce(item.`Address 2`, [])),
                o.addressPostalCodes = apoc.coll.toSet(coalesce(o.addressPostalCodes, []) + coalesce(toString(item.Zip), [])),
                o.addressStates = apoc.coll.toSet(coalesce(o.addressStates, []) + coalesce(item.State, [])),
                o.addressCities = apoc.coll.toSet(coalesce(o.addressCities, []) + coalesce(item.City, []))
            
            WITH item, n, m, o
            SET o.name = trim(apoc.text.capitalize(reduce(shortest = head(o.names), name IN o.names | CASE WHEN size(name) < size(shortest) THEN name ELSE shortest END)))
            
            MERGE (a:Address {id: coalesce(item.`Address 1`, "Unknown")})
            SET a.addressPostalCode = toString(item.Zip),
                a.addressState = item.State,
                a.addressCity = item.City
            
            MERGE (t:ProcurementType {id: coalesce(item.`Procurement Type`, "Unknown")})
            MERGE (n)-[:INCLUDED_IN_CONTRACT]->(m)
            MERGE (n)-[:HAS_VENDOR]->(o)
            MERGE (n)-[:HAS_PROCUREMENT_TYPE]->(t)
            MERGE (o)-[r:HAS_ADDRESS]->(a)
            SET r.source = item.DATA_SOURCE
            """
            size = self.get_csv_size(contracts_file)
            self.batch_store(query, self.get_rows(contracts_file), size=size)

        def merge_departments_contract_types(self, contracts_file):
            query = """
            UNWIND $batch as item
            MERGE (n:Contract {id: item.`Purchase Order (Contract) Number`})
            SET n.name = apoc.text.join(n.names, " + ")
            MERGE (m:Department {id: coalesce(item.Department, "Unknown")})
            MERGE (o:ContractType {id: coalesce(item.`Contract Type`, "Unknown")})
            MERGE (m)-[:ASSIGNS_CONTRACT]->(n)
            MERGE (n)-[:HAS_CONTRACT_TYPE]->(o)
            """
            size = self.get_csv_size(contracts_file)
            self.batch_store(query, self.get_rows(contracts_file), size=size)
        
        def import_data(self, contracts_file):
            logging.info("Loading constraints and indexes...")
            self.set_constraints()
    
            logging.info("Loading contract records...")
            self.import_contract_records(contracts_file)
            
            logging.info("Merging vendors and orders...")
            self.merge_vendors_and_orders(contracts_file)

            logging.info("Merging departments and contract types...")
            self.merge_departments_contract_types(contracts_file)

    return ChicagoContractsImporter

if __name__ == '__main__':
    from util.cli_entry import run_backend_importer

    run_backend_importer(
        chi_contracts_importer_factory,
        description="Run Chicago Contracts Importer with selected backend.",
        file_help="Path to the Contracts CSV file",
        default_base_path="./data/chicago/"
    )