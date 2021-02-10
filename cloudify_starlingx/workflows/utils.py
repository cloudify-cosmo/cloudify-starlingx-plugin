# # #######
# # Copyright (c) 2021 Cloudify Platform Ltd. All rights reserved
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #        http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
#
# from copy import deepcopy
#
# from cloudify.workflows import ctx as wtx
# from cloudify.manager import get_rest_client
# from cloudify.exceptions import NonRecoverableError
#
#
# def get_instances_of_nodes(node_id=None, node_type=None):
#     """ Get instances of nodes either by node ID or node type.
#
#     :param node_id: The node ID to filter.
#     :param node_type: The node type to filter.
#     :return list: A list of node instances.
#     """
#
#     if node_id:
#         controller_node = wtx.get_node(node_id)
#         return controller_node.instances
#     elif node_type:
#         return get_node_instances_by_type(
#             get_deployment_node_instances(), node_type)
#     else:
#         raise NonRecoverableError('No node_id and no node_type provided.')
#
#
# def get_deployment_node_instances():
#     """ Get node instances of the current deployment.
#
#     :return list: cloudify node instances
#     """
#     rest_client = get_rest_client()
#     return rest_client.nodes.list(deployment_id=wtx.deployment.id)
#
#
# def get_node_instances_by_type(nodes, node_type):
#     """Filter node instances by type.
#
#     :param nodes: The node objects from cloudify rest api
#     :param node_type: the node type that we wish to filter.
#     :return list: a list of node instances.
#     """
#
#     node_instances = []
#     for node in nodes:
#         if node_type in node.type_hierarchy:
#             for node_instance in node.instances:
#                 node_instances.append(node_instance)
#     return node_instances
#
#
# def update_runtime_properties(instance,
#                               resources,
#                               prop_name):
#     """
#
#     :param instance: The node instance to update.
#     :param resources: A list of resources to pull.
#     :param prop_name: The property on the instance to update.
#     :return:
#     """
#
#     rest_client = get_rest_client()
#
#     for resource in resources:
#         props = deepcopy(instance.runtime_properties)
#         prop = props.get(prop_name, {})
#         if resource.id not in prop:
#             prop.update({resource.resource_id: resource.to_dict()})
#         props[prop_name] = prop
#         rest_client.nodeinstances.update(instance.id,
#                                          instance.state,
#                                          props,
#                                          instance.state + 1)
