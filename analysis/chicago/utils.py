import json
from collections import defaultdict

from pyshacl import validate
from rdflib import Graph, RDF, SH

def parse_textual_graph(file_path: str, format: str = 'ttl') -> Graph:
    g = Graph()
    g.parse(file_path, format)
    print(f'Data Graph has {len(g)} statements.')
    return g

def parse_graph(data: str, format: str = 'ttl') -> Graph:
    g = Graph()
    g.parse(data=data, format=format)
    print(f'SHACL Graph has {len(g)} statements.')
    return g

def parse_shacl_result(report: Graph):
    grouped_violations = defaultdict(list)

    for result in report.subjects(RDF.type, SH.ValidationResult):
        focus_node = str(report.value(result, SH.focusNode))
        path = str(report.value(result, SH.resultPath)) if report.value(result, SH.resultPath) else None
        message = str(report.value(result, SH.resultMessage))
        severity = str(report.value(result, SH.resultSeverity)).split("#")[-1]
        source_shape = str(report.value(result, SH.sourceShape)) if report.value(result, SH.sourceShape) else None

        # Create a group key excluding the focus_node
        key = json.dumps({
            "path": path,
            "message": message,
            "severity": severity,
            "source_shape": source_shape
        }, sort_keys=True)

        grouped_violations[key].append(focus_node)

    # Format the grouped output
    compressed_output = []
    for key_str, focus_nodes in grouped_violations.items():
        common = json.loads(key_str)
        compressed_output.append({
            "common": common,
            "focus_nodes": focus_nodes
        })

    return compressed_output

def run_validation(data_graph: Graph, shacl_graph: Graph, inference: str = "rdfs"):
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shacl_graph,
        inference=inference,
        debug=False
    )
    return conforms, results_graph, results_text

def run_validation_pipeline(file_path: str, shacl: str, rdf_format: str = 'ttl'):
    data_graph = parse_textual_graph(file_path)
    shacl_graph = parse_graph(shacl, rdf_format)
    return run_validation(data_graph, shacl_graph)

def process_agent_step(step):
    if "agent" in step:
        print("\n=== Agent Step ===")
        messages = step["agent"].get("messages", [])
        for msg in messages:
            tool_calls = msg.additional_kwargs.get("tool_calls", [])
            for call in tool_calls:
                name = call["function"]["name"]
                args = json.loads(call["function"]["arguments"])
                print(f"\n🔧 Tool Call: {name}")
                print("🧾 Arguments:")
                for k, v in args.items():
                    print(f"  - {k}: {v[:100]}{'...' if len(v) > 100 else ''}")

    elif "tools" in step:
        print("\n=== Tool Results ===")
        for msg in step["tools"].get("messages", []):
            print(f"\n🛠️ Tool Name: {msg.name}")
            print(f"🆔 Tool Call ID: {msg.tool_call_id}")
            print("📄 Content:")
            print(msg.content)

    else:
        print("\n[⚠️ Unrecognized step structure]")
        print(step)
