import requests
from tmm.config.loader import ConfigLoader

loader = ConfigLoader("config")
jira_config = loader.jira()

auth = (jira_config['email'], jira_config['api_token'])
base_url = jira_config['base_url']

print("=== Jira Service Desk IDs ===\n")
try:
    # Get service desks
    sds = requests.get(f'{base_url}/rest/servicedeskapi/servicedesk', auth=auth).json()['values']
    for sd in sds:
        print(f"Project {sd['projectKey']} (ID {sd['id']}):")
        
        # Get request types for this desk
        rts = requests.get(f"{base_url}/rest/servicedeskapi/servicedesk/{sd['id']}/requesttype", auth=auth).json()['values']
        for rt in rts:
            print(f"  {rt['name']}: {rt['id']}")
        
        if sd['projectKey'] == 'MD':
            print(f"\n✅ For MD project, use:")
            print(f"   service_desk_id: {sd['id']}")
            print(f"   request_type_id: {rts[0]['id'] if rts else '?'}")
except Exception as e:
    print(f"Error: {e}")
    