import json

def get_logs():
    with open("app/mock_data/logs.json") as f:
        return json.load(f)
