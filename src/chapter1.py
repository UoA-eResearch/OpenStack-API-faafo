# More or less a straight riff of the original documentation for chapter 1, titled
# "Getting Started". (http://developer.openstack.org/firstapp-libcloud/getting_started.html)
# There are three differences, though:
#       I put the configuration into a config file, so that I can share it amongst files, and not accidentally
#           check it into source control.
#       I have modified the network routines to deal with NeCTAR's use of private IP's
#       Added a work around that solves the problem of instances not having their private IP properly populated
#           before it is accessed.

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.common.exceptions import BaseHTTPError

try:
    import configparser
except ImportError:
    import ConfigParser

# setup defaults
config = ConfigParser.ConfigParser({'keypair_name': 'demokey', 'pub_key_file': '~/.ssh/id_rsa.pub'})
# read the config file
config.read('faafo.cfg')

# step-1
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

# step-2
images = conn.list_images()
for image in images:
    print(image)

# step-3
flavors = conn.list_sizes()
for flavor in flavors:
    print(flavor)

# step-4
image_id = config.get('Cloud', 'image_id')
image = conn.get_image(image_id)
print(image)

# step-5
flavor_id = config.get('Cloud', 'flavor_id')
flavor = conn.ex_get_size(flavor_id)
print(flavor)

# We don't want a room full of people colliding here...
# # step-6
# instance_name = 'faafo'
# testing_instance = conn.create_node(name=instance_name, image=image, size=flavor)
# print(testing_instance)
#
# # step-7
# instances = conn.list_nodes()
# for instance in instances:
#     print(instance)
#
# # step-8
# conn.destroy_node(testing_instance)

# step-9
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

for keypair in conn.list_key_pairs():
    print(keypair)

# step-10
print('Checking for existing security group...')
security_group_name = 'all-in-one'
security_group_exists = False
for security_group in conn.ex_list_security_groups():
    if security_group.name == security_group_name:
        all_in_one_security_group = security_group
        security_group_exists = True

if security_group_exists:
    print('Security Group {} already exists. Skipping creation'.format(all_in_one_security_group.name))
else:
    all_in_one_security_group = conn.ex_create_security_group(security_group_name,
                                                              'network access for all-in-one application.')
    conn.ex_create_security_group_rule(all_in_one_security_group, 'TCP', 80, 80)
    conn.ex_create_security_group_rule(all_in_one_security_group, 'TCP', 22, 22)

for security_group in conn.ex_list_security_groups():
    print(security_group)

# step-11
userdata = '''#!/usr/bin/env bash
curl -L -s https://raw.githubusercontent.com/MartinPaulo/son_of_faafo/master/contrib/install.sh | bash -s -- \
    -i faafo -i messaging -r api -r worker -r demo
'''

# step-12
print('Checking for existing instance...')
instance_name = config.get('Names', 'all-in-one')
instance_exists = False
for instance in conn.list_nodes():
    if instance.name == instance_name:
        testing_instance = instance
        instance_exists = True

if instance_exists:
    print('Instance {} already exists. Skipping creation'.format(testing_instance.name))
else:
    print('Creating new instance')
    testing_instance = conn.create_node(name=instance_name,
                                        image=image,
                                        size=flavor,
                                        ex_keyname=keypair_name,
                                        ex_userdata=userdata,
                                        ex_security_groups=[all_in_one_security_group])
    conn.wait_until_running([testing_instance])

# fix for bug where by the instance isn't immediately updated with the instance data
for instance in conn.list_nodes():
    if instance.id == testing_instance.id:
        testing_instance = instance

print (testing_instance)

ip_address = None

# Find the IP address to use
# Default to the private IP if, there is one.
if len(testing_instance.private_ips) > 0:
    ip_address = testing_instance.private_ips[0]
    print('Private IP is: {}'.format(ip_address))

# step-14
# But prefer the public one, if there is one.
if len(testing_instance.public_ips) > 0:
    ip_address = testing_instance.public_ips[0]
    print('Instance {} already has a Public IP. Skipping attachment'.format(testing_instance.name))
else:
    # step-13
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
        except (IndexError, BaseHTTPError) as e:
            print('There are no unused Floating IP\'s found! Message: {}'.format(e))
    if unused_floating_ip:
        conn.ex_attach_floating_ip_to_node(testing_instance, unused_floating_ip)
        ip_address = unused_floating_ip.ip_address

# step-15
print('The Fractals app will be deployed to http://{}'.format(ip_address))
