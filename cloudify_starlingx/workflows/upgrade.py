
from argparse import Namespace
import re

from http.client import responses
from cloudify.decorators import workflow
from cloudify.workflows import ctx as wtx
from cloudify_terminal_sdk.terminal_connection import SmartConnection
from cloudify.exceptions import NonRecoverableError


def smart_connection(func):
    def inner_func(ctx, command, source=True):
        # TODO find way to get info from ctx
        ip = ''
        user = ''
        password = ''
        port = 22
        source = 'source /etc/platform/openrc && {}'
        cmd = source.format(command) if source else command
        func(ip, user, password, port, cmd)
    return inner_func

@smart_connection
def _run_ssh_command(ip, user, password, port, ctx=None, command=''):
    ssh_client = SmartConnection()
    ssh_client.connect(ip=ip, user=user, password=password, port=port)
    out = ssh_client.run(command=command)
    return out

@workflow
def upgrade_service(node_instance_id=None, node_id=None, sw_path=None, sw_version=None, ctx=None, **_):
    """
        Once you have completed a platform upgrade from Wind River Cloud Platform Release 20.06 to Release 21.05,
    """
    deployment_manager_file = 'wind-river-cloud-platform-deployment-manager.yaml'
    inventory='controller-0'
    extra_var='@ansible-overrides.yaml'
    user='sysdamin'
    ssh_password='',
    deployment_manager_file_path='/wind-river-cloud-platform-deployment-manager.yaml'
    namespace='platform-deployment-manager'
    pod_name='platform-deployment-manager-0'
    deploy_overrides = 'wind-river-cloud-platform-deployment-manager-overrides.yaml'
    deployment_manager_tgz_file_path = 'WRCP_2105/wind-river-cloud-platform-deployment-manager-2.0.6.tgz'
    
    # UPGRADE DEPLOYMENT MANAGER
    _download_wind_river_cloud_platform_deployment(ctx=ctx, sw_version=sw_version, sw_path=sw_path,deployment_manager_file=deployment_manager_file)
    _upgrade_deployment_manager(ctx=ctx, inventory=inventory, extra_var=extra_var, user=user, ssh_password=ssh_password,
                                deployment_manager_file_path=deployment_manager_file_path, ctx=ctx)
    _verify_deployment_manager_upgrade(namespace=namespace, pod_name=pod_name, sw_version=sw_version, ctx=ctx)
    _deploy_the_updated_deployment_manager_files(deployment_manager_file_path=deployment_manager_tgz_file_path, deploy_overrides=deploy_overrides,
                                                 deployment_manager_tgz_file_path=deployment_manager_tgz_file_path, ctx=ctx)
    # Upgrading the System Controller
    _upgrade_the_system_controller()


def _download_wind_river_cloud_platform_deployment(sw_version, sw_path, deployment_manager_file, ctx=None):
    """
        download
        https://github.com/Wind-River/cloud-platform-deployment-manager/blob/master/docs/playbooks/wind-river-cloud-platform-deployment-manager.yaml
        to controler-0
    """
    pass
    #TODO - find way how to check if WRCP_2105.zip is downloaded
    # ctx = ctx or wtx
    # download_command = 'curl --output {} https://raw.githubusercontent.com/Wind-River/cloud-platform-deployment-manager/master/docs/playbooks/wind-river-cloud-platform-deployment-manager.yaml'
    # resp = _run_ssh_command(ctx, download_command.format(deployment_manager_file))


def _upgrade_deployment_manager(inventory, extra_var, user, ssh_password, deployment_manager_file_path, ctx=None):
    """
        4. Upgrade Deployment Manager.
        ~(keystone_admin)] ansible-playbook --inventory controller-0, --extra-var "@ansible-overrides.yaml" 
        --ask-pass --ask-become-pass --user sysadmin WRCP_2105/wind-river-cloud-platform-deployment-manager.yaml
    """
    ctx = ctx or wtx
    responses = [{"question": "SSH password:", "answer": ssh_password},
                 {"question": "SUDO password[defaults to SSH password]:", "answer": ssh_password},
                ]
    ansible_command = 'ansible-playbook --inventory {}, --extra-var "{}" --ask-pass --ask-become-pass --user {} {}'
    resp = _run_ssh_command(ctx, ansible_command.format(inventory, extra_var, user, deployment_manager_file_path))


