def chi_employees_importer_factory(base_importer_cls, backend: str):
    import logging

    class ChicagoEmployeesImporter(base_importer_cls):
        def __init__(self):
            super().__init__()
            self.backend = backend

        @staticmethod
        def get_csv_size(employees_file, encoding="utf-8"):
            return sum(1 for _ in ChicagoEmployeesImporter.get_rows(employees_file))

        @staticmethod
        def get_rows(employees_file):
            import numpy as np
            import pandas as pd
            employees = pd.read_csv(employees_file, low_memory=False)
            employees['DATA_SOURCE'] = "EMPLOYEES"
            employees['RECORD_TYPE'] = "PERSON"
            if 'RECORD_ID' not in employees:
                employees.insert(0, 'RECORD_ID', range(4000000, 4000000 + len(employees)))

            def split_name(name):
                parts = name.split(',')
                last = parts[0].strip()
                rest = parts[1].strip().split(' ') if len(parts) > 1 else []
                first = rest[0] if len(rest) > 0 else None
                middle = rest[1] if len(rest) > 1 else None
                return pd.Series([first, middle, last])

            employees[['Owner First Name', 'Owner Middle Initial', 'Owner Last Name']] = employees['Name'].apply(split_name)
            employees.replace({np.nan: None}, inplace=True)
            for _, row in employees.iterrows():
                yield row.to_dict()

        def set_constraints(self):
            queries = [
                "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (node:Person) REQUIRE node.clusterId IS UNIQUE",
                "CREATE CONSTRAINT person_record_id IF NOT EXISTS FOR (node:PersonRecord) REQUIRE node.id IS UNIQUE",
                "CREATE CONSTRAINT department_id IF NOT EXISTS FOR (node:Department) REQUIRE node.id IS UNIQUE",
                "CREATE INDEX person_record_component_id IF NOT EXISTS FOR (node:PersonRecord) ON (node.componentId)",
                "CREATE INDEX person_record_employer_id IF NOT EXISTS FOR (node:PersonRecord) ON (node.employerId)",
                "CREATE FULLTEXT INDEX person_record_fullName IF NOT EXISTS FOR (node:PersonRecord) ON EACH [node.fullName]"
            ]
            for query in queries:
                with self._driver.session(database=self.database) as session:
                    session.run(query)

        def import_people_records(self, employees_file):
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
            SET n.title = item.`Job Titles`

            MERGE (d:Department {id: item.Department})
            SET d.source = item.DATA_SOURCE

            MERGE (n)-[r:WORKS_FOR_DEPARTMENT]->(d)
            SET r.employmentType = item.`Full or Part-Time`
            SET r.salaryType = item.`Salary or Hourly`
            SET r.typicalHours = item.`Typical Hours`
            SET r.annualSalary = item.`Annual Salary`
            SET r.hourlyRate = item.`Hourly Rate`
            """

            size = self.get_csv_size(employees_file)
            self.batch_store(import_people_records_query, self.get_rows(employees_file), size=size)

        def import_data(self, employees_file):
            logging.info("Loading constraints and indexes for person records and entities...")
            self.set_constraints()

            logging.info("Loading person record nodes...")
            self.import_people_records(employees_file)

    return ChicagoEmployeesImporter

if __name__ == '__main__':
    from util.cli_entry import run_backend_importer

    run_backend_importer(
        chi_employees_importer_factory,
        description="Run Chicago Employee Importer with selected backend.",
        file_help="Path to the Employees CSV file",
        default_base_path="./data/chicago/"
    )

