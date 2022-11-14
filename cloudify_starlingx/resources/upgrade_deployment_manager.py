import re

from cloudify.decorators import workflow
from cloudify.workflows import ctx as wtx
from cloudify_terminal_sdk.terminal_connection import SmartConnection
from cloudify.exceptions import NonRecoverableError


def smart_connection(func):
    def inner_func(ctx: object, command: str, responses: object = None, source: bool = True) -> object:
        # TODO find way to get info from ctx
        ip = ''
        user = ''
        password = ''
        port = 22
        source_cmd = 'source /etc/platform/openrc && {}'
        cmd = source_cmd.format(command) if source else command
        func(ip, user, password, port, cmd, responses, ctx=ctx)
    return inner_func


@smart_connection
def _run_ssh_command(ip, user, password, port, command='', responses=None, ctx=None):
    ssh_client = SmartConnection()
    ssh_client.connect(ip=ip, user=user, password=password, port=port)
    out = ssh_client.run(command=command, responses=responses)
    return out


@workflow
def upgrade_deployment_manager(sw_version=None, ctx=None, **_):
    """
        Once you have completed a platform upgrade from Wind River Cloud Platform Release 20.06 to Release 21.05,
        sw_version: WRCP_21.05       
    """
    user = 'sysdamin'
    ssh_password = ''
    home_path = '/home/sysadmin'
    inventory = 'controller-0'
    namespace = 'platform-deployment-manager'
    pod_name = 'platform-deployment-manager-0'
    # sw_version = 'WRCP_21.05'
    sw_version_short = sw_version.replace('.', '')
    registry = 'registry.local:9001'
    manager_repo = '/docker.io/wind-river/cloud-platform-deployment-manager'
    rbac_proxy_image = '/gcr.io/kubebuilder/kube-rbac-proxy:v0.4.0'

    ansible_overrides_file = '{}/ansible-overrides.yaml'.format(home_path)
    deploy_overrides_file = '{}/wind-river-cloud-platform-deployment-manager-overrides.yaml'.format(home_path)
    deployment_manager_file = '{}/{}/wind-river-cloud-platform-deployment-manager.yaml'\
        .format(home_path, sw_version_short)
    deployment_manager_tgz_file = '{}/{}/wind-river-cloud-platform-deployment-manager-2.0.6.tgz'.\
        format(home_path, sw_version_short)
    helm_chart_path = '{}/helm-chart-overrides.yaml'.format(home_path)
    
    # UPGRADE DEPLOYMENT MANAGER
    _provide_the_required_files(sw_version=sw_version, deployment_manager_file=deployment_manager_file, ctx=ctx)
    _upgrade_deployment_manager(inventory=inventory, ansible_overrides_file=ansible_overrides_file,
                                user=user, ssh_password=ssh_password,
                                deployment_manager_file=deployment_manager_file, ctx=ctx)
    _verify_deployment_manager_upgrade(namespace=namespace, pod_name=pod_name, sw_version=sw_version, ctx=ctx)
    _deploy_the_updated_deployment_manager_files(deployment_manager_file=deployment_manager_file,
                                                 deploy_overrides_file=deploy_overrides_file,
                                                 deployment_manager_tgz_file=deployment_manager_tgz_file, ctx=ctx)
    # Upgrading the System Controller
    _upgrade_the_system_controller(ansible_overrides_file=ansible_overrides_file,
                                   deployment_manager_file=deployment_manager_file,
                                   sw_version=sw_version, helm_chart_path=helm_chart_path,
                                   deployment_manager_tgz_file_patch=deployment_manager_tgz_file,
                                   registry=registry, manager_repo=manager_repo, rbac_proxy_image=rbac_proxy_image)
    # Upgrading the Subcloud
    _upgrading_the_subcloud(ctx, deployment_manager_file,
                            deployment_manager_tgz_file, helm_chart_path,
                            new_subcloud_password=None)


def _provide_the_required_files(sw_version, deployment_manager_file, ctx=None):
    """
        download
        https://github.com/Wind-River/cloud-platform-deployment-manager/blob/master/docs/playbooks/wind-river-cloud-platform-deployment-manager.yaml
        to controler-0
    """
    pass
    # TODO - find way how to check if WRCP_2105.zip is downloaded
    ctx = ctx or wtx
    download_command = 'curl --output {} https://raw.githubusercontent.com/Wind-River/cloud-platform-deployment-' \
                       'manager/master/docs/playbooks/wind-river-cloud-platform-deployment-manager.yaml'
    resp = _run_ssh_command(ctx, download_command.format(deployment_manager_file))


def _upgrade_deployment_manager(inventory, ansible_overrides_file, user, ssh_password, deployment_manager_file, ctx=None):
    """
        4. Upgrade Deployment Manager.
        ~(keystone_admin)] ansible-playbook --inventory controller-0, --extra-var "@ansible-overrides.yaml" 
        --ask-pass --ask-become-pass --user sysadmin WRCP_2105/wind-river-cloud-platform-deployment-manager.yaml
    """
    ctx = ctx or wtx
    responses = [{"question": "SSH password:", "answer": ssh_password},
                 {"question": "SUDO password[defaults to SSH password]:", "answer": ssh_password},
                ]
    ansible_command = 'ansible-playbook --inventory {}, --extra-var "@{}" --ask-pass --ask-become-pass --user {} {}'
    resp = _run_ssh_command(ctx, ansible_command.format(inventory, ansible_overrides_file,
                                                        user, deployment_manager_file))


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
    image_version = re.findall('cloud-platform-deployment-manager:(.*)', img_output)[-1].replace('.', '')
    if image_version not in sw_version:
        raise NonRecoverableError  ## -> correct?
    pod_list = _run_ssh_command(ctx, pods_list.format(namespace))
    #TODO verify pod list


