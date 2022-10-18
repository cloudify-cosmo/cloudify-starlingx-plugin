import re

from ..utils import (
    get_child_deployments)

from ...starlingx_server.sdk.client import StarlingxPatchClient
from ...starlingx_server.sdk.dcmanager import StarlingxDcManagerClient


def upload_patch(resource, ctx, autoapply: bool, refresh_status: bool, patch_dir: str, **kwargs):
    """
        Steps:
        1. Upload patch from patch dir
        2. Apply patch (optional)
        3. Check status (optional)
        :param autoapply: make patch apply
        :param patch_dir: patch directory
        :param refresh_status: refresh status of subcloud
    """
    client_config = resource.client_config
    auth_url = client_config.get('auth_url')
    username = client_config.get('username')
    password = client_config.get('api_key')
    project_name = client_config.get('project_name')
    user_domain_id = client_config.get('user_domain_id')
    project_domain_id = client_config.get('project_domain_id')    

    # ctx.logger.info("""auth_url={},username={},password={},project_name={}, user_domain_id={},
    # #                                                      project_domain_id={}""".format(res))
    patch_client = StarlingxPatchClient.get_patch_client(auth_url=auth_url, username=username, password=password,
                                                         project_name=project_name, user_domain_id=user_domain_id,
                                                         project_domain_id=project_domain_id)
    outputs = patch_client.upload_patch(patch_dir=patch_dir)

    if autoapply:
        for output in outputs:
            patch_id = re.findall(' \"(.*) is now available', output)
            apply_patch(resource=resource, ctx=ctx, patch_id=patch_id)

    if refresh_status:
        refresh_status(ctx=ctx)



def apply_patch(resource, ctx, patch_id: str):
    client_config = resource.client_config
    auth_url = client_config.get('auth_url')
    username = client_config.get('username')
    password = client_config.get('api_key')
    project_name = client_config.get('project_name')
    user_domain_id = client_config.get('user_domain_id')
    project_domain_id = client_config.get('project_domain_id')    

    # ctx.logger.info("""auth_url={},username={},password={},project_name={}, user_domain_id={},
    # #                                                      project_domain_id={}""".format(res))
    patch_client = StarlingxPatchClient.get_patch_client(auth_url=auth_url, username=username, password=password,
                                                         project_name=project_name, user_domain_id=user_domain_id,
                                                         project_domain_id=project_domain_id)
    out = patch_client.apply_patch(patch_id=patch_id)
    assert out['info'] == '{} has been applied\n'.format(patch_id)                                                        


def refresh_status(ctx):
    deployment_id = ctx.deployment.id
    child_deployments =  get_child_deployments(deployment_id)
    for child_deployment in child_deployments:
        pass
