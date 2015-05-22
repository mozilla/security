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

DEFAULT_ROLE_SESSION_NAME = 'ip2instanceRoleSessionName'


def get_config():
    config = {'rich_line_format': '# "{account}", "{region}", '
              '"{date_fetched}", "{name}", "{instance_type}", '
              '"{id}", "{account_alias}", "{tags}"\n{ip_address}',
              'role_session_name': DEFAULT_ROLE_SESSION_NAME,
              'roles': [],
              'policy': '''{
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
}'''}
    CONFIG_FILENAME = "/etc/ip2instance.yaml"
    if os.path.isfile(CONFIG_FILENAME) and os.access(CONFIG_FILENAME, os.R_OK):
        with open(CONFIG_FILENAME, 'r') as f:
            config.update(yaml.load(f))
    return config


def get_safe_regions():
    # Skip regions that require special access to use
    # https://github.com/boto/boto/issues/1951
    special_access_regions = ["cn-north-1",
                              "us-gov-west-1"]
    return [x for x in boto.ec2.regions()
            if x.name not in special_access_regions]


def get_all_instances(roles,
                      role_session_name=DEFAULT_ROLE_SESSION_NAME,
                      policy=None,
                      ip_address=None):
    returned_instances = []
    assumed_roles = {}

    date = datetime.datetime.now().isoformat()

    for region in get_safe_regions():
        for role_arn in roles:
            if role_arn not in assumed_roles:
                assumed_role = get_assumed_role(role_arn,
                                                role_session_name,
                                                policy)
                if assumed_role:
                    assumed_roles[role_arn] = assumed_role
                else:
                    continue
            data = {'role': role_arn,
                    'date_fetched': date,
                    'account': role_arn.split(':')[4],
                    'region': region.name,
                    'account_alias': assumed_roles[role_arn]['alias']}
            instances = get_instances(assumed_roles[role_arn]['credentials'],
                                      region,
                                      data,
                                      ip_address)
            if instances:
                returned_instances.extend(instances)
    return returned_instances


def get_assumed_role(role_arn,
                     role_session_name=DEFAULT_ROLE_SESSION_NAME,
                     policy=None):
    logging.debug("Connecting to sts")
    try:
        # This makes no call to AWS so no downside to creating it with each
        # get_assumed_role call
        conn_sts = boto.sts.connect_to_region('us-east-1')
    except Exception, e:
        logging.error("Unable to connect to sts with exception %s" % e)
        raise

    try:
        credentials = conn_sts.assume_role(
            role_arn=role_arn,
            role_session_name=role_session_name,
            policy=policy)
    except Exception, e:
        logging.error("Unable to assume role %s due to exception %s" %
                      (role_arn, e))
        return False
    try:
        conn_iam = boto.connect_iam(
            aws_access_key_id=credentials.credentials.access_key,
            aws_secret_access_key=credentials.credentials.secret_key,
            security_token=credentials.credentials.session_token)
    except Exception, e:
        logging.error("Unable to connect to iam with role %s due to "
                      "exception %s" % (role_arn, e))
        return False
    try:
        aliases = (conn_iam.get_account_alias()
                   ['list_account_aliases_response']
                   ['list_account_aliases_result']['account_aliases'])
        alias = (', '.join(aliases)
                 if len(aliases) > 0
                 else '')
    except Exception, e:
        logging.error("Unable to get account alias with role %s due to "
                      "exception %s" % (role_arn, e))
        return False
    return {'credentials': credentials,
            'alias': alias}


def get_instances(credentials, region, additional_data={}, ip_address=None):
    try:
        conn_ec2 = boto.connect_ec2(
            aws_access_key_id=credentials.credentials.access_key,
            aws_secret_access_key=credentials.credentials.secret_key,
            security_token=credentials.credentials.session_token,
            region=region)
    except Exception, e:
        logging.error("Unable to connect to aws with access_key %s in "
                      "region %s with exception %s" %
                      (credentials.credentials.access_key, region, e))
        return False

    instances = conn_ec2.get_only_instances()
    returned_instances = []
    for instance in [x for x in instances if x.state == "running"]:
        if instance.ip_address is not None:
            instance.__dict__.update(additional_data)
            instance.name = (instance.tags['Name']
                             if 'Name' in instance.tags
                             else "")
            if (ip_address is not None
                    and instance.ip_address == ip_address):
                # short circuit as soon as we find the IP and return it
                return [instance]
            else:
                returned_instances.append(instance)
    return returned_instances


def print_ip_list(instances):
    for instance in instances:
        print instance.ip_address


def print_rich_ip_list(rich_line_format, instances):
    for instance in instances:
        print rich_line_format.format(**instance.__dict__)


def main():
    config = get_config()
    instances = get_all_instances(config['roles'],
                                  config['role_session_name'],
                                  config['policy'])
    print_rich_ip_list(config['rich_line_format'], instances)

if __name__ == "__main__":
    main()