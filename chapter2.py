# Chapter 2's script (titled "Introduction to the fractals application architecture",
# at http://developer.openstack.org/firstapp-libcloud/introduction.html ), but with extra changes added.
#       I put the configuration into a config file, so that I can share it amongst files, and not accidentally
#           check it into source control.
#       I have modified the network routines to deal with NeCTAR's use of private IP's
#       I have removed more of the boiler plate code that just prints stuff out
#       I have moved the network code that attaches an IP number into a method, so that we don't have to
#           have it typed out twice.
#       Added a work around that solved the problem of instances not having their private IP properly populated
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
    print('Keypair ' + keypair_name + ' already exists. Skipping import.')
else:
    print('adding keypair...')
    conn.import_key_pair_from_file(keypair_name, pub_key_file)

print('Checking for existing security group...')
security_group_name = 'worker'
security_group_exists = False
for security_group in conn.ex_list_security_groups():
    if security_group.name == security_group_name:
        worker_group = security_group
        security_group_exists = True

if security_group_exists:
    print('Security Group ' + worker_group.name + ' already exists. Skipping creation.')
else:
    worker_group = conn.ex_create_security_group('worker', 'for services that run on a worker node')
    conn.ex_create_security_group_rule(worker_group, 'TCP', 80, 80)
    conn.ex_create_security_group_rule(worker_group, 'TCP', 22, 22)

print('Checking for existing security group...')
security_group_name = 'control'
security_group_exists = False
for security_group in conn.ex_list_security_groups():
    if security_group.name == security_group_name:
        controller_group = security_group
        security_group_exists = True

if security_group_exists:
    print('Security Group ' + controller_group.name + ' already exists. Skipping creation.')
else:
    controller_group = conn.ex_create_security_group('control', 'for services that run on a control node')
    conn.ex_create_security_group_rule(controller_group, 'TCP', 22, 22)
    conn.ex_create_security_group_rule(controller_group, 'TCP', 80, 80)
    conn.ex_create_security_group_rule(controller_group, 'TCP', 5672, 5672, source_security_group=worker_group)


# My introduced method to attach an IP number.
def attach_ip_number(target_instance):
    result = target_instance.private_ips[0]
    print('Checking for unused Floating IP...')
    unused_floating_ip = None
    for floating_ip in conn.ex_list_floating_ips():
        if floating_ip.node_id:
            unused_floating_ip = floating_ip
            break
    if not unused_floating_ip:
        try:
            pool = conn.ex_list_floating_ip_pools()[0]
            print('Allocating new Floating IP from pool: {}'.format(pool))
            unused_floating_ip = pool.create_floating_ip()
        except IndexError:
            print('There are no Floating IP\'s found')
    if len(target_instance.public_ips) > 0:
        result = target_instance.public_ips[0]
        print('Instance ' + target_instance.name + ' already has a Public ip. Skipping attachment.')
    else:
        if unused_floating_ip:
            result = unused_floating_ip.ip_address
            conn.ex_attach_floating_ip_to_node(target_instance, unused_floating_ip)
        else:
            print('Could not find a Floating IP, and there are no Public IP\'s?')
    return result


print("Building controller")

userdata = '''#!/usr/bin/env bash
curl -L -s http://git.openstack.org/cgit/stackforge/faafo/plain/contrib/install.sh | bash -s -- \
    -i messaging -i faafo -r api
'''

instance_controller_1 = conn.create_node(name='app-controller',
                                         image=image,
                                         size=flavor,
                                         ex_keyname=keypair_name,
                                         ex_userdata=userdata,
                                         ex_security_groups=[controller_group])

running = conn.wait_until_running([instance_controller_1])
for instance in conn.list_nodes():
    if instance.id == instance_controller_1.id:
        # fix for bug where by the instance isn't immediately updated with the instance data
        instance_controller_1 = instance
    print(instance)

ip_controller = attach_ip_number(instance_controller_1)
print('Instance ' + instance_controller_1.name + ' will be deployed to http://%s' % ip_controller)

print("Building worker")

userdata = '''#!/usr/bin/env bash
curl -L -s http://git.openstack.org/cgit/stackforge/faafo/plain/contrib/install.sh | bash -s -- \
    -i faafo -r worker -e 'http://%(ip_controller)s' -m 'amqp://guest:guest@%(ip_controller)s:5672/'
''' % {'ip_controller': ip_controller}

instance_worker_1 = conn.create_node(name='app-worker-1',
                                     image=image,
                                     size=flavor,
                                     ex_keyname=keypair_name,
                                     ex_userdata=userdata,
                                     ex_security_groups=[worker_group])

conn.wait_until_running([instance_worker_1], ssh_interface='private_ips')

for instance in conn.list_nodes():
    if instance.id == instance_worker_1.id:
        # fix for bug where by the instance isn't immediately updated with the instance data
        instance_worker_1 = instance
    print(instance)

ip_instance_worker_1 = attach_ip_number(instance_worker_1)
print('The worker will be available for SSH at %s' % ip_instance_worker_1)
