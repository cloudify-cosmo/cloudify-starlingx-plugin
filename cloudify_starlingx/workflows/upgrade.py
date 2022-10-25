
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
    
    _download_wind_river_cloud_platform_deployment(ctx=ctx, sw_version=sw_version, deployment_manager_file=deployment_manager_file)
    _upgrade_deployment_manager(ctx=ctx)
    _verify_deployment_manager_upgrade(ctx=ctx, sw_version=sw_version)


def _download_wind_river_cloud_platform_deployment(sw_version, deployment_manager_file, ctx=None):
    """
        download
        https://github.com/Wind-River/cloud-platform-deployment-manager/blob/master/docs/playbooks/wind-river-cloud-platform-deployment-manager.yaml
        to controler-0
    """
    #TODO - find way how to check if WRCP_2105.zip is downloaded
    # ctx = ctx or wtx
    # download_command = 'curl --output {} https://raw.githubusercontent.com/Wind-River/cloud-platform-deployment-manager/master/docs/playbooks/wind-river-cloud-platform-deployment-manager.yaml'
    # resp = _run_ssh_command(ctx, download_command.format(deployment_manager_file))


def _upgrade_deployment_manager(inventory='controller-0', extra_var='@ansible-overrides.yaml', user='sysdamin', ssh_password='',
                                deployment_manager_file='/wind-river-cloud-platform-deployment-manager.yaml', ctx=None, verify_installation=True):
    """
        4. Upgrade Deployment Manager.
        ~(keystone_admin)] ansible-playbook --inventory controller-0, --extra-var "@ansible-overrides.y
        aml" --ask-pass --ask-become-pass --user sysadmin WRCP_2105/wind-river-cloud-platform-deploymen
        t-manager.yaml
    """
    ctx = ctx or wtx
    responses = [{"question": "SSH password:", "answer": ssh_password},
                 {"question": "SUDO password[defaults to SSH password]:", "answer": ssh_password},
                ]
    ansible_command = 'ansible-playbook --inventory {}, --extra-var "{}" --ask-pass --ask-become-pass --user {} {}'
    resp = _run_ssh_command(ctx, ansible_command.format(inventory, extra_var, user, deployment_manager_file))

def _verify_deployment_manager_upgrade(inventory='controller-0', namespace='platform-deployment-manager',
                                       pod_name='platform-deployment-manager-0', sw_version=None, ctx=None):
    cmd_image = 'kubectl describe pod -n {} {} | grep Image'
    pods_list = 'kubectl get pods -n {}'
    img_output = _run_ssh_command(ctx, cmd_image.format(namespace, pod_name))
    image_version = re.findall('cloud-platform-deployment-manager:(.*)', img_output)[-1].replace('.','')
    if image_version not in sw_version:
        raise NonRecoverableError  ## -> correct?
