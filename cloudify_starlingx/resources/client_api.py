from cloudify_starlingx_sdk.resources.configuration import SystemResource
from ..decorators import with_starlingx_resource


@with_starlingx_resource(SystemResource)
def get_patches_list(resource, ctx):
    """
    Patching endpoint: /v1/query
    Lists all patches in the patching system
    """
    pass


@with_starlingx_resource(SystemResource)
def get_patches_details(resource, ctx):
    """
    Patching endpoint: /v1/show/{patch_id}
    Shows detailed information about a specific patch
    """
    pass
