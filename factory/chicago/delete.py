def chi_delete_node_factory(base_importer_cls, backend: str):
    import logging

    class ChicagoNodeDeleter(base_importer_cls):
        def __init__(self):
            super().__init__()
            self.backend = backend
            self.batch_size = 500

        def delete_nodes_by_label(self, labels):
            for label in labels:
                logging.info(f"Deleting {str(label)}")
                query = f"""
                CALL apoc.periodic.iterate(
                    'MATCH (n:{label}) RETURN n',
                    'DETACH DELETE n',
                    {{batchSize: 1000, parallel: false}}
                ) YIELD batches, total
                RETURN batches, total
                """
                with self._driver.session() as session:
                    session.run(query)

        def apply_updates(self):
            logging.info("Start deleting nodes and relations...")
            self.delete_nodes_by_label(["Person",
                                        "PersonRecord",
                                        "Organization",
                                        "LicenseRecord",
                                        "LicenseType",
                                        "OrganizationGroup",
                                        "Contract",
                                        "ContractRecord",
                                        "ContractType",
                                        "Department",
                                        "Procurement type",
                                        "Address"])

    return ChicagoNodeDeleter

if __name__ == '__main__':
    from util.cli_entry import run_backend_importer

    run_backend_importer(
        chi_delete_node_factory,
        description="Remove Chicago nodes from the selected backend.",
        file_help="No file needed.",
        default_base_path="./data/chicago/",
        require_file=False
    )