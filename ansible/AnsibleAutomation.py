from __future__ import print_function
import boto3
import os
import re
import sys
import requests
import json
import yaml
 
envs_regex_pattern = r"(--envs=\[(\w|,)*\])"
teams_regex_pattern = r"(--teams=\[(\w|,)*\])"
dynamo_db_null_value = 'DYNAMO_DB_NULL_VALUE'
attributes = [
    "accountId", "team", "adminEmail", "teamEmail", "region", "environment",
    "VpcCidr", "PublicNetworks", "PrivateNetworks", "ProtectedNetworks", "AvailabilityZone1",
    "AvailabilityZone2", "AvailabilityZone3", "AvailabilityZone4", "CloudabilityExternalId"
]
 
environments = ['demo', 'dev', 'test', 'prod', 'sharedprod', 'provisioning', 'logging', 'custodian']
dynamo = boto3.resource('dynamodb')
table = dynamo.Table('AWSAccounts')
 
 
def get_value(line, item):
    key = None
    value = None
 
    if line.startswith(item + ': '):
        key = item
        value = line.split(item + ': ', 1)[1].replace('\n', '')
 
    return key, value
 
 
def process_file(file):
    with open(file) as open_file:
        current_item = {}
        line = open_file.readline()
        while line:
            for attribute in attributes:
                key, value = get_value(line, attribute)
                if key and value:
                    current_item[key] = value
            line = open_file.readline()
        return current_item
 
 
def get_account_by_filter(inventory, filter, value):
    return [account for account in inventory if account[filter] == value]
 
 
def get_accounts_for_environment(inventory, environment):
    special_accounts = ['awsdemo', 'logging', 'custodian']
    accounts = []
    if environment == 'demo':
        accounts = get_account_by_filter(inventory, 'team', 'awsdemo')
    elif environment == 'sharedprod':
        accounts = get_account_by_filter(inventory, 'accountId', '839975860898')
    elif environment == 'logging':
        accounts = get_account_by_filter(inventory, 'accountId', '396533554678')
    elif environment == 'custodian':
        accounts = get_account_by_filter(inventory, 'accountId', '575660321058')
    else:
        accounts = [account for account in inventory if (
                account['environment'] == environment and
                account['team'] not in special_accounts and
                account['adminEmail'] != 'bmahmud@yahoo.com'
        )]
 
    if len(sys.argv) == 1:
        return [(account['team'].strip() + account['environment'].strip())
                for account in accounts
                if 'creationDate' in account]
    else:
        return [(account['team'].strip() + account['environment'].strip())
                for account in accounts]
 
def create_inventory_file(inventory):
    print('Generating inventory file...')
 
    with open('inventory', 'w') as open_file:
        for environment in environments:
            open_file.write('[%s]\n' % environment)
            accounts_for_environment = get_accounts_for_environment(inventory, environment)
            [open_file.write('%s\n' % account) for account in accounts_for_environment]
            open_file.write('\n')
 
    print('Inventory file created!')
 
    return
 

def get_inventory_from_files():
    file_dir = '/Users/bmahmud/Documents/projects/awsaccountmgr/ansible/host_vars'
 
    inventory = []
    files = os.listdir(file_dir)
    if '.DS_Store' in files:
        files.remove('.DS_Store')
    for file in files:
        full_path = '%s/%s' % (file_dir, file)
        inventory.append(process_file(full_path))
 
    print(inventory)
 
    return inventory
 
 
def create_host_vars_files(inventory):
    print('Generating host_vars files...')
    for inventory_item in inventory:
        file_name = inventory_item['team'].strip()+inventory_item['environment'].strip()
 
        print('Creating host file for: %s' % file_name)
 
        complete_file_path = os.path.join('./host_vars', file_name)
        with open(complete_file_path, 'w') as open_file:
            open_file.write('---\n')
            for key, value in inventory_item.items():
                if key in ['VpcCidr', 'accountId']:
                    value = '"' + value + '"'
                elif key in ['PublicNetworks', 'PrivateNetworks', 'ProtectedNetworks']:
                    value = '"' + ','.join(value) + '"'
                elif key == 'regions':
                    value = '\n' + yaml.dump(value, default_flow_style=False).rstrip()
                elif value == dynamo_db_null_value:
                    value = ''
                open_file.write('%s: %s\n' % (key, value))
 
    print('Host Files Created: %s' % len(inventory))
 
    return
 
 
