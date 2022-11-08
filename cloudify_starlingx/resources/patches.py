import re

from ..utils import (
    get_child_deployments,
    with_rest_client,
    add_new_label,
    get_parent_deployment,
    get_secret)
from ..decorators import with_starlingx_resource
from starlingx_server.sdk.client import StarlingxPatchClient
from starlingx_server.sdk.dcmanager import StarlingxDcManagerClient

from cloudify.exceptions import NonRecoverableError
from cloudify_starlingx_sdk.resources.configuration import SystemResource
from cloudify.exceptions import OperationRetry


@with_starlingx_resource(SystemResource)
def upload_and_apply_patch(resource, ctx, autoapply: bool, refresh_status: bool, patch_dir: str,
                           type_of_strategy: str, subcloud_apply_type: str, strategy_action: str,
                           max_parallel_subclouds: int, stop_on_failure: bool, **kwargs):
    """
        Steps:
        1. Upload patch from patch dir
        2. Apply patch (optional)
        3. Check status (optional)
    """
    client_config = resource.client_config
    auth_url = client_config.get('os_auth_url')
    username = client_config.get('os_username')
    password = client_config.get('os_password')
    project_name = client_config.get('os_project_name')
    user_domain_name = client_config.get('os_user_domain_name', None)
    project_domain_name = client_config.get('os_project_domain_name', None)
    user_domain_id = client_config.get('os_user_domain_id', None)
    project_domain_id = client_config.get('os_project_domain_id', None)
    verify_value = True if client_config.get('insecure', None) else False
    patch_client = StarlingxPatchClient.get_patch_client(auth_url=auth_url, username=username, password=password,
                                                         project_name=project_name,
                                                         user_domain_name=user_domain_name,
                                                         project_domain_name=project_domain_name,
                                                         user_domain_id=user_domain_id,
                                                         project_domain_id=project_domain_id,
                                                         verify=verify_value)
    dc_patch_client = StarlingxDcManagerClient.get_patch_client(auth_url=auth_url, username=username, password=password,
                                                                project_name=project_name,
                                                                user_domain_name=user_domain_name,
                                                                project_domain_name=project_domain_name,
                                                                user_domain_id=user_domain_id,
                                                                project_domain_id=project_domain_id,
                                                                verify=verify_value)
    outputs = patch_client.upload_patch(patch_dir=patch_dir)

    if autoapply:
        for output, _code in outputs:
            if _code != 200:
                ctx.logger.error('{}'.format(output))
                raise NonRecoverableError
            if dict(output)['error']:
                ctx.logger.error('{}'.format(output))
                raise NonRecoverableError
            patch_id = re.findall('(.*) is', dict(output)['info'])[-1]
            ctx.logger.info('PATCH ID: {}'.format(patch_id))
            resp, _code = patch_client.get_patch_details(patch_id=patch_id)
            if _code >= 300:
                ctx.logger.error('{} is not uploaded'.format(patch_id))
                raise NonRecoverableError
            state = resp["metadata"][patch_id]["patchstate"]
            if state.lower() in 'applied':
                ctx.logger.warning('{} patch already applied'.format(patch_id))
                continue                

            resp, _code = patch_client.apply_patch(patch_id=patch_id)
            if resp.get('error', ''):
                ctx.logger.error('Apply patch error: {}'.format(resp.get('error', '')))
                raise NonRecoverableError
            if resp.get('warning', ''):
                ctx.logger.warning('Apply patch warn: {}'.format(resp.get('warning', '')))

        resp, _code = dc_patch_client.get_subcloud_update_strategy(type_of_strategy=type_of_strategy)
        ctx.logger.info('Strategy exist?: {}'.format(resp))
        if _code < 300:
            dc_patch_client.delete_update_strategy(type_of_strategy=type_of_strategy)

        resp, _code = dc_patch_client.create_subcloud_update_strategy(type_of_strategy=type_of_strategy,
                                                                      max_parallel_subclouds=max_parallel_subclouds,
                                                                      stop_on_failure=stop_on_failure,
                                                                      subcloud_apply_type=subcloud_apply_type)
        ctx.logger.info('Create subcloud update strategy logs.\n RESP: {}\nCODE: {}.'.format(resp, _code))
        # if _code >= 300:
        #     raise NonRecoverableError
        resp, _code = dc_patch_client.execute_action_on_strategy(type_of_strategy=type_of_strategy,
                                                                 action=strategy_action)
        ctx.logger.info('Action on strategy logs.\n RESP: {}\nCODE: {}.'.format(resp, _code))
        # if _code >= 300:
        #     raise NonRecoverableError

    if refresh_status:
        refresh_status_action(ctx=ctx)


@with_rest_client
@with_starlingx_resource(SystemResource)
def refresh_status_action(resource, ctx, rest_client):
    deployment_id = ctx.deployment.id
    child_deployment_ids = get_child_deployments(deployment_id_of_parent=deployment_id)
    for child_deployment_id in child_deployment_ids:
        rest_client.executions.start(
            deployment_id=child_deployment_id,
            workflow_id='check_status',
            queue=True
        )


def _get_status(resource, ctx, deployment_inputs):
    client_config = resource.client_config
    auth_url = deployment_inputs.get('auth_url')
    username = get_secret(secret_name=deployment_inputs.get('user_secret'))
    password = get_secret(secret_name=deployment_inputs.get('password_secret'))
    project_name = client_config.get('os_project_name')
    user_domain_name = client_config.get('os_user_domain_name', None)
    project_domain_name = client_config.get('os_project_domain_name', None)
    user_domain_id = client_config.get('os_user_domain_id', None)
    project_domain_id = client_config.get('os_project_domain_id', None)
    verify_value = False if deployment_inputs.get('insecure', None) else True
    subcloud_name = _get_subcloud_name(ctx=ctx)
    dc_patch_client = StarlingxDcManagerClient.get_patch_client(auth_url=auth_url, username=username, password=password,
                                                                project_name=project_name,
                                                                user_domain_name=user_domain_name,
                                                                project_domain_name=project_domain_name,
                                                                user_domain_id=user_domain_id,
                                                                project_domain_id=project_domain_id,
                                                                verify=verify_value)
    resp, _code = dc_patch_client.get_all_strategy_steps_for_cloud(subcloud_name)
    if isinstance(resp, dict):
        return resp["state"]
    if isinstance(resp, str):
        ctx.logger.warning('Strategy does not exist.\n{}'.format(resp))
        return 'complete'


@with_starlingx_resource(SystemResource)
def check_status(resource, ctx):
    statuses_list = ['complete', 'failed']
    deployment_id = ctx.deployment.id
    deployment_info = get_parent_deployment(deployment_id=deployment_id)
    ctx.logger.info('Parent deployment: {}'.format(deployment_info))
    status = _get_status(resource, ctx, deployment_inputs=deployment_info['inputs'])
    if status not in statuses_list:
        raise OperationRetry
    else:
        add_new_label('csys-subcloud-status',
                      status,
                      deployment_id)


def _get_subcloud_name(ctx):
    subcloud_dict = ctx.instance.runtime_properties.get('subcloud', {})
    return str(list(subcloud_dict.items())[0][1]['name'])


def _get_subclouds_names(ctx):
    subcloud_dict = ctx.instance.runtime_properties.get('subclouds', {})
    return list(subcloud_dict.items())[0][1]['name'] #TODO
