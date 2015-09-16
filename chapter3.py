# Chapter 3's script (titled "Scaling out", at http://developer.openstack.org/firstapp-libcloud/scaling_out.html ),
# but with extra changes added.
#       I put the configuration into a config file, so that I can share it amongst files, and not accidentally
#           check it into source control.
#       I have modified the network routines to deal with NeCTAR's use of private IP's
#       I have removed more of the boiler plate code that just prints stuff out
#       I have moved the code that creates a security group into a method
#       I have moved the network code that attaches an IP number into a method
#       I have moved the code that launches an instance into a method
#       Added a work around that solves the problem of instances not having their private IP properly populated
#           before it is accessed.
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

try:
    import configparser
except ImportError:
    import ConfigParser

config = ConfigParser.ConfigParser({'keypair_name': 'demokey', 'pub_key_file': '~/.ssh/id_rsa.pub'})
config.read('faafo.cfg')

auth_username = config.get('Connection', 'auth_username')
auth_password = config.get('Connection', 'auth_password')
auth_url = config.get('Connection', 'auth_url')
project_name = config.get('Connection', 'project_name')
region_name = config.get('Connection', 'region_name')

provider = get_driver(Provider.OPENSTACK)
conn = provider(auth_username,
                auth_password,
                ex_tenant_name=project_name,
                ex_force_auth_url=auth_url,
                ex_force_service_name='Compute Service',
                ex_force_auth_version='2.0_password',
                ex_force_service_region=region_name)

image_id = config.get('Cloud', 'image_id')
image = conn.get_image(image_id)
print(image)

flavor_id = config.get('Cloud', 'flavor_id')
flavor = conn.ex_get_size(flavor_id)
print(flavor)

print('Checking for existing SSH key pair...')
keypair_name = config.get('Credentials', 'keypair_name')
pub_key_file = config.get('Credentials', 'pub_key_file')
keypair_exists = False
for keypair in conn.list_key_pairs():
    if keypair.name == keypair_name:
        keypair_exists = True

if keypair_exists:
    print('Keypair {} already exists. Skipping import'.format(keypair_name))
else:
    print('adding keypair...')
    conn.import_key_pair_from_file(keypair_name, pub_key_file)


def create_security_group(security_group_name, security_group_description, rules):
    print('Checking for existing security group...')
    security_group_exists = False
    for security_group in conn.ex_list_security_groups():
        if security_group.name == security_group_name:
            result = security_group
            security_group_exists = True
    if security_group_exists:
        print('Security Group {} already exists. Skipping creation'.format(result.name))
    else:
        print('Creating security group {}'.format(security_group_name))
        result = conn.ex_create_security_group(security_group_name, security_group_description)
        for rule in rules:
            conn.ex_create_security_group_rule(result, **rule)
    return result


api_group = create_security_group('api', 'for services that run on an api node',
                                  ({'ip_protocol': 'TCP', 'from_port': 80, 'to_port': 80},
                                   {'ip_protocol': 'TCP', 'from_port': 22, 'to_port': 22}))

worker_group = create_security_group('worker', 'for services that run on a worker node',
                                     ({'ip_protocol': 'TCP', 'from_port': 22, 'to_port': 22},))

controller_group = create_security_group('control', 'for services that run on a control node',
                                         ({'ip_protocol': 'TCP', 'from_port': 22, 'to_port': 22},
                                          {'ip_protocol': 'TCP', 'from_port': 80, 'to_port': 80},
                                          {'ip_protocol': 'TCP', 'from_port': 5672, 'to_port': 5672,
                                           'source_security_group': worker_group}))

services_group = create_security_group('services', 'for DB and AMPQ services only',
                                       ({'ip_protocol': 'TCP', 'from_port': 22, 'to_port': 22},
                                        {'ip_protocol': 'TCP', 'from_port': 3306, 'to_port': 3306,
                                         'source_security_group': 'api_group'},
                                        {'ip_protocol': 'TCP', 'from_port': 5672, 'to_port': 5672,
                                         'source_security_group': worker_group},
                                        {'ip_protocol': 'TCP', 'from_port': 5672, 'to_port': 5672,
                                         'source_security_group': api_group}))