def insert_inventory_into_database(inventory):
    print('Inserting records into database...')
 
    for host in inventory:
        insert = {}
        for key, value in host.items():
            value = value.replace('"', '')
 
            if value is None:
                value = dynamo_db_null_value
 
            if key in ['PrivateNetworks', 'ProtectedNetworks', 'PublicNetworks']:
                value = value.split(',')
 
            insert[key] = value
        print(insert)
        table.put_item(Item=insert)
 
    print("Hosts Inserted Into Table!")
 
    return
 
 
def get_inventory_from_database():
    scan = table.scan()
    return scan['Items']
 
 
def apply_team_filter(inventory, teams):
    if not teams:
        return inventory
    else:
        #Always run for specified team(s) along with demo, sandbox, logging, custodian, and sharedservices
        teams = [account for account in inventory if (
                 account['team'] in teams or
                 account['team'] in ['awsdemo', 'awssandbox', 'logging', 'custodian'] or
                 account['adminEmail'] == 'bmahmud@yahoo.com')]
        print('Running for teams: %s' % teams)
 
        return teams
 
 
def apply_environment_filter(inventory, envs):
    if not envs:
        return inventory
    return [host for host in inventory if host["environment"] in envs]
 
 
# Use regular expression to test for valid title   
def get_envs_from_title(title):
    regex_response = re.search(envs_regex_pattern, title)
    if regex_response:
        return re.search(envs_regex_pattern, title).group(0)[8:-1].split(',')
    else:
        return []
 
 
# Use regular expression to test for valid title   
def get_teams_from_title(title):
    regex_response = re.search(teams_regex_pattern, title)
    if regex_response:
        return (re.search(teams_regex_pattern, title).group(0)[9:-1]).split(',')
    else:
        return []
 
 
def get_github_token():
    token_value = boto3.client('ssm').get_parameter(Name='GitHubToken', WithDecryption=True)['Parameter']['Value']
    bearer_token = "Bearer " + token_value
    return bearer_token
 
 
# Set up pull request api call for github api
def get_url():
    author = 'bmahmud'
    repo = 'awspipelinerepo'
   
    sha = os.environ['CODEBUILD_RESOLVED_SOURCE_VERSION']
 
    return https://api.github.com/repos/{}/{}/commits/{}.format(author, repo, sha)
   
 
# Send Status update through github status api
def make_commit_api_call():
    github_url = get_url()
    # Setting up OAUTH for requests call
    headers = {'Authorization': get_github_token()}
 
    r = requests.get(github_url, headers=headers)
    return r.content
 
 
# Get title of pull request from response
def get_pull_request_title_from_response(response):
    json_response = json.loads(response)
    pull_request_title_message = json_response['commit']['message']
    return pull_request_title_message
 
 
def populate_database():
    inventory = get_inventory_from_files()
    insert_inventory_into_database(inventory)
 
    return inventory
 
 
def get_inventory_after_applying_filters(title, inventory):
    teams_filter = get_teams_from_title(title)
    envs_filter = get_envs_from_title(title)
 
    inventory = apply_team_filter(inventory, teams_filter)
    inventory = apply_environment_filter(inventory, envs_filter)
 
    return inventory
 
 
def main():
    inventory = get_inventory_from_database()
 
    if len(sys.argv) == 1:
        github_response = make_commit_api_call()
        title = get_pull_request_title_from_response(github_response)
        inventory = get_inventory_after_applying_filters(title, inventory)
    else:
        title = '--teams=[%s]' % (sys.argv[1])
        inventory = get_inventory_after_applying_filters(title, inventory)
 
    create_inventory_file(inventory)
    create_host_vars_files(inventory)
 
    return
 
 
main()