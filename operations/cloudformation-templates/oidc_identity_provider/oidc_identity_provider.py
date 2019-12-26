import boto3
from crhelper import CfnResource
from botocore.exceptions import ClientError

helper = CfnResource(
    json_logging=False, log_level='INFO', boto_level='CRITICAL')

try:
    iam = boto3.client("iam")
    ARN_FORMAT = "arn:aws:iam::{}:oidc-provider/{}"
except Exception as e:
    helper.init_failure(e)


def get_comma_delimited_list(event, parameter):
    value = event['ResourceProperties'].get(parameter)
    return [x.strip() for x in value.split(',')] if value else []


def get_parameters(event):
    aws_account_id = event['StackId'].split(':')[4]
    url = event['ResourceProperties']['Url']
    client_id_list = get_comma_delimited_list(event, 'ClientIDList')
    thumbprint_list = get_comma_delimited_list(event, 'ThumbprintList')
    return aws_account_id, url, client_id_list, thumbprint_list


def update_provider(url, aws_account_id, client_id_list, thumbprint_list):
    arn = ARN_FORMAT.format(aws_account_id, url[8:])
    try:
        response = iam.get_open_id_connect_provider(
            OpenIDConnectProviderArn=arn)
    except ClientError as e:
        if e.response['Error']['Code'] == "NoSuchEntity":
            response_create = iam.create_open_id_connect_provider(
                Url=url,
                ClientIDList=client_id_list,
                ThumbprintList=thumbprint_list)
            return response_create['OpenIDConnectProviderArn']
        else:
            raise
    deleted_client_ids = set(response['ClientIDList']) - set(
        client_id_list)
    added_client_ids = set(client_id_list) - set(
        response['ClientIDList'])
    if set(thumbprint_list) ^ set(response['ThumbprintList']):
        iam.update_open_id_connect_provider_thumbprint(
            OpenIDConnectProviderArn=arn,
            ThumbprintList=thumbprint_list)
    for client_id in added_client_ids:
        iam.add_client_id_to_open_id_connect_provider(
            OpenIDConnectProviderArn=arn, ClientID=client_id)
    for client_id in deleted_client_ids:
        iam.remove_client_id_from_open_id_connect_provider(
            OpenIDConnectProviderArn=arn, ClientID=client_id)
    return arn


def create_provider(aws_account_id, url, client_id_list, thumbprint_list):
    try:
        response = iam.create_open_id_connect_provider(
            Url=url,
            ClientIDList=client_id_list,
            ThumbprintList=thumbprint_list)
        return response['OpenIDConnectProviderArn']
    except ClientError as e:
        if e.response['Error']['Code'] == "EntityAlreadyExists":
            arn = ARN_FORMAT.format(aws_account_id, url[8:])
            return update_provider(url, aws_account_id, client_id_list, thumbprint_list)


@helper.create
def create(event, context):
    return create_provider(*get_parameters(event))


@helper.update
def update(event, context):
    aws_account_id, url, client_id_list, thumbprint_list = get_parameters(
        event)
    if (event['OldResourceProperties']['Url'] !=
            event['ResourceProperties']['Url']):
        arn = ARN_FORMAT.format(
            aws_account_id, event['OldResourceProperties']['Url'][8:])
        iam.delete_open_id_connect_provider(OpenIDConnectProviderArn=arn)
        return create_provider(
            aws_account_id, url, client_id_list, thumbprint_list)
    else:
        arn = ARN_FORMAT.format(
            aws_account_id, event['ResourceProperties']['Url'][8:])
        update_provider(url, aws_account_id, client_id_list, thumbprint_list)


@helper.delete
def delete(event, context):
    aws_account_id, _, _, _ = get_parameters(event)
    arn = ARN_FORMAT.format(
        aws_account_id, event['ResourceProperties']['Url'][8:])
    iam.delete_open_id_connect_provider(OpenIDConnectProviderArn=arn)


def lambda_handler(event, context):
    helper(event, context)
