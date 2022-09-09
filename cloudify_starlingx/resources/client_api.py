from cloudify_starlingx_sdk.resources.configuration import SystemResource
from ..decorators import with_starlingx_resource


@with_starlingx_resource(SystemResource)
def get_patches_list(resource, ctx):
    """
    Patching endpoint: /v1/query
    Lists all patches in the patching system
    """

    # Instantiate StarlingClient -> How to pass config parameters?
    client = StarlingClient(api_url='', user_name='', password='', api_key='')
    client.get_patches_list()


@with_starlingx_resource(SystemResource)
def get_patch_details(resource, ctx):
    """
    Patching endpoint: /v1/show/{patch_id}
    Shows detailed information about a specific patch
    """
    # Instantiate StarlingClient -> How to pass config parameters?
    client = StarlingClient(api_url='', user_name='', password='', api_key='')

    # How to pass patch_id from the cloudify.types.starlingx.Patch?
    client.get_patch_details(patch_id='')


class StarlingClient(object):
    PATCHES_LIST_ENDPOINT = '/v1/query'
    PATCH_DETAILS_ENDPOINT = '/v1/show'

    def __init__(self, api_url: str, user_name: str, password: str, api_key: str):
        """
        Constructs all the necessary attributes for the StarlingClient object.
        Parameters
        ----------
            api_url : str
                url for StarlingX service
            user_name : str
                user_name for the api call
            password : str
                password for the api call
            api_key : str
                api key for the request
        """

        self.api_url = api_url
        self.user_name = user_name
        self.password = password
        self.api_key = api_key

    def get_patches_list(self):
        """
        Get the list of all available patches using StarlingX API call.
        """
        pass

    def get_patch_details(self, patch_id: str):
        """
        Gets details for given patch_id using StarlingX API call.
        Parameters
        ----------
            patch_id : str
                patch id to get details for

        """
        pass
