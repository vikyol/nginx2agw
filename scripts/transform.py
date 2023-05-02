import re
import json
import sys
from urllib.parse import urlparse

FILENAME = 'conf.d/mysite.conf'

class Logger(object):
    def __init__(self, filename="output.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass


# Generate rule sequence number, 10, 15, 20...
def generate_number():
    count = 10
    while True:
        yield count
        count += 5

def process_nginx_line(line):
    pattern = r'location\s+(?P<path>.+?)\s*\{\s*proxy_pass\s+(?P<url>https?://[^;/]+)(?P<proxy_path>/[^;]*)(?:;|\n\s*.+)*?\}'

    match = re.match(pattern, line)
    name = ''

    if match:
        path = match.group('path')
        proxy_path = match.group('proxy_path')
        proxy_url = match.group('url')

        parsed_uri = urlparse(proxy_url)
        # this will fail if there is no subdomain 
        hostname = parsed_uri.hostname.split('.')[0]
 
        print(f"Matched line: {line}")
        print(f"Extracted [path: {path}] [proxy_path: {proxy_path}] [proxy_url: {proxy_url}]")

        modified_path = proxy_path.strip('/')
        if len(modified_path) > 0:
            name = modified_path.strip('/').split('/')[-1]
        else:
            modified_path = '/'
            name = path.strip('/').split('/')[-1]

        name = name.replace("-", "").lower()
        print(f"Extracted [name: {name}] [modified_path: {modified_path}]")

        return {
            'name': name,
            'modified_path': modified_path,
            'path': path,
            'hostname': hostname
        }
    else:
        if line.strip().startswith("location"):
            print(f"No Math: {line}")

    return None

def get_rewrite_rule(rule_data, ruleSequence):
    return {
        "name": f"{rule_data['name']}{ruleSequence}",
        "properties": {
            "rewriteRules": [
                {
                    "actionSet": {
                        "urlConfiguration": {
                            "modifiedPath": f"/{rule_data['modified_path']}",
                            "reroute": True
                        }
                    },
                    "name": f"rwrule-{rule_data['name']}",
                    "ruleSequence": ruleSequence
                }
            ]
        }
    }


def get_path_rule(rule_data, ruleSequence):
    return {
        "name": f"{rule_data['name']}{ruleSequence}",
        "backendAddressPoolName": f"pool-{rule_data['hostname']}",
        "backendHttpSettingsName": f"settings-{rule_data['hostname']}",
        "paths": [
            f"{rule_data['path'].replace('*', '')}*"
        ],
        "rewriteRuleSetName": f"{rule_data['name']}{ruleSequence}",
    }


def generate_json_config(nginx_rules):
    rewrite_rules = []
    path_rules = []
    rule_sequence = generate_number() 

    if len(nginx_rules) == 0:
        return None

    for rule in nginx_rules: 
        rule_data = process_nginx_line(rule.strip())
        if rule_data:
            rule_id = next(rule_sequence)
            rewrite_rules.append(get_rewrite_rule(rule_data, rule_id))
            path_rules.append(get_path_rule(rule_data, rule_id))

    return {
        "rewriteRuleSets": {
            "value": rewrite_rules
        },
        "urlPathMaps": {
            "value": [
                {
                    "name": "{{ env.hostName }}",
                    "defaultBackendAddressPoolName": "pool-default-{{ env.fullWorkloadName }}",
                    "defaultBackendHttpSettingsName": "settings-default-{{ env.fullWorkloadName }}",
                    "pathRules": path_rules
                }
            ]
        }
    }


if __name__ == "__main__":
    sys.stdout = Logger("transform_debug.log")
    json_config = []

    # Read the NGINX configuration from a file line by line
    with open(FILENAME, 'r') as f:
        nginx_rules = f.readlines()
        json_rules = generate_json_config(nginx_rules)

    outFile = f"{FILENAME.split('/')[-1]}.json"
    with open(outFile, 'w') as f:
        json.dump(json_rules, f, indent=2)

    print(f"JSON configuration saved to {outFile}")
