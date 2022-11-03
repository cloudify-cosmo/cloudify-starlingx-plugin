import os

import requests
from requests_toolbelt import MultipartEncoder

from sdk.keystone_auth import get_token_from_keystone, get_endpoints, PATCHING_API_URL


class StarlingxPatchClient(object):
    """
    StarlingX Patch API client for specification taken from:
    https://docs.starlingx.io/api-ref/update/api-ref-patching-v1-update.html?expanded=
    uploads-a-patch-to-the-patching-system-detail,shows-detailed-information-about-a-specific-patch-detail,deletes-a-patch-that-is-in-the-available-state-detail,removes-a-patch-that-is-in-the-applied-state-detail,applies-a-patch-that-is-in-the-available-state-detail#
    """

    AVAILABLE_VERSION = 'v1'

    @classmethod
    def get_patch_client(cls, auth_url: str, username: str, password: str, project_name: str = 'admin',
                         user_domain_id: str = 'default', project_domain_id: str = 'default'):
        """
        Instantiate API client together with gathering token from Keystone.

        :param auth_url: URL for Keystone
        :param username: Username for Keystone
        :param password: Password for Keystone
        :param project_name: Project name for Keystone
        :param user_domain_id: User domain ID for Keystone
        :param project_domain_id: Project domain ID for Keystone
        """

        token = get_token_from_keystone(auth_url=auth_url, username=username, password=password,
                                        project_name=project_name, user_domain_id=user_domain_id,
                                        project_domain_id=project_domain_id)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "X-Auth-Token": token
        }

        all_endpoints = get_endpoints(auth_url=auth_url, headers=headers)
        return cls(url=all_endpoints[PATCHING_API_URL], headers=headers)

    @classmethod
    def get_for_mock_server(cls, keystone_password: str):
        """
        This method will instantiate StarlingX client for Mock testing.

        :type keystone_password: Password for the keystone admin user
        """
        url = "http://localhost:15491"

        token = get_token_from_keystone(auth_url='http://localhost:5000/v3', username='admin', password=keystone_password)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "X-Auth-Token": token
        }

        return cls(url=url, headers=headers)

    def __init__(self, url: str, headers: dict):
        self.connection = None
        self.url = url
        self.headers = headers

    def _api_call(self, api_call_type: requests, url='', headers=None, check_status=False, is_json=True, **kwargs):
        """
            General method to execute requests call
            :params - https://requests.readthedocs.io/en/latest/api/ 
            :rtype: dict or str
        """
        url = url or self.url
        headers = headers or self.headers

        try:
            response = api_call_type(url=url, headers=headers, **kwargs)
        except requests.exceptions.HTTPError as e:
            return {
                'message': "Http Error: {}".format(e),
                'error': "True",
            }
        except requests.exceptions.ConnectionError as e:
            return {
                'message': "Error Connecting: {}".format(e),
                'error': "True",
            }
        except requests.exceptions.Timeout as e:
            return {
                'message': "Timeout Error: {}".format(e),
                'error': "True",
            }
        except requests.exceptions.RequestException as e:
            return {
                'message': "Unsupported error: {}".format(e),
                'error': "True",
            }

        if check_status:
            response.raise_for_status()
        return response.json() if is_json else response.text

    def get_api_version(self) -> str:
        """
        This method returns information about supported version

        :rtype: str
        """
        return self._api_call(api_call_type=requests.get, is_json=False)

    def get_list_of_patches(self) -> dict:
        """
        This method returns list of available patches.

        :rtype: list
        """
        endpoint = "{}/{}/query".format(self.url, self.AVAILABLE_VERSION)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def get_patch_details(self, patch_id: str) -> dict:
        """
        This method returns detailed information about given patch id.

        :param patch_id: Patch ID
        :rtype: dict
        """
        endpoint = "{}/{}/show/{}".format(self.url, self.AVAILABLE_VERSION, patch_id)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def upload_patch(self, patch_dir: str) -> list:
        """
        This method uploads patch to StarlingX.

        :param patch_dir: Patch to be applied
        :rtype: list
        """
        ret = []

        endpoint = "{}/{}/upload".format(self.url, self.AVAILABLE_VERSION)
        for file in os.listdir(patch_dir):
            f = '{}/{}'.format(patch_dir, file)
            if os.path.isfile(f):
                enc = MultipartEncoder(fields={'file': (f, open(f, 'rb'),)})
                # Change content type from json to enc
                self.headers['Content-Type'] = enc.content_type

                out = self._api_call(api_call_type=requests.post,
                                     url=endpoint,
                                     data=enc,
                                     allow_redirects=False)
                ret.append(out)

        return ret

    def apply_patch(self, patch_id: str) -> dict:
        """
        This method applies given patch that is in available state to StarlingX.

        :param patch_id: Patch ID to be applied into StarlingX
        :rtype: dict
        """
        endpoint = "{}/{}/apply/{}".format(self.url, self.AVAILABLE_VERSION, patch_id)
        return self._api_call(api_call_type=requests.post, url=endpoint)

    def remove_patch(self, patch_id: str) -> dict:
        """
        This method removes a patch that is in the applied state.
        :param patch_id: Patch ID to be removed from StarlingX
        :rtype: dict
        """

        endpoint = "{}/{}/remove/{}".format(self.url, self.AVAILABLE_VERSION, patch_id)
        return self._api_call(api_call_type=requests.post, url=endpoint)

    def delete_patch(self, patch_id: str) -> dict:
        """
        This method deletes a patch that is in the available state.

        :param patch_id: Patch ID to be removed from StarlingX
        :rtype: dict
        """
        endpoint = "{}/{}/delete/{}".format(self.url, self.AVAILABLE_VERSION, patch_id)
        return self._api_call(api_call_type=requests.post, url=endpoint)

    def query_hosts(self) -> dict:
        """
        This method lists all host entities and their patching information.

        :rtype: dict
        """
        endpoint = "{}/{}/query_hosts".format(self.url, self.AVAILABLE_VERSION)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def host_install(self, hostname: str) -> dict:
        """
        This method triggers an asynchronous host install on the specified host.

        :param hostname: Dedicated host where install operation should be triggered
        :rtype: dict
        """
        endpoint = "{}/{}/host_install_async/{}".format(self.url, self.AVAILABLE_VERSION, hostname)
        return self._api_call(api_call_type=requests.post, url=endpoint)
