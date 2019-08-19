from typing import Dict, List, Optional
import os
import logging
import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger('boto3').propagate = False
logging.getLogger('botocore').propagate = False
logging.getLogger('urllib3').propagate = False

DRY_RUN = True
TABLE_CATEGORY = os.getenv('TABLE_CATEGORY', 'AWS Security Auditing Service')
TABLE_INDEX_NAME = os.getenv('TABLE_INDEX_NAME', 'category')
TABLE_ATTRIBUTE_NAME = os.getenv(
    'TABLE_ATTRIBUTE_NAME', 'SecurityAuditIAMRoleArn'
)
TABLE_PRIMARY_PARTITION_KEY_NAME = 'aws-account-id'
TABLE_PRIMARY_SORT_KEY_NAME = 'id'
TABLE_NAME = os.getenv('TABLE_NAME', 'cloudformation-stack-emissions')
TABLE_REGION = os.getenv('TABLE_REGION', 'us-west-2')

SimpleDict = Dict[str, str]
DictOfLists = Dict[str, list]


def get_paginated_results(
    product: str,
    action: str,
    key: str,
    client_args: Optional[SimpleDict] = None,
    action_args: Optional[SimpleDict] = None,
) -> list:
    action_args = {} if action_args is None else action_args
    client_args = {} if client_args is None else client_args
    return [
        response_element
        for sublist in [
            api_response[key]
            for api_response in boto3.client(product, **client_args)
            .get_paginator(action)
            .paginate(**action_args)
        ]
        for response_element in sublist
    ]


def get_security_audit_role_arns() -> List[str]:
    dynamodb = boto3.resource('dynamodb', region_name=TABLE_REGION)
    table = dynamodb.Table(TABLE_NAME)
    items = table.query(
        IndexName=TABLE_INDEX_NAME,
        Select='SPECIFIC_ATTRIBUTES',
        ProjectionExpression=TABLE_ATTRIBUTE_NAME,
        KeyConditionExpression=Key(TABLE_INDEX_NAME).eq(TABLE_CATEGORY)
    )['Items']
    return [x[TABLE_ATTRIBUTE_NAME] for x in items if TABLE_ATTRIBUTE_NAME in x]


def get_failed_role_assumptions(security_audit_role_arns):
    aws_accounts_to_remove_from_table = []
    for assumed_role_arn in security_audit_role_arns:
        aws_account_id = assumed_role_arn.split(':')[4]
        client_sts = boto3.client('sts')
        logger.debug('Testing role assumption of {}'.format(assumed_role_arn))
        try:
            client_sts.assume_role(
                RoleArn=assumed_role_arn,
                RoleSessionName='Security-Audit-Role-Tester',
            )
        except client_sts.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                logger.error(
                    'AWS Account {} IAM role {} is not assumable : {}'.format(
                        aws_account_id, assumed_role_arn, e
                    )
                )
            aws_accounts_to_remove_from_table.append(aws_account_id)
            continue
    return aws_accounts_to_remove_from_table


def delete_table_records(aws_accounts_to_remove_from_table):
    client = boto3.client('dynamodb')
    dynamodb = boto3.resource('dynamodb', region_name=TABLE_REGION)
    table = dynamodb.Table(TABLE_NAME)
    for aws_account_id in aws_accounts_to_remove_from_table:
        items = table.query(
            KeyConditionExpression=Key(TABLE_PRIMARY_PARTITION_KEY_NAME).eq(
                aws_account_id)
        )['Items']
        for item in items:
            if not DRY_RUN:
                result = client.batch_write_item(
                    RequestItems={TABLE_NAME: [{'DeleteRequest': {'Key': {TABLE_PRIMARY_PARTITION_KEY_NAME: {'S': item[TABLE_PRIMARY_PARTITION_KEY_NAME]}, TABLE_PRIMARY_SORT_KEY_NAME: {'S': item[TABLE_PRIMARY_SORT_KEY_NAME]}}}}]})
                logger.info('Deleted {} {}'.format(
                        item[TABLE_PRIMARY_PARTITION_KEY_NAME],
                        item[TABLE_PRIMARY_SORT_KEY_NAME]))
                if len(result['UnprocessedItems']) > 0:
                    logger.info(
                        'Unprocessed items : {}'.format([(k, v) for k, v in result['UnprocessedItems'][TABLE_NAME]['DeleteRequest']['Key'].items()]))
            else:
                logger.info(
                    'Would have deleted {} {}'.format(
                        item[TABLE_PRIMARY_PARTITION_KEY_NAME],
                        item[TABLE_PRIMARY_SORT_KEY_NAME],
                    )
                )


def lambda_handler(event, context):
    security_audit_role_arns = get_security_audit_role_arns()
    logger.info(
        'IAM Role ARNs fetched from table : {}'.format(
            security_audit_role_arns
        )
    )
    aws_accounts_to_remove_from_table = get_failed_role_assumptions(security_audit_role_arns)
    logger.info(
        'AWS Accounts to remove from table : {}'.format(
            aws_accounts_to_remove_from_table
        )
    )
    delete_table_records(aws_accounts_to_remove_from_table)