def _verify_deployment_manager_upgrade(namespace, pod_name, sw_version=None, ctx=None):
    """
        5. Verify if the upgrade is completed.
        ~(keystone_admin)] kubectl describe pod -n platform-deployment-manager platform-deployment-mana
        ger-0 | grep Image
        Image: registry.local:9001/gcr.io/kubebuilder/kube-rbac-proxy:v0.4.0
        Image ID: registry.local:9001/gcr.io/kubebuilder/kube-rbac-proxy@sha256:297896d96b827bbcb1
        abd696da1b2d81cab88359ac34cce0e8281f266b4e08de
        Image: registry.local:9001/docker.io/wind-river/cloud-platform-deployment-manager:WRCP_
        21.05
        Image ID: registry.local:9001/docker.io/wind-river/cloud-platform-deployment-manager@sha25
        6:37b14a5ad085da28b288f553bd2e49dee1649977ff01790e5a20cccab981a7ce
        6. Verify if the Deployment Manager application is running using the following command.
        ~(keystone_admin)] kubectl get pods -n platform-deployment-manager
        NAME READY STATUS RESTARTS AGE
        platform-deployment-manager-0 2/2 Running 1 119m
        7. List the images used in the pod.
        ~(keystone_admin)] kubectl describe pod -n platform-deployment-manager platform-deployment-mana
        ger-0 | grep Image
        Image: registry.local:9001/gcr.io/kubebuilder/kube-rbac-proxy:v0.4.0
        Image ID: registry.local:9001/gcr.io/kubebuilder/kube-rbac-proxy@sha256:297896d96b827bbcb1
        abd696da1b2d81cab88359ac34cce0e8281f266b4e08de
        Image: registry.local:9001/docker.io/wind-river/cloud-platform-deployment-manager:WRCP_
        21.05
        Image ID: registry.local:9001/docker.io/wind-river/cloud-platform-deployment-manager@sha25
        6:37b14a5ad085da28b288f553bd2e49dee1649977ff01790e5a20cccab981a7ce
    """
    cmd_image = 'kubectl describe pod -n {} {} | grep Image'
    pods_list = 'kubectl get pods -n {}'
    img_output = _run_ssh_command(ctx, cmd_image.format(namespace, pod_name))
    image_version = re.findall('cloud-platform-deployment-manager:(.*)', img_output)[-1].replace('.','')
    if image_version not in sw_version:
        raise NonRecoverableError  ## -> correct?
    pod_list = _run_ssh_command(ctx, pods_list.format(namespace))


def _deploy_the_updated_deployment_manager_files(deployment_manager_file_path, deploy_overrides, deployment_manager_tgz_file_path, ctx=None):
    """
        ~(keystone_admin)] dcmanager subcloud-deploy upload --deploy-playbook WRCP_2105/wind-river-clou
        d-platform-deployment-manager.yaml --deploy-overrides wind-river-cloud-platform-deployment-mana
        ger-overrides.yaml --deploy-chart WRCP_2105/wind-river-cloud-platform-deployment-manager-2.0.6.
        tgz
        +------------------+------------------------------------------------------------------+
        | Field | Value |
        +------------------+------------------------------------------------------------------+
        | deploy_playbook | WRCP_2105/wind-river-cloud-platform-deployment-manager.yaml |
        | deploy_overrides | wind-river-cloud-platform-deployment-manager-overrides.yaml |
        | deploy_chart | WRCP_2105/wind-river-cloud-platform-deployment-manager-2.0.6.tgz |
        +------------------+------------------------------------------------------------------+
    """
    command = "dcmanager subcloud-deploy upload --deploy-playbook {} --deploy-overrides {} --deploy-chart {}"
    _run_ssh_command(ctx,command.format(deployment_manager_file_path,  deploy_overrides, deployment_manager_tgz_file_path))


def _upgrade_the_system_controller():
    """
        1. Create an ansible-overrides.yaml file.
        ansible_become_pass: <sysadmin password>
        deployment_manager_overrides: /home/sysadmin/helm-chart-overrides.yaml
        deployment_manager_chart: /home/sysadmin/wind-river-cloud-platform-deployment-manager-2.0.6.tgz
        Where helm-chart-overrides.yaml contains the following:
        manager:
        image:
        repository: registry.local:9001/docker.io/wind-river/cloud-platform-deployment-manager
        tag: WRCP_21.05
        pullPolicy: IfNotPresent
        rbacProxy:
        image: registry.local:9001/gcr.io/kubebuilder/kube-rbac-proxy:v0.4.0
        2. Execute the following command.
        ~(keystone_admin)] ansible-playbook wind-river-cloud-platform-deployment-manager.yaml -e @ansible-overrides.yaml
    """
    _
