def manual_match_factory(base_importer_cls, backend: str):
    import logging

    class ManualDepartmentMatcher(base_importer_cls):
        def __init__(self):
            super().__init__()
            self.backend = backend

        def expand_department_pairs(self):
            raw_pairs = [
                ("DEPARTMENT OF BUILDINGS", "DEPARTMENT OF CONSTRUCTION AND PERMITS"),
                ("CHICAGO DEPARTMENT OF TRANSPORTATION", "DEPT OF FLEET MGMT|DEPT OF FLEET AND FACILITY MANAGEMENT"),
                ("DEPARTMENT OF FINANCE", "FINANCE GENERAL"),
                ("OFFICE OF THE MAYOR", "MAYORS OFFICE OF WORKFORCE DEVELOPMENT"),
                ("DEPARTMENT OF HOUSING", "DEPARTMENT OF ZONING"),
                ("DEPARTMENT OF LAW", "DEPT OF LAW"),
                ("OFFICE OF BUDGET & MANAGEMENT", "DEPARTMENT OF REVENUE"),
                ("DEPARTMENT OF CULTURAL AFFAIRS AND SPECIAL EVENTS", "DEPARTMENT OF SPECIAL EVENTS|OFFICE OF SPECIAL EVENTS|DEPARTMENT OF CULTURAL AFFAIRS"),
                ("OFFICE OF INSPECTOR GENERAL", "DEPT OF GENERAL SERVICES"),
                ("OFFICE OF PUBLIC SAFETY ADMINISTRATION", ""),
                ("DEPARTMENT OF HUMAN RESOURCES", "DEPARTMENT OF HUMAN SERVICES"),
                ("DEPARTMENT OF ENVIRONMENT", "DEPARTMENT OF ENVIROMENT"),
                ("CHICAGO POLICE DEPARTMENT", "POLICE BOARD"),
                ("CHICAGO DEPARTMENT OF PUBLIC HEALTH", "DEPARTMENT OF HEALTH"),
                ("CHICAGO DEPARTMENT OF AVIATION", "DEPT OF AVIATION"),
                ("CHICAGO FIRE DEPARTMENT", "FIRE DEPARTMENT"),
                ("DEPARTMENT OF STREETS AND SANITATION", "DEPT OF STREETS & SANITATION"),
                ("DEPARTMENT OF FAMILY AND SUPPORT SERVICES", "DEPT OF FAMILY AND SUPPORT SERVICES"),
                ("DEPARTMENT OF FLEET AND FACILITY MANAGEMENT", "DEPT OF FLEET MGMT|DEPT OF FLEET AND FACILITY MANAGEMENT"),
                ("OFFICE OF EMERGENCY MANAGEMENT AND COMMUNICATIONS", "OFFICE OF EMERGENCY COMMUNICATION"),
                ("CIVILIAN OFFICE OF POLICE ACCOUNTABILITY", "INDEPENDENT POLICE REVIEW AUTHORITY"),
                ("DEPARTMENT OF BUSINESS AFFAIRS AND CONSUMER PROTECTION", "DEPT OF BUSINESS AFFAIRS & CONSUMER PROTECTION"),
                ("BOARD OF ELECTION COMMISSIONERS", "BOARD OF ELECTION COMMISSIONER"),
                ("DEPARTMENT OF TECHNOLOGY AND INNOVATION", "DEPT OF INNOVATION & TECHNOLOGY"),
                ("DEPARTMENT OF PLANNING AND DEVELOPMENT", "PLANNING & DEVELOPMENT"),
                ("COMMUNITY COMMISSION FOR PUBLIC SAFETY AND ACCOUNTABILITY", "OFFICE FOR PEOPLE WITH DISABILITIES"),
                ("OFFICE OF CITY CLERK", "CITY CLERK"),
                ("CHICAGO ANIMAL CARE AND CONTROL", "COMM ON ANIMAL CARE & CONTROL"),
                ("DEPARTMENT OF PROCUREMENT SERVICES", "DEPT OF PROCUREMENT SERVICES"),
                ("MAYORS OFFICE FOR PEOPLE WITH DISABILITIES", "OFFICE OF CABLE COMMUNICATION ADM"),
                ("CHICAGO COMMISSION ON HUMAN RELATIONS", "COMMISSION ON HUMAN RELATIONS"),
                ("CITY TREASURER'S OFFICE", "CITY TREASURER"),
                ("DEPARTMENT OF ADMINISTRATIVE HEARING", "DEPARTMENT OF ADMINISTRATIVE HEARINGS"),
                ("CHICAGO POLICE BOARD", "POLICE BOARD"),
            ]
            for source, targets in raw_pairs:
                if not source or not targets:
                    continue
                for target in targets.split('|'):
                    yield{
                        "source": source.strip(),
                        "target": target.strip()
                    }


        def create_manual_similarity_relationships(self):
            query = """
            UNWIND $batch as item
            MATCH (a:Department) WHERE a.id = item.source
            MATCH (b:Department) WHERE b.id = item.target AND a <> b
            MERGE (a)-[r:IS_SIMILAR_TO {method: "MANUAL_MATCH"}]->(b)
            ON CREATE SET r.score = 1.0
            """
            self.batch_store(query, self.expand_department_pairs())

        def apply_updates(self):
            logging.info("Creating manual similarity relationships from hardcoded pairs...")
            self.create_manual_similarity_relationships()

    return ManualDepartmentMatcher

if __name__ == '__main__':
    from util.cli_entry import run_backend_importer

    run_backend_importer(
        manual_match_factory,
        description="Manually link department pairs with IS_SIMILAR_TO relationships.",
        file_help="No file needed.",
        default_base_path="./data/chicago/",
        require_file=False
    )