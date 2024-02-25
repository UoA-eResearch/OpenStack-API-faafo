#!/usr/local/bin/python
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
from keystoneauth1.identity import v3
from keystoneauth1 import session
import openstack.cloud

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
project_domain = config.get('Connection', 'project_domain')
project_id = config.get('Connection', 'project_id')
region_name = config.get('Connection', 'region_name')
image_id = config.get('Cloud', 'image_id')
flavor_id = config.get('Cloud', 'flavor_id')
keypair_name = config.get('Credentials', 'keypair_name')

auth = v3.Password(auth_url='https://keystone.rc.nectar.org.au:35357/v3',
                   username=auth_username,
                   password=auth_password,
                   project_name=project_name,
                   project_domain_name=project_domain,
                   user_domain_name='default',
                   )
sess = session.Session(auth=auth)
conn = openstack.connect(session=sess)

api_security_group = config.get('Names', 'api_security_group')
worker_security_group = config.get('Names', 'worker_security_group')
service_security_group = config.get('Names', 'service_security_group')
#controller_security_group = config.get('Connection', 'controller_security_group')

api_group = conn.get_security_group(api_security_group)
if api_group == None:
  api_group = conn.create_security_group(api_security_group, 'for services that run on an api node')
  conn.create_security_group_rule(api_group.id, port_range_min=22,  port_range_max=22, protocol='tcp', direction='ingress', ethertype='IPv4')
  conn.create_security_group_rule(api_group.id, port_range_min=80,  port_range_max=80, protocol='tcp', direction='ingress', ethertype='IPv4')

worker_group = conn.get_security_group(worker_security_group)
if worker_group == None:
  worker_group = conn.create_security_group(worker_security_group, 'for services that run on a worker node')
  conn.create_security_group_rule(worker_group.id, port_range_min=22,  port_range_max=22, protocol='tcp', direction='ingress', ethertype='IPv4')

services_group = conn.get_security_group(service_security_group)
if services_group == None:
  services_group = conn.create_security_group(service_security_group, 'for DB and AMPQ services only')
  conn.create_security_group_rule(services_group.id, port_range_min=22,  port_range_max=22, protocol='tcp', direction='ingress', ethertype='IPv4')
  conn.create_security_group_rule(services_group.id, port_range_min=3306,  port_range_max=3306, protocol='tcp', direction='ingress', ethertype='IPv4')
  conn.create_security_group_rule(services_group.id, port_range_min=5672,  port_range_max=5672, protocol='tcp', direction='ingress', ethertype='IPv4')

#controller_group = conn.get_security_group('control')
#if controller_group == None:
#  controller_group = conn.create_security_group('control', 'for services that run on a control node')
#  conn.create_security_group_rule(controller_group.id, port_range_min=22,  port_range_max=22, protocol='TCP', direction='Ingress', ethertype='IPv4')
#  conn.create_security_group_rule(controller_group.id, port_range_min=80,  port_range_max=80, protocol='TCP', direction='Ingress', ethertype='IPv4')
#  conn.create_security_group_rule(controller_group.id, port_range_min=5672,  port_range_max=5672, protocol='TCP', direction='Ingress', ethertype='IPv4')

app_services = config.get('Names', 'app_services')
app_api_1 = config.get('Names', 'app_api_1')
app_api_2 = config.get('Names', 'app_api_2')
worker_1 = config.get('Names', 'worker_1')
worker_2 = config.get('Names', 'worker_2')
worker_3 = config.get('Names', 'worker_3')

def launch(server_name, security_group, userdata):
  print "Launching", server_name
  instance_services = conn.create_server( server_name, image=image_id, flavor=flavor_id, key_name=keypair_name, userdata=userdata, wait=True, auto_ip=True, timeout=300, security_groups=[security_group.name])
  #conn.add_server_security_groups(server=instance_services, security_groups=[security_group.name])
  services_ip = instance_services.public_v4
  print('Instance services will be available for ssh at: //{}'.format(services_ip))
  return services_ip

# launch app services instance (database and messaging)
app_services_userdata = '''#!/usr/bin/env bash
curl -L -s https://raw.githubusercontent.com/MartinPaulo/son_of_faafo/master/contrib/install.sh | bash -s -- \
    -i database -i messaging
'''

services_ip = launch(app_services, services_group, app_services_userdata)

# launch the two api instances
api_userdata = '''#!/usr/bin/env bash
curl -L -s https://raw.githubusercontent.com/MartinPaulo/son_of_faafo/master/contrib/install.sh | bash -s -- \
    -i faafo -r api -m 'amqp://guest:guest@%(services_ip)s:5672/' \
    -d 'mysql+pymysql://faafo:password@%(services_ip)s:3306/faafo'
''' % {'services_ip': services_ip}

api_1_ip = launch(app_api_1, api_group, api_userdata)
api_2_ip = launch(app_api_2, api_group, api_userdata)


# launch the three worker instances
worker_user_data = '''#!/usr/bin/env bash
curl -L -s https://raw.githubusercontent.com/MartinPaulo/son_of_faafo/master/contrib/install.sh | bash -s -- \
    -i faafo -r worker -e 'http://%(api_1_ip)s' -m 'amqp://guest:guest@%(services_ip)s:5672/'
''' % {'api_1_ip': api_1_ip, 'services_ip': services_ip}

worker_1_ip = launch(worker_1, worker_group, worker_user_data)
worker_2_ip = launch(worker_2, worker_group, worker_user_data)
worker_3_ip = launch(worker_3, worker_group, worker_user_data)
