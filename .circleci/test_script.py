
import os
import sys
import logging

from dcmanagerclient.api import client
from cgtsclient.client import get_client

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

try:
    client_args = dict(
        auth_url=os.environ['OS_AUTH_URL'],
        username=os.environ['OS_USERNAME'],
        api_key=os.environ['OS_PASSWORD'],
        project_name=os.environ['OS_PROJECT_NAME'],
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
except KeyError:
    logging.error('Please source your RC file before execution, '
                  'e.g.: `source ~/downloads/admin-rc.sh`')
    sys.exit(1)

os_client_args = {}
for key, val in client_args.items():
    os_client_args['os_{key}'.format(key=key)] = val
os_client_args['os_password'] = os_client_args.pop('os_api_key')
os_client_args['os_region_name'] = 'RegionOne'
os_client_args['api_version'] = 1
config_client = get_client(**os_client_args)
dc_client = client.client(**dc_client_args)


class System(object):

    def __init__(self, api_response):
        self.api_response = api_response
        self.id = self.api_response.uuid
        self.name = self.api_response.name

        try:
            self.distributed_cloud_role = \
                self.api_response.distributed_cloud_role.lower()
        except AttributeError:
            self.distributed_cloud_role = \
                self.api_response.distributed_cloud_role

        self.system_type = self.api_response.system_type.lower()
        self.system_mode = self.api_response.system_mode.lower()

    @property
    def is_system_controller(self):
        return self.distributed_cloud_role == 'systemcontroller'

    @property
    def is_subcloud(self):
        return self.distributed_cloud_role == 'subcloud'

    @property
    def is_standalone_system(self):
        # It is not clear how this will appear in the API response.
        if self.distributed_cloud_role == 'null':
            return True
        elif self.api_response.distributed_cloud_role is None:
            return True
        return False

    @property
    def is_all_in_one(self):
        return self.system_type == 'all-in-one'

    @property
    def is_standard(self):
        # Not clear how this value will appear in API response.
        return self.system_type == 'standard'

    @property
    def is_duplex(self):
        return self.system_mode == 'duplex'

    @property
    def is_simplex(self):
        # Not clear how this value will appear in API response.
        return self.system_mode == 'simplex'

    @property
    def __str__(self):
        return self.api_response.__dict__


def get_systems():
    return [System(system) for system in config_client.isystem.list()]


def get_subclouds():
    subclouds = []
    for subcloud in dc_client.subcloud_manager.list_subclouds():
        subcloud_detail = \
            dc_client.subcloud_manager.subcloud_additional_details(
                subcloud.name)[0]
        subclouds.append(subcloud_detail)
    return subclouds


def get_hosts():
    return config_client.ihost.list()


def get_applications():
    return config_client.app.list()


def get_kube_clusters():
    return config_client.kube_cluster.list()


def get_service_parameter():
    return config_client.service_parameter.list()


def print_hosts_for_system(system_id):
    for host in get_hosts():
        if host.isystem_uuid == system_id:
            print_host(host)


def print_subclouds_for_system(system_name):
    logging.error(
        "We do not know how to identify the subclouds " 
        "for system {name}. What is the criteria, " 
        "when I look at the list of subclouds, " 
        "to deduce which are managed by this system controller?".format(
            name=system_name))
    # If I just list all subclouds, some of them will be for
    # certain System Controllers, and others will belong to others.
    # How do I identify a subcloud as being managed by a
    # specific system controller?
    # I thought I had a solution, but it does not work.


def print_subcloud_system_controller(system_name):
    logging.error(
        "We do not know how to identify the system controller " 
        "for subcloud {name}. What is the criteria, " 
        "when I look at the list of systems, "
        "to deduce which are managing this subcloud?".format(
            name=system_name))
    # How can I discover the System Controller that manages a specific
    # subcloud?


def print_kube_cluster():
    for kube_cluster in get_kube_clusters():
        print(kube_cluster.__dict__)


def print_service_parameter():
    for service_parameter in get_service_parameter():
        if service_parameter == 'openstack':
            print(service_parameter)


def print_applications():
    logging.info('Blah blah')
    for application in get_applications():
        print(application.__dict__)


def print_system(system):
    logging.info(system.__dict__)


def print_host(host):
    logging.info(host.to_dict())


def print_subcloud(subcloud):
    logging.info(subcloud.__dict__)


def show_system_info():

    logging.info("Showing info for systems in environment.")

    for system in get_systems():
        # I noticed that in the CLI `system show`, we can only show one system
        # controller.
        # In the Python client, there is no such limitation, but it makes me
        # suspect, that one may only ever see one System Controller a single
        # credential.

        if system.is_duplex:
            logging.info("The system is duplex with hosts:")
            print_hosts_for_system(system.id)

        elif system.is_simplex:
            logging.info("The system is simplex and will have one host.")
            print_hosts_for_system(system.id)

        else:
            logging.info("The system is {mode}.".format(
                mode=system.api_response.system_mode))

        if system.is_standalone_system:
            logging.info(
                "The system is a " 
                "Standalone system and will have no subclouds.")
            print(system)

        elif system.is_system_controller:
            logging.info(
                "The system is a " 
                "System Controller and has the following subclouds.")
            print_subclouds_for_system(system.name)

        elif system.is_subcloud:
            logging.info(
                "The system is a " 
                "Subcloud, it is managed by this System Controller:")
            print_subcloud_system_controller(system.name)
            # Let's say that we have subclouds,
            # which are also system controllers,
            # how can we find subclouds of subclouds?

    # print_kube_cluster()
    # print_applications()
    # print_service_parameter()


def show_diagnostics():

    logging.info("Diagnostics: ")

    logging.info("These are the systems available: ")
    for system in get_systems():
        print_system(system)

    logging.info("These are the hosts available: ")
    for host in get_hosts():
        print_host(host)

    logging.info("These are the subclouds available: ")
    for subcloud in get_subclouds():
        print_subcloud(subcloud)


if __name__ == '__main__':

    if 'help' in sys.argv:
        logging.info('Usage: python ./test_script.py.')
        logging.info('Please source your RC file before execution, '
                     'e.g.: `source ~/downloads/admin-rc.sh`')
        sys.exit(0)
    else:
        show_system_info()
        # show_diagnostics()
