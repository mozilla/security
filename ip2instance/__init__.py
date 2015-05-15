#!/usr/bin/env python

import boto.ec2
import boto.sts
import logging
import datetime
import yaml
import os
import os.path
#import re

#logging.basicConfig(level=logging.DEBUG)

# rfc1918 = re.compile("^(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3})$")

def get_config():
    config = {'rich_line_format': '# "{account}", "{region}", "{date}", "{name}", "{instance_type}", "{id}", "{account alias}", "{tags}"\n{ip_address}',
              'role_session_name': 'OpSecSecurityAudit',
              'roles': []}
    CONFIG_FILENAME = "/etc/ip2instance.yaml"
    if os.path.isfile(CONFIG_FILENAME) and os.access(CONFIG_FILENAME, os.R_OK):
        with open(CONFIG_FILENAME, 'r') as f:
            config.update(yaml.load(f))
    return config

def get_instances(config, ip_address=None):
    returned_instances=[]
    # This constrains the permission that this tool requests to a subset of what 
    # the assumed role could provide
    policy = '''{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Action": [
            "ec2:Describe*",
            "iam:ListAccountAliases"
          ],
          "Effect": "Allow",
          "Resource": "*"
        }
      ]
    }'''
    
    # Skip regions that require special access to use
    # https://github.com/boto/boto/issues/1951
    special_access_regions=["cn-north-1",
                            "us-gov-west-1"]
    
    regions = boto.ec2.regions()
    date = datetime.datetime.now().isoformat()
    
    logging.debug("Connecting to sts")
    try:
        conn_sts = boto.sts.connect_to_region('us-east-1')
    except Exception, e:
        logging.error("Unable to connect to sts with exception %s" % e)
    
    assumed_roles = {}
    for role_arn in config['roles']:
        assumed_roles[role_arn] = {}
        try:
            assumed_roles[role_arn]['credentials'] = conn_sts.assume_role(role_arn=role_arn,
                                                        role_session_name=config['role_session_name'],
                                                        policy=policy)
        except Exception, e:
            logging.error("Unable to assume role %s due to exception %s" % (role_arn, e))
            continue
        try:
            credentials = assumed_roles[role_arn]['credentials']
            assumed_roles[role_arn]['conn_iam'] = boto.connect_iam(
                aws_access_key_id=credentials.credentials.access_key,
                aws_secret_access_key=credentials.credentials.secret_key,
                security_token=credentials.credentials.session_token)
        except Exception, e:
            logging.error("Unable to connect to iam with role %s due to exception %s" % (role_arn, e))
        try:
            aliases = assumed_roles[role_arn]['conn_iam'].get_account_alias()['list_account_aliases_response']['list_account_aliases_result']['account_aliases']
            assumed_roles[role_arn]['alias'] = ', '.join(aliases) if len(aliases) > 0 else ''
        except Exception, e:
            logging.error("Unable to get account alias with role %s due to exception %s" % (role_arn, e))
    
    for region in [x for x in regions if x.name not in special_access_regions]:
        for role_arn in config['roles']:
            try:
                credentials = assumed_roles[role_arn]['credentials']
                conn_ec2 = boto.connect_ec2(
                    aws_access_key_id=credentials.credentials.access_key,
                    aws_secret_access_key=credentials.credentials.secret_key,
                    security_token=credentials.credentials.session_token,
                    region=region)
            except Exception, e:
                logging.error("Unable to connect to aws with role %s in region %s with exception %s" % (role_arn, region, e))
                continue
    
            instances = conn_ec2.get_only_instances()
            for instance in [x for x in instances if x.state == "running"]:
                if instance.ip_address is not None:
                    instance.extra_fields = {
                        'role': role_arn,
                        'date': date,
                        'account': role_arn.split(':')[4],
                        'region': region.name,
                        'account alias': assumed_roles[role_arn]['alias'],
                        'name': instance.tags['Name'] if 'Name' in instance.tags else ""}
                    if ip_address is not None and instance.ip_address == ip_address:
                        # short circuit as soon as we find the IP and return it
                        return instance
                    else:
                        returned_instances.append(instance)
    return returned_instances

def print_ip_list(config, instances):
    for instance in instances:
        print instance.ip_address

def print_rich_ip_list(config, instances):
    for instance in instances:
        extra_fields = instance.extra_fields
        print config['rich_line_format'].format(**dict(instance.__dict__.items() + 
                                                  extra_fields.items()))

def main():
    config = get_config()
    instances = get_instances(config)
    print_rich_ip_list(config, instances)

if __name__ == "__main__":
    main()