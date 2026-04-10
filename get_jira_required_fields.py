import requests
from tmm.config.loader import ConfigLoader

loader = ConfigLoader("config")
jira_config = loader.jira()
auth = (jira_config['email'], jira_config['api_token'])
base_url = jira_config['base_url']
request_type_id = jira_config['request_type_id']
service_desk_id = jira_config['service_desk_id']

url = f"{base_url}/rest/servicedeskapi/servicedesk/{service_desk_id}/requesttype/{request_type_id}/field"
resp = requests.get(url, auth=auth)
resp.raise_for_status()
fields = resp.json().get('requestTypeFields', [])

print(f"Required fields for request type {request_type_id}:")
for field in fields:
    print(f"- {field['name']} (key: {field['fieldId']}) required: {field['required']}")
    if 'validValues' in field:
        print(f"  Valid values: {[v['label'] for v in field['validValues']]}")
