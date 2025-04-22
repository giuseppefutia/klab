import json

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_json_size(file_path):
    data = load_json_file(file_path)
    return len(data)