def launch_instance(instance_name, userdata, security_group):
    result = conn.create_node(name=instance_name,
                              image=image,
                              size=flavor,
                              ex_keyname=keypair_name,
                              ex_userdata=userdata,
                              # ex_availability_zone='NCI',
                              ex_security_groups=[security_group])
    print('Launching {}'.format(instance_name))
    conn.wait_until_running([result])
    # fix for bug where by the result isn't immediately updated with the instance IP data
    for instance in conn.list_nodes():
        if instance.id == result.id:
            result = instance
    print(result)
    return result


def attach_ip_number(target_instance):
    if len(target_instance.private_ips) > 0:
        result = target_instance.private_ips[0]
        print('Private IP is: {}'.format(result))
    # But prefer the public one, if there is one.
    if len(target_instance.public_ips) > 0:
        result = target_instance.public_ips[0]
        print('Instance {} already has a Public IP. Skipping attachment'.format(target_instance.name))
    else:
        print('Checking for unused Floating IP...')
        unused_floating_ip = None
        # find the first unassigned floating ip
        for floating_ip in conn.ex_list_floating_ips():
            if not floating_ip.node_id:
                unused_floating_ip = floating_ip
                break
        # no unassigned floating IP's so we need to create one
        if not unused_floating_ip:
            try:
                pool = conn.ex_list_floating_ip_pools()[0]
                print('Allocating new Floating IP from pool: {}'.format(pool))
                unused_floating_ip = pool.create_floating_ip()
            except IndexError:
                print('There are no Floating IP\'s found')
        if unused_floating_ip:
            conn.ex_attach_floating_ip_to_node(target_instance, unused_floating_ip)
            result = unused_floating_ip.ip_address
    return result


# launch app services instance (database and messaging)
app_services_userdata = '''#!/usr/bin/env bash
curl -L -s http://git.openstack.org/cgit/stackforge/faafo/plain/contrib/install.sh | bash -s -- \
    -i database -i messaging
'''

instance_services = launch_instance('app-services', app_services_userdata, services_group)
services_ip = attach_ip_number(instance_services)
print('Instance services will be available for ssh at: //{}'.format(services_ip))

# launch the two api instances
api_userdata = '''#!/usr/bin/env bash
curl -L -s http://git.openstack.org/cgit/stackforge/faafo/plain/contrib/install.sh | bash -s -- \
    -i faafo -r api -m 'amqp://guest:guest@%(services_ip)s:5672/' \
    -d 'mysql://faafo:password@%(services_ip)s:3306/faafo'
''' % {'services_ip': services_ip}

instance_api_1 = launch_instance('app-api-1', api_userdata, api_group)
api_1_ip = attach_ip_number(instance_api_1)
print('Instance api_1 will be deployed to http://{}'.format(api_1_ip))

instance_api_2 = launch_instance('app-api-2', api_userdata, api_group)
api_2_ip = attach_ip_number(instance_api_2)
print('Instance api_2 will be deployed to http:{}'.format(api_2_ip))

# launch the three worker instances
worker_user_data = '''#!/usr/bin/env bash
curl -L -s http://git.openstack.org/cgit/stackforge/faafo/plain/contrib/install.sh | bash -s -- \
    -i faafo -r worker -e 'http://%(api_1_ip)s' -m 'amqp://guest:guest@%(services_ip)s:5672/'
''' % {'api_1_ip': api_1_ip, 'services_ip': services_ip}

instance_worker_1 = launch_instance('worker-1', worker_user_data, worker_group)
worker_1_ip = attach_ip_number(instance_worker_1)
print('Instance worker_1_ip will be available for ssh at: {}'.format(worker_1_ip))

instance_worker_2 = launch_instance('worker-2', worker_user_data, worker_group)
worker_2_ip = attach_ip_number(instance_worker_2)
print('Instance worker_2_ip will be available for ssh at: {}'.format(worker_2_ip))

instance_worker_3 = launch_instance('worker-3', worker_user_data, worker_group)
worker_3_ip = attach_ip_number(instance_worker_3)
print('Instance worker_3_ip will be available for ssh at: {}'.format(worker_3_ip))
