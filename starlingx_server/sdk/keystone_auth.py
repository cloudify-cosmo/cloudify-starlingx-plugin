import json

import requests
from keystoneauth1.identity import v3
from keystoneauth1 import session

DC_MANAGER_API_URL = 'dcmanager_url'
PATCHING_API_URL = 'patch_url'


def get_token_from_keystone(auth_url: str, username: str, password: str, project_name: str = 'admin',
                            user_domain_id: str = 'default', project_domain_id: str = 'default') -> str:
    """
    This function return keystone token.
    :param auth_url: Keystone url
    :param username: Keystone username
    :param password: Keystone password
    :param project_name: Keystone project
    :param user_domain_id: User domain id
    :param project_domain_id: Project domain id

    :rtype: str
    """
    auth = v3.Password(auth_url=auth_url,
                       username=username,
                       password=password,
                       project_name=project_name,
                       user_domain_id=user_domain_id,
                       project_domain_id=project_domain_id)

    sess = session.Session(auth=auth)
    token = sess.get_token()

    return token


def get_endpoints(auth_url: str, headers: dict) -> dict:
    """
    Returns API URLS for DcManager and Patch API.

    :param auth_url: Keystone auth url
    :param headers: Header containing token

    :rtype: dict
    """
    url = '{}/auth/catalog'.format(auth_url)
    endpoints = requests.get(url=url, headers=headers)
    all_endpoints = {}

    for entity in endpoints.json()['catalog']:
        if entity['type'] == 'dcmanager':
            for endpoint in entity['endpoints']:
                if endpoint['interface'] == 'public':
                    all_endpoints[DC_MANAGER_API_URL] = endpoint['url']
                    break

        if entity['type'] == 'patching':
            for endpoint in entity['endpoints']:
                if endpoint['interface'] == 'public':
                    all_endpoints[PATCHING_API_URL] = endpoint['url']
                    break

    return all_endpoints
