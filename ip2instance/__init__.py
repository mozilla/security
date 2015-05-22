#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import boto.ec2
import boto.sts
import logging
import datetime
import yaml
import os
import os.path

# logging.basicConfig(level=logging.DEBUG)


def get_config():
    config = {'rich_line_format': '# "{account}", "{region}", "{date_fetched}", '
              '"{name}", "{instance_type}", "{id}", "{account_alias}", '
              '"{tags}"\n{ip_address}',
              'role_session_name': 'ip2instanceRoleSessionName',
              'roles': []}
    CONFIG_FILENAME = "/etc/ip2instance.yaml"
    if os.path.isfile(CONFIG_FILENAME) and os.access(CONFIG_FILENAME, os.R_OK):
        with open(CONFIG_FILENAME, 'r') as f:
            config.update(yaml.load(f))
    return config


def get_instances(config, ip_address=None):
    returned_instances = []
    # This constrains the permission that this tool requests to a subset of
    # what the assumed role could provide
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
    special_access_regions = ["cn-north-1",
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
            assumed_roles[role_arn]['credentials'] = conn_sts.assume_role(
                role_arn=role_arn,
                role_session_name=config['role_session_name'],
                policy=policy)
        except Exception, e:
            logging.error("Unable to assume role %s due to exception %s" %
                          (role_arn, e))
            continue
        try:
            credentials = assumed_roles[role_arn]['credentials']
            assumed_roles[role_arn]['conn_iam'] = boto.connect_iam(
                aws_access_key_id=credentials.credentials.access_key,
                aws_secret_access_key=credentials.credentials.secret_key,
                security_token=credentials.credentials.session_token)
        except Exception, e:
            logging.error("Unable to connect to iam with role %s due to "
                          "exception %s" % (role_arn, e))
        try:
            aliases = (assumed_roles[role_arn]['conn_iam'].get_account_alias()
                       ['list_account_aliases_response']
                       ['list_account_aliases_result']['account_aliases'])
            assumed_roles[role_arn]['alias'] = (', '.join(aliases)
                                                if len(aliases) > 0
                                                else '')
        except Exception, e:
            logging.error("Unable to get account alias with role %s due to "
                          "exception %s" % (role_arn, e))

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
                logging.error("Unable to connect to aws with role %s in "
                              "region %s with exception %s" %
                              (role_arn, region, e))
                continue

            instances = conn_ec2.get_only_instances()
            for instance in [x for x in instances if x.state == "running"]:
                if instance.ip_address is not None:
                    instance.role = role_arn
                    instance.date_fetched = date,
                    instance.account = role_arn.split(':')[4]
                    instance.region = region.name
                    instance.account_alias = assumed_roles[role_arn]['alias']
                    instance.name = (instance.tags['Name']
                                     if 'Name' in instance.tags
                                     else "")
                    if (ip_address is not None
                            and instance.ip_address == ip_address):
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
        print config['rich_line_format'].format(**instance.__dict__)


def main():
    config = get_config()
    instances = get_instances(config)
    print_rich_ip_list(config, instances)

if __name__ == "__main__":
    main()