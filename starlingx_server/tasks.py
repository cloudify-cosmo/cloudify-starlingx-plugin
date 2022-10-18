########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


# 'ctx' is always passed as a keyword argument to operations, so
# your operation implementation must either specify it in the arguments
# list, or accept '**kwargs'. Both are shown here.
from cloudify.decorators import operation

from starlingxplugin.sdk.client import StarlingxPatchClient


@operation
def get_api_version(ctx, **kwargs):
    # getting node instance runtime property
    api_url = ctx.node.properties.get('api_url')
    keystone_url = ctx.node.properties.get('keystone_url')
    keystone_username = ctx.node.properties.get('keystone_username')
    keystone_password = ctx.node.properties.get('keystone_password')
    keystone_project_name = ctx.node.properties.get('keystone_project_name')
    keystone_user_domain_id = ctx.node.properties.get('keystone_user_domain_id')
    keystone_project_domain_id = ctx.node.properties.get('keystone_project_domain_id')

    client = StarlingxPatchClient.get_patch_client(api_url=api_url, auth_url=keystone_url, username=keystone_username,
                                                   password=keystone_password, project_name=keystone_project_name,
                                                   user_domain_id=keystone_user_domain_id,
                                                   project_domain_id=keystone_project_domain_id)
    res = client.get_api_version()

    ctx.logger.info("Available API version: {}".format(res))


@operation
def get_list_of_patches(ctx, **kwargs):
    # getting node instance runtime property
    api_url = ctx.node.properties.get('api_url')
    keystone_url = ctx.node.properties.get('keystone_url')
    keystone_username = ctx.node.properties.get('keystone_username')
    keystone_password = ctx.node.properties.get('keystone_password')
    keystone_project_name = ctx.node.properties.get('keystone_project_name')
    keystone_user_domain_id = ctx.node.properties.get('keystone_user_domain_id')
    keystone_project_domain_id = ctx.node.properties.get('keystone_project_domain_id')

    client = StarlingxPatchClient.get_patch_client(api_url=api_url, auth_url=keystone_url, username=keystone_username,
                                                   password=keystone_password, project_name=keystone_project_name,
                                                   user_domain_id=keystone_user_domain_id,
                                                   project_domain_id=keystone_project_domain_id)
    res = client.get_list_of_patches()

    ctx.logger.info("List of available patches: {}".format(res))


@operation
def get_patch_details(ctx, **kwargs):
    # getting node instance runtime property
    api_url = ctx.node.properties.get('api_url')
    keystone_url = ctx.node.properties.get('keystone_url')
    keystone_username = ctx.node.properties.get('keystone_username')
    keystone_password = ctx.node.properties.get('keystone_password')
    keystone_project_name = ctx.node.properties.get('keystone_project_name')
    keystone_user_domain_id = ctx.node.properties.get('keystone_user_domain_id')
    keystone_project_domain_id = ctx.node.properties.get('keystone_project_domain_id')
    patch_id = ctx.node.properties.get('patch_id')

    client = StarlingxPatchClient.get_patch_client(api_url=api_url, auth_url=keystone_url, username=keystone_username,
                                                   password=keystone_password, project_name=keystone_project_name,
                                                   user_domain_id=keystone_user_domain_id,
                                                   project_domain_id=keystone_project_domain_id)
    res = client.get_patch_details(patch_id=patch_id)

    ctx.logger.info("List of available patches: {}".format(res))


@operation
def apply_patch(ctx, **kwargs):
    # getting node instance runtime property
    api_url = ctx.node.properties.get('api_url')
    keystone_url = ctx.node.properties.get('keystone_url')
    keystone_username = ctx.node.properties.get('keystone_username')
    keystone_password = ctx.node.properties.get('keystone_password')
    keystone_project_name = ctx.node.properties.get('keystone_project_name')
    keystone_user_domain_id = ctx.node.properties.get('keystone_user_domain_id')
    keystone_project_domain_id = ctx.node.properties.get('keystone_project_domain_id')
    patch_id = ctx.node.properties.get('patch_id')

    client = StarlingxPatchClient.get_patch_client(api_url=api_url, auth_url=keystone_url, username=keystone_username,
                                                   password=keystone_password, project_name=keystone_project_name,
                                                   user_domain_id=keystone_user_domain_id,
                                                   project_domain_id=keystone_project_domain_id)
    res = client.apply_patch(patch_id=patch_id)

    ctx.logger.info("Patch applied: {}".format(res))


