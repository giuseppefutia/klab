def chi_people_importer_factory(base_importer_cls, backend: str):
    import logging

    class ChicagoPeopleImporter(base_importer_cls):
        def __init__(self):
            super().__init__()
            self.backend = backend

        @staticmethod
        def get_csv_size(owners_file, encoding="utf-8"):
            return sum(1 for _ in ChicagoPeopleImporter.get_rows(owners_file))

        @staticmethod
        def get_rows(owners_file):
            import numpy as np
            import pandas as pd
            owners = pd.read_csv(owners_file, low_memory=False)
            owners['DATA_SOURCE'] = "OWNERS"
            owners['RECORD_TYPE'] = "PERSON"
            if 'RECORD_ID' not in owners:
                owners.insert(0, 'RECORD_ID', range(3000000, 3000000 + len(owners)))
            owners.replace({np.nan: None}, inplace=True)
            for _, row in owners.iterrows():
                yield row.to_dict()

        def set_constraints(self):
            queries = [
                "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (node:Person) REQUIRE node.clusterId IS UNIQUE",
                "CREATE CONSTRAINT person_record_id IF NOT EXISTS FOR (node:PersonRecord) REQUIRE node.id IS UNIQUE",
                "CREATE INDEX person_record_component_id IF NOT EXISTS FOR (node:PersonRecord) ON (node.componentId)",
                "CREATE INDEX person_record_employer_id IF NOT EXISTS FOR (node:PersonRecord) ON (node.employerId)",
                "CREATE FULLTEXT INDEX person_record_fullName IF NOT EXISTS FOR (node:PersonRecord) ON EACH [node.fullName]"
            ]
            for query in queries:
                with self._driver.session(database=self.database) as session:
                    session.run(query)

        def import_people_records(self, owners_file):
            import_people_records_query = """
            UNWIND $batch as item
            MERGE (n:PersonRecord {id: item.RECORD_ID})
            SET n.firstName = coalesce(item.`Owner First Name`, NULL)
            SET n.lastName = coalesce(item.`Owner Last Name`, NULL)
            SET n.middleName = coalesce(item.`Owner Middle Initial`, NULL)
            SET n.fullName = CASE
                WHEN trim(apoc.text.replace(
                    coalesce(item.`Owner First Name`, '') + ' ' +
                    coalesce(item.`Owner Middle Initial`, '') + ' ' +
                    coalesce(item.`Owner Last Name`, ''),
                    "\\s+", " ")) = '' THEN NULL
                ELSE apoc.text.capitalizeAll(toLower(trim(apoc.text.replace(
                    coalesce(item.`Owner First Name`, '') + ' ' +
                    coalesce(item.`Owner Middle Initial`, '') + ' ' +
                    coalesce(item.`Owner Last Name`, ''),
                    "\\s+", " "))))
            END
            SET n.source = item.DATA_SOURCE
            SET n.employerId = item.`Account Number`
            SET n.title = item.Title
            """
            size = self.get_csv_size(owners_file)
            self.batch_store(import_people_records_query, self.get_rows(owners_file), size=size)
        
        def import_data(self, owners_file):
            logging.info("Loading constraints and indexes for person records and entities...")
            self.set_constraints()

            logging.info("Loading person record nodes...")
            self.import_people_records(owners_file)

    return ChicagoPeopleImporter

if __name__ == '__main__':
    from util.cli_entry import run_backend_importer

    run_backend_importer(
        chi_people_importer_factory,
        description="Run Chicago People Importer with selected backend.",
        file_help="Path to the Business Owners CSV file",
        default_base_path="./data/chicago/"
    )
