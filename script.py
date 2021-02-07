# For the exercises here, set up the following environment.

import os
import json
from copy import deepcopy

from dcmanagerclient.api import client
from cgtsclient.client import get_client

# Collect client configurations:

client_args = dict(
    auth_url=os.environ['OS_AUTH_URL'],
    username=os.environ['OS_USERNAME'],
    api_key=os.environ['OS_PASSWORD'],
    project_name=os.environ['OS_PROJECT_NAME'],
    user_domain_name=os.environ['OS_USER_DOMAIN_NAME'],
    project_domain_name=os.environ['OS_PROJECT_NAME'],
    project_domain_id=os.environ['OS_PROJECT_DOMAIN_ID']
)

dc_client_args = dict(
    auth_url=os.environ['OS_AUTH_URL'],
    username=os.environ['OS_USERNAME'],
    api_key=os.environ['OS_PASSWORD'],
    project_name=os.environ['OS_PROJECT_NAME'],
    user_domain_name=os.environ['OS_USER_DOMAIN_NAME'],
    project_domain_name=os.environ['OS_PROJECT_NAME'],
    project_domain_id=os.environ['OS_PROJECT_DOMAIN_ID']
)

os_client_args = {}
for key, val in client_args.items():
    os_client_args['os_{key}'.format(key=key)] = val
os_client_args['os_password'] = os_client_args.pop('os_api_key')
os_client_args['api_version'] = 1

config_client = get_client(**os_client_args)
dc_client = client.client(**dc_client_args)

# Method for clean printing:


def print_object(obj):
    if hasattr(obj, 'to_dict'):
        print(json.dumps(obj.to_dict(), indent=4, sort_keys=True))
    elif hasattr(obj, '__dict__'):
        print(json.dumps(obj.__dict__, indent=4, sort_keys=True))
    else:
        print('Error: no way to dump obj...')
        print(json.dumps(obj, indent=4, sort_keys=True))

# I can list deployment configurations:
# These are either: "all-in-one simplex", "all-in-one duplex", etc.
# In our lab, we only have "all-in-one duplex".
# My assumption is that these are called


def print_isystems():
    print('Displaying System Info')
    for isystem in config_client.isystem.list():
        print_object(isystem)
        for ihost in config_client.ihost.list():
            if ihost.isystem_uuid != isystem.uuid:
                continue
            print_object(ihost)
        internal_dc_client_args = deepcopy(dc_client_args)
        internal_dc_client_args['region_name'] = isystem.region_name
        internal_dc_client = client.client(**internal_dc_client_args)
        for subcloud in internal_dc_client.subcloud_manager.list_subclouds():
            print_object(subcloud)