@operation
def upload_patch(ctx, **kwargs):
    # getting node instance runtime property
    api_url = ctx.node.properties.get('api_url')
    keystone_url = ctx.node.properties.get('keystone_url')
    keystone_username = ctx.node.properties.get('keystone_username')
    keystone_password = ctx.node.properties.get('keystone_password')
    keystone_project_name = ctx.node.properties.get('keystone_project_name')
    keystone_user_domain_id = ctx.node.properties.get('keystone_user_domain_id')
    keystone_project_domain_id = ctx.node.properties.get('keystone_project_domain_id')
    patch_dir = ctx.node.properties.get('patch_dir')

    client = StarlingxPatchClient.get_patch_client(api_url=api_url, auth_url=keystone_url, username=keystone_username,
                                                   password=keystone_password, project_name=keystone_project_name,
                                                   user_domain_id=keystone_user_domain_id,
                                                   project_domain_id=keystone_project_domain_id)
    res = client.apply_patch(patch_id=patch_dir)

    ctx.logger.info("Patch applied: {}".format(res))


@operation
def remove_patch(ctx, **kwargs):
    # getting node instance runtime property
    api_url = ctx.node.properties.get('api_url')
    keystone_url = ctx.node.properties.get('keystone_url')
    keystone_username = ctx.node.properties.get('keystone_username')
    keystone_password = ctx.node.properties.get('keystone_password')
    keystone_project_name = ctx.node.properties.get('keystone_project_name')
    keystone_user_domain_id = ctx.node.properties.get('keystone_user_domain_id')
    keystone_project_domain_id = ctx.node.properties.get('keystone_project_domain_id')
    patch_id = ctx.node.properties.get('patch_id')

    client = StarlingxPatchClient.get_patch_client(api_url=api_url, auth_url=keystone_url, username=keystone_username,
                                                   password=keystone_password, project_name=keystone_project_name,
                                                   user_domain_id=keystone_user_domain_id,
                                                   project_domain_id=keystone_project_domain_id)
    res = client.remove_patch(patch_id=patch_id)

    ctx.logger.info("Patch removed: {}".format(res))


@operation
def delete_patch(ctx, **kwargs):
    # getting node instance runtime property
    api_url = ctx.node.properties.get('api_url')
    keystone_url = ctx.node.properties.get('keystone_url')
    keystone_username = ctx.node.properties.get('keystone_username')
    keystone_password = ctx.node.properties.get('keystone_password')
    keystone_project_name = ctx.node.properties.get('keystone_project_name')
    keystone_user_domain_id = ctx.node.properties.get('keystone_user_domain_id')
    keystone_project_domain_id = ctx.node.properties.get('keystone_project_domain_id')
    patch_id = ctx.node.properties.get('patch_id')

    client = StarlingxPatchClient.get_patch_client(api_url=api_url, auth_url=keystone_url, username=keystone_username,
                                                   password=keystone_password, project_name=keystone_project_name,
                                                   user_domain_id=keystone_user_domain_id,
                                                   project_domain_id=keystone_project_domain_id)
    res = client.delete_patch(patch_id=patch_id)

    ctx.logger.info("Patch deleted: {}".format(res))


@operation
def query_hosts(ctx, **kwargs):
    # getting node instance runtime property
    api_url = ctx.node.properties.get('api_url')
    keystone_url = ctx.node.properties.get('keystone_url')
    keystone_username = ctx.node.properties.get('keystone_username')
    keystone_password = ctx.node.properties.get('keystone_password')
    keystone_project_name = ctx.node.properties.get('keystone_project_name')
    keystone_user_domain_id = ctx.node.properties.get('keystone_user_domain_id')
    keystone_project_domain_id = ctx.node.properties.get('keystone_project_domain_id')

    client = StarlingxPatchClient.get_patch_client(api_url=api_url, auth_url=keystone_url, username=keystone_username,
                                                   password=keystone_password, project_name=keystone_project_name,
                                                   user_domain_id=keystone_user_domain_id,
                                                   project_domain_id=keystone_project_domain_id)
    res = client.query_hosts()

    ctx.logger.info("Hosts: {}".format(res))


@operation
def host_install(ctx, **kwargs):
    # getting node instance runtime property
    api_url = ctx.node.properties.get('api_url')
    keystone_url = ctx.node.properties.get('keystone_url')
    keystone_username = ctx.node.properties.get('keystone_username')
    keystone_password = ctx.node.properties.get('keystone_password')
    keystone_project_name = ctx.node.properties.get('keystone_project_name')
    keystone_user_domain_id = ctx.node.properties.get('keystone_user_domain_id')
    keystone_project_domain_id = ctx.node.properties.get('keystone_project_domain_id')
    hostname = ctx.node.properties.get('hostname')

    client = StarlingxPatchClient.get_patch_client(api_url=api_url, auth_url=keystone_url, username=keystone_username,
                                                   password=keystone_password, project_name=keystone_project_name,
                                                   user_domain_id=keystone_user_domain_id,
                                                   project_domain_id=keystone_project_domain_id)
    res = client.host_install(hostname=hostname)

    ctx.logger.info("Host installed: {}".format(res))
