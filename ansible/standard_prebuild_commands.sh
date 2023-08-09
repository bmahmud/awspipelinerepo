#!/bin/bash -xe
 
cd ansible && mkdir host_vars
python ./AnsibleAutomation.py
ls ./host_vars
cat inventory
 
# using pipenv to install some dependencies
cd ..
pipenv install --deploy
pipenv graph
pipenv run ansible-galaxy collection install -r ansible-requirements.yaml