def _deploy_the_updated_deployment_manager_files(deployment_manager_file, deploy_overrides_file,
                                                 deployment_manager_tgz_file, ctx=None):
    """
        ~(keystone_admin)] dcmanager subcloud-deploy upload --deploy-playbook WRCP_2105/wind-river-clou
        d-platform-deployment-manager.yaml --deploy-overrides wind-river-cloud-platform-deployment-mana
        ger-overrides.yaml --deploy-chart WRCP_2105/wind-river-cloud-platform-deployment-manager-2.0.6.
        tgz
        +------------------+------------------------------------------------------------------+
        | Field | Value |
        +------------------+------------------------------------------------------------------+
        | deploy_playbook | WRCP_2105/wind-river-cloud-platform-deployment-manager.yaml |
        | deploy_overrides_file | wind-river-cloud-platform-deployment-manager-overrides.yaml |
        | deploy_chart | WRCP_2105/wind-river-cloud-platform-deployment-manager-2.0.6.tgz |
        +------------------+------------------------------------------------------------------+
    """
    command = "dcmanager subcloud-deploy upload --deploy-playbook {} --deploy-overrides {} --deploy-chart {}"
    _run_ssh_command(ctx, command.format(deployment_manager_file,  deploy_overrides_file, deployment_manager_tgz_file))


def _upgrade_the_system_controller(sw_version, deployment_manager_file, ansible_overrides_file, sysadmin_password, helm_chart_path,
                                   deployment_manager_tgz_file_patch, registry, manager_repo, rbac_proxy_image, ctx):
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

    create_ansible_overrides_file_command = """cat << EOF > {}
ansible_become_pass: {}
deployment_manager_overrides: {}
deployment_manager_chart: {}
EOF""".format(ansible_overrides_file, sysadmin_password, helm_chart_path, deployment_manager_tgz_file_patch)
    #
    helm_chart_cmd = """cat << EOF > {}
manager:
  image:
    repository: {}{}
    tag: {}
    pullPolicy: IfNotPresent
rbacProxy:
  image: {}{}
EOF""".format(helm_chart_path, registry, manager_repo, sw_version, registry, rbac_proxy_image)
    ansible_command = 'ansible-playbook {} -e @{}'.format(deployment_manager_file, ansible_overrides_file)
    _run_ssh_command(ctx, create_ansible_overrides_file_command)
    _run_ssh_command(ctx, helm_chart_cmd)
    _run_ssh_command(ctx, ansible_command)
    

def _upgrading_the_subcloud(ctx, deployment_manager_file, deployment_manager_tgz_file, helm_chart_path, new_subcloud_password=None):
    """
    1. For each subcloud, use the following command.
    ~(keystone_admin)] dcmanager subcloud-deploy upload --deploy-playbook /home/sysadmin/wind-river
    -cloud-platform-deployment-manager.yaml --deploy-chart /home/sysadmin/wind-river-cloud-platform
    -deployment-manager-2.0.6.tgz --deploy-overrides /home/sysadmin/helm-chart-overrides.yaml
    Where helm-chart-overrides.yaml contains the following:
    manager:
    image:
    repository: registry.local:9001/docker.io/wind-river/cloud-platform-deployment-manager
    tag: WRCP_21.05
    pullPolicy: IfNotPresent
    rbacProxy:
    image: registry.local:9001/gcr.io/kubebuilder/kube-rbac-proxy:v0.4.0
    2. To configure the password for the subcloud, use the following command.
    ~(keystone_admin)] dcmanager subcloud reconfig --sysadmin-password <password> --deploy-config d
    eployment-config.yaml <subcloud>
    Where subcloud is the name of the subcloud.
    Where deployment-config.yaml contains the following:
    ---
    apiVersion: v1
    5| Documentation Upgrade Deployment Manager
    Wind River Cloud Platform Updates and Upgrades 21.05 Patch 7
    kind: Namespace
    metadata:
    name: deployment
    ---
    """
    # helm-chart-overrides.yaml is configured in previous step
    subcloud_update_command = 'dcmanager subcloud-deploy upload --deploy-playbook {} --deploy-chart {}' \
                              ' --deploy-overrides {}'.format(deployment_manager_file,
                                                              deployment_manager_tgz_file,
                                                              helm_chart_path)
    _run_ssh_command(ctx, subcloud_update_command)
    if new_subcloud_password:
        deployment_config = '/home/sysadmin/deployment-config.yaml'
        subcloud_password_update_command = 'dcmanager subcloud reconfig --sysadmin-password {} --deploy-config {} {}'
        deployment_config_cmd = """cat << EOF > {}
---
apiVersion: v1
kind: Namespace
metadata:
 name: deployment
---EOF""".format(deployment_config)
        _run_ssh_command(ctx, deployment_config_cmd)
        subcloud_list = []
        for subcloud in subcloud_list:
            _run_ssh_command(ctx, subcloud_password_update_command.format(new_subcloud_password,
                                                                          deployment_config, subcloud))
