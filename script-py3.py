
import os
import json
from dcmanagerclient.api import client
from cgtsclient.client import get_client
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
os_client_args['os_region_name'] = 'RegionOne'
os_client_args['api_version'] = 1
config_client = get_client(**os_client_args)
dc_client = client.client(**dc_client_args)

def print_object(obj):
    if hasattr(obj, 'to_dict'):
        print(json.dumps(obj.to_dict(), indent=4, sort_keys=True))
    elif hasattr(obj, '__dict__'):
        print(json.dumps(obj.__dict__, indent=4, sort_keys=True))
    else:
        print('Error: no way to dump obj...')
        print(json.dumps(obj, indent=4, sort_keys=True))

def print_something(something):
    c = getattr(config_client, something)
    for x in c.list():
        print_object(x)

def print_systems():
    print('Displaying Systems')
    for system in config_client.isystem.list():
        print_object(system)

def print_hosts():
    print('Displaying Hosts\n')
    for host in config_client.ihost.list():
        print_object(host)

def print_apps():
    for app in config_client.app.list():
        print(json.dumps(app, indent=4, sort_keys=True))

def print_subclouds():
    print('Displaying Subclouds')
    for subcloud in dc_client.subcloud_manager.list_subclouds():
        subcloud_dict = subcloud.__dict__
        sc = dc_client.subcloud_manager.subcloud_additional_details(subcloud.name)
        delattr(sc[0], 'manager')
        print(json.dumps(sc[0].__dict__, indent=4, sort_keys=True))

def print_subcloud_groups():
    for group in dc_client.subcloud_group_manager.list_subcloud_groups():
        print(json.dumps(group, indent=4, sort_keys=True))


  # System Type All-in-one/Simplex, All-in-one/Duplex, standard - physical topology
  # System Mode Simplex Duplex - relationship between the two controller hosts
  # Distributed Cloud Role - Null - standalond - no discover , or non-null get a subcloud list

