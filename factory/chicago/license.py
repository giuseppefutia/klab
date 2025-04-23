def chi_licenses_importer_factory(base_importer_cls, backend: str):
    import logging

    class ChicagoLicensesImporter(base_importer_cls):
        def __init__(self):
            super().__init__()
            self.backend = backend

        @staticmethod
        def get_csv_size(licenses_file, encoding="utf-8"):
            return sum(1 for _ in ChicagoLicensesImporter.get_rows(licenses_file))

        @staticmethod
        def get_rows(licenses_file):
            import pandas as pd
            import numpy as np
            licenses = pd.read_csv(licenses_file, low_memory=False)
            licenses['DATA_SOURCE'] = "LICENSES"
            licenses['RECORD_TYPE'] = "LICENSE"
            if 'RECORD_ID' not in licenses:
                licenses.insert(0, 'RECORD_ID', range(1000000, 1000000 + len(licenses)))
            licenses.replace({np.nan: None}, inplace=True)
            for _, row in licenses.iterrows():
                yield row.to_dict()

        def set_constraints(self):
            queries = [
                "CREATE CONSTRAINT license_record_id IF NOT EXISTS FOR (node:LicenseRecord) REQUIRE node.id IS UNIQUE",
                "CREATE CONSTRAINT license_type_id IF NOT EXISTS FOR (node:LicenseType) REQUIRE node.id IS UNIQUE",
                "CREATE CONSTRAINT organization_id IF NOT EXISTS FOR (node:Organization) REQUIRE node.id IS UNIQUE",
                "CREATE CONSTRAINT address_id IF NOT EXISTS FOR (node:Address) REQUIRE node.id IS UNIQUE",
                "CREATE FULLTEXT INDEX organization_name IF NOT EXISTS FOR (node:Organization) ON EACH [node.name]",
                "CREATE INDEX organization_component_id IF NOT EXISTS FOR (node:Organization) ON (node.componentId)",
                "CREATE INDEX organization_group_cluster_id IF NOT EXISTS FOR (node:OrganizationGroup) ON (node.clusterId)"
            ]
            for query in queries:
                with self._driver.session(database=self.database) as session:
                    session.run(query)

        def import_license_records(self, licenses_file):
            query = """
            UNWIND $batch as item
            MERGE (n:LicenseRecord {id: item.RECORD_ID})
            SET n.license_id = item.`LICENSE ID`,
                n.name = coalesce(item.`LEGAL NAME`, item.`DOING BUSINESS AS NAME`),
                n.businessName = coalesce(item.`DOING BUSINESS AS NAME`, '-'),
                n.businessId = item.`ACCOUNT NUMBER`,
                n.address = item.ADDRESS,
                n.addressPostalCode = item.`ZIP CODE`,
                n.addressState = item.STATE,
                n.addressCity = item.CITY,
                n.source = item.DATA_SOURCE,
                n.amount = item.`Award Amount`,
                n.date = item.`Approval Date`,
                n.startDate = item.`LICENSE TERM START DATE`,
                n.endDate = item.`LICENSE TERM EXPIRATION DATE`,
                n.status = item.`LICENSE STATUS`,
                n.code = item.`LICENSE CODE`,
                n.number = item.`LICENSE NUMBER`,
                n.siteNumber = item.`SITE NUMBER`,
                n.latitude = item.LATITUDE,
                n.longitude = item.LONGITUDE
            """
            size = self.get_csv_size(licenses_file)
            self.batch_store(query, self.get_rows(licenses_file), size=size)

        def import_license_type(self, licenses_file):
            query = """
            UNWIND $batch as item
            MERGE (n:LicenseType {id: item.`LICENSE CODE`})
            SET n.description = item.`LICENSE DESCRIPTION`
            """
            size = self.get_csv_size(licenses_file)
            self.batch_store(query, self.get_rows(licenses_file), size=size)

        def connect_license_to_type(self, licenses_file):
            query = """
            UNWIND $batch as item
            MERGE (n:LicenseType {id: item.`LICENSE CODE`})
            MERGE (m:LicenseRecord {id: item.RECORD_ID})
            MERGE (m)-[:HAS_LICENSE_TYPE]->(n)
            """
            size = self.get_csv_size(licenses_file)
            self.batch_store(query, self.get_rows(licenses_file), size=size)

        def import_organization(self, licenses_file):
            query = """
            UNWIND $batch as item
            MERGE (o:Organization {id: item.`ACCOUNT NUMBER`})
            SET o.names = apoc.coll.toSet(coalesce(o.names, []) + coalesce(item.`LEGAL NAME`, item.`DOING BUSINESS AS NAME`, [])),
                o.otherNames = apoc.coll.toSet(coalesce(o.otherNames, []) + coalesce(item.`DOING BUSINESS AS NAME`, [])),
                o.source = item.DATA_SOURCE,
                o.addresses = apoc.coll.toSet(coalesce(o.addresses, []) + coalesce(item.ADDRESS, [])),
                o.addressPostalCodes = apoc.coll.toSet(coalesce(o.addressPostalCodes, []) + coalesce(toString(item.`ZIP CODE`), [])),
                o.addressStates = apoc.coll.toSet(coalesce(o.addressStates, []) + coalesce(item.STATE, [])),
                o.addressCities = apoc.coll.toSet(coalesce(o.addressCities, []) + coalesce(item.CITY, []))
            MERGE (a:Address {id: item.ADDRESS})
            SET a.addressPostalCode = toString(item.`ZIP CODE`),
                a.addressState = item.STATE,
                a.addressCity = item.CITY,
                a.latitude = item.LATITUDE,
                a.longitude = item.LONGITUDE
            MERGE (o)-[r:HAS_ADDRESS]->(a)
            SET r.source = item.DATA_SOURCE
            """
            size = self.get_csv_size(licenses_file)
            self.batch_store(query, self.get_rows(licenses_file), size=size)

        def connect_org_to_license(self, licenses_file):
            query = """
            UNWIND $batch as item
            MERGE (n:Organization {id: item.`ACCOUNT NUMBER`})
            SET n.name = trim(apoc.text.capitalize(reduce(shortest = head(n.names), name IN n.names | CASE WHEN size(name) < size(shortest) THEN name ELSE shortest END)))
            MERGE (m:LicenseRecord {id: item.RECORD_ID})
            MERGE (n)-[:ORG_HAS_LICENSE]->(m)
            """
            size = self.get_csv_size(licenses_file)
            self.batch_store(query, self.get_rows(licenses_file), size=size)

        def connect_people_to_org(self, licenses_file):
            query = """
            UNWIND $batch as item
            MERGE (n:Organization {id: item.`ACCOUNT NUMBER`})
            WITH n, item
            MATCH (m:PersonRecord {employerId: item.`ACCOUNT NUMBER`})-[:RECORD_RESOLVED_TO]->(p:Person)
            MERGE (p)-[r:WORKS_FOR_ORG]->(n)
            SET r.roles = p.titles
            """
            size = self.get_csv_size(licenses_file)
            self.batch_store(query, self.get_rows(licenses_file), size=size)
        
        def import_data(self, license_file):
            logging.info("Loading constraints...")
            self.set_constraints()

            logging.info("Loading license records...")
            self.import_license_records(license_file)
    
            logging.info("Merging license types...")
            self.import_license_type(license_file)
    
            logging.info("Connecting licenses to types...")
            self.connect_license_to_type(license_file)
    
            logging.info("Importing organizations...")
            self.import_organization(license_file)
    
            logging.info("Connecting organizations to licenses...")
            self.connect_org_to_license(license_file)

            logging.info("Connecting people to organizations...")
            self.connect_people_to_org(license_file)

    return ChicagoLicensesImporter

if __name__ == '__main__':
    from util.cli_entry import run_backend_importer

    run_backend_importer(
        chi_licenses_importer_factory,
        description="Run Chicago Licenses Importer with selected backend.",
        file_help="Path to the Business Licenses CSV file",
        default_base_path="./data/chicago/"
    )