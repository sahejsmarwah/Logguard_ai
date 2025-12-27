import json

def get_deployments():
    with open("app/mock_data/deployments.json") as f:
        return json.load(f)
