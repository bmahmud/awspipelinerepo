import re
import os
import requests
import json
import boto3
 
# Use regular expression to test for valid title   
def get_tags_from_title(title):
    pattern = "(--tags=\[(\w|,)*\])"
    regex_response = re.search(pattern, title)
    if regex_response:
        return re.search(pattern, title).group(0)[8:-1]
    else:
        return 'all'
 
def get_github_token():
    github_token_value = boto3.client('ssm').get_parameter(Name='GitHubToken', WithDecryption=True)['Parameter']['Value']
    bearer_token = "Bearer " + github_token_value
    return bearer_token
 
# Set up pull request api call for github api
def get_url():
    author = 'magellan-health'
    repo = 'awsaccountmgr'
   
    sha = os.environ['CODEBUILD_RESOLVED_SOURCE_VERSION']
 
    return https://api.github.com/repos/{}/{}/commits/{}.format(author, repo, sha)
   
 
# Send Status update through github status api
def make_commit_api_call():
    github_url = get_url()
    # Setting up OAUTH for requests call
    headers = {'Authorization': get_github_token()}
 
    r = requests.get(github_url,headers=headers)
    return r.content
 
# Get title of pull request from response
def get_pull_request_title_from_response(response):
    json_response = json.loads(response)
    pull_request_title_message = json_response['commit']['message']
    return pull_request_title_message
 
def main():
    github_response = make_commit_api_call()
    title = get_pull_request_title_from_response(github_response)
    # title = "AWSCM-1256 something here"
 
    print(get_tags_from_title(title))
 
main()