# #######
# Copyright (c) 2021 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from cloudify.exceptions import NonRecoverableError
from cloudify.constants import NODE_INSTANCE, RELATIONSHIP_INSTANCE


def resolve_node_ctx_from_relationship(_ctx):
    """
    This method is to decide where to get node from relationship context
    since this is not exposed correctly from cloudify
    :param _ctx: current cloudify context object
    :return: RelationshipSubjectContext instance
    """
    # Get the node_id for the current node in order to decide if that node
    # is source | target
    node_id = _ctx._context.get('node_id')

    source_node_id = _ctx.source._context.get('node_id')
    target_node_id = _ctx.target._context.get('node_id')

    if node_id == source_node_id:
        return _ctx.source
    elif node_id == target_node_id:
        return _ctx.target
    else:
        raise NonRecoverableError(
            'Unable to decide if current node is source or target')


def resolve_ctx(_ctx):
    """
    This method is to lookup right context instance which could be one of
    the following:
     1- Context for source relationship instance
     2- Context for target relationship instance
     3- Context for current node
    :param _ctx: current cloudify context object
    :return: This could be RelationshipSubjectContext or CloudifyContext
    instance
    """
    if _ctx.type == RELATIONSHIP_INSTANCE:
        return resolve_node_ctx_from_relationship(_ctx)
    if _ctx.type != NODE_INSTANCE:
        _ctx.logger.warn(
            'CloudifyContext is neither {0} nor {1} type. '
            'Falling back to {0}. This indicates a problem.'.format(
                NODE_INSTANCE, RELATIONSHIP_INSTANCE))
    return _ctx


def update_prop_resource(ctx_instance, resource, config_key=None):
    config_key = config_key or 'resource_config'
    resource_config = ctx_instance.runtime_properties.get(config_key, {})
    resource_config.update(resource.to_dict())
    ctx_instance.runtime_properties[config_key] = resource_config
    ctx_instance.update()


def update_prop_resources(ctx_instance, resources, config_key=None):
    for resource in resources:
        update_prop_resource(ctx_instance, resource, config_key)


def update_kubernetes_props(ctx_instance, resources):
    for cluster in resources:
        ctx_instance.runtime_properties['k8s_ip'] = \
            cluster.resource.cluster_api_endpoint
        ctx_instance.runtime_properties['k8s_service_account_token'] = \
            cluster.resource.admin_token
        ctx_instance.runtime_properties['k8s_cert'] = \
            cluster.resource.cluster_ca_cert
        break
