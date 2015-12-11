import boto3
from cfnlambda import handler_decorator
import logging

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)


@handler_decorator()
def publish_to_sns(event, context):
    """Publish messages to an SNS topic

    CloudFormation custom resource property inputs :
        Message : The message to publish.
        TopicArn : The SNS Topic to publish the message to.

    CloudFormation custom resource attribute outputs :
        result : String describing the result of the action.
    """

    for required_property in ['TopicArn', 'Message']:
        if required_property not in event['ResourceProperties']:
            raise ValueError('%s argument not present in ResourceProperties'
                             % required_property)

    arguments = {x: event['ResourceProperties'][x]
                 for x
                 in event['ResourceProperties'].keys()
                 if x != 'ServiceToken'}

    if type(arguments['Message']) == dict:
        arguments['MessageStructure'] = 'json'

    client = boto3.client('sns')
    if event['RequestType'] != 'Delete':
        result = client.publish(**arguments)['MessageId']
    else:
        result = 'Stack is being deleted'
    return result
