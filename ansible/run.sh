#!/bin/bash -xe
 
export TAG_STRATEGY=`python ansible_github_title_tag_extractor.py`
 
[ -n "${EXTERNAL_ID}" ]
 
ansible-playbook -l $1 -t "${TAG_STRATEGY}" playbook.yml