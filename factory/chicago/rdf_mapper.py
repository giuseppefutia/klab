from mapper.convert import Neo4jToRDFConverter
from factory.chicago.mappings import (
    entity_mappings,
    data_property_mappings,
    computed_data_property_mappings,
    object_property_mappings,
    namespaces
)

def main():
    converter = Neo4jToRDFConverter(
        entity_mappings=entity_mappings,
        data_property_mappings=data_property_mappings,
        computed_data_property_mappings=computed_data_property_mappings,
        object_property_mappings=object_property_mappings,
        namespaces=namespaces,
    )

    converter.convert(
        output_file="data/chicago/chicago.ttl",
        serialization_format="turtle"
    )

if __name__ == "__main__":
    main()
