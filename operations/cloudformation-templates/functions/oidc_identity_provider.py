import json
import boto3
from botocore.vendored import requests
from botocore.exceptions import ClientError

iam = boto3.client("iam")


def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
  print(event['ResponseURL'])
  responseBody = {
    'Status': 'SUCCESS' if responseStatus else 'FAILED',
    'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
    'PhysicalResourceId': physicalResourceId or context.log_stream_name,
    'StackId': event['StackId'], 'RequestId': event['RequestId'],
    'LogicalResourceId': event['LogicalResourceId'], 'NoEcho': noEcho, 'Data': responseData
  }
  json_responseBody = json.dumps(responseBody)
  print("Response body:\n" + json_responseBody)
  headers = {'content-type' : '', 'content-length': str(len(json_responseBody))}
  try:
    response = requests.put(event['ResponseURL'], data=json_responseBody, headers=headers)
    print("Status code: " + response.reason)
  except Exception as e:
    print("send(..) failed executing requests.put(..): " + str(e))


def create_provider(url, client_id_list, thumbprint_list):
  try:
    response = iam.create_open_id_connect_provider(Url=url, ClientIDList=client_id_list, ThumbprintList=thumbprint_list)
    return True, response['OpenIDConnectProviderArn']
  except Exception as e:
    return False, "Cannot create OIDC provider: " + str(e)


def delete_provider(arn):
  try:
    iam.delete_open_id_connect_provider(OpenIDConnectProviderArn=arn)
    return True, "OIDC provider with ARN " + arn + " deleted"
  except ClientError as e:
    if e.response['Error']['Code'] == "NoSuchEntity":
      return True, "OIDC provider with ARN {} does not exist, deletion succeeded".format(arn)
    else:
      return False, "Cannot delete OIDC provider with ARN {} : {}".format(arn, str(e))
  except Exception as e:
    return False, "Cannot delete OIDC provider with ARN " + arn + ": " + str(e)


def update_provider(arn, client_id_list, thumbprint_list):
  try:
    response = iam.get_open_id_connect_provider(OpenIDConnectProviderArn=arn)
    deleted_client_ids = set(response['ClientIDList']) - set(client_id_list)
    added_client_ids = set(client_id_list) - set(response['ClientIDList'])
    if set(thumbprint_list) ^ set(response['ThumbprintList']):
      iam.update_open_id_connect_provider_thumbprint(OpenIDConnectProviderArn=arn, ThumbprintList=thumbprint_list)
    for client_id in added_client_ids:
      iam.add_client_id_to_open_id_connect_provider(OpenIDConnectProviderArn=arn, ClientID=client_id)
    for client_id in deleted_client_ids:
      iam.remove_client_id_from_open_id_connect_provider(OpenIDConnectProviderArn=arn, ClientID=client_id)
    return True, "OIDC provider " + arn + " updated"
  except Exception as e:
    return False, "Cannot update OIDC provider " + arn + ": " + str(e)


def lambda_handler(event, context):
  url = event['ResourceProperties']['Url']
  def split_list(k):
    return [x.strip() for x in event['ResourceProperties'].get(k, '').split(',')]
  client_id_list = split_list('ClientIDList')
  thumbprint_list = split_list('ThumbprintList')

  arn_format = "arn:aws:iam::${AWS::AccountId}:oidc-provider/{}"
  arn = arn_format.format(url[8:])
  if event['RequestType'] == 'Create':
    result, arn = create_provider(url, client_id_list, thumbprint_list)
    reason = "Creation succeeded"
  elif event['RequestType'] == 'Update':
    if event['OldResourceProperties']['Url'] != url:
        result, reason = delete_provider(arn)
        if result:
          result, reason_create = create_provider(url, client_id_list, thumbprint_list)
          if result:
            reason = ' '.join([reason, reason_create])
    else:
      result, reason = update_provider(arn, client_id_list, thumbprint_list)
  elif event['RequestType'] == 'Delete':
    result, reason = delete_provider(arn)
  else:
    result, reason = False, "Unknown operation: " + event['RequestType']
  send(event, context, result, {'Reason': reason, 'event': event}, arn)
