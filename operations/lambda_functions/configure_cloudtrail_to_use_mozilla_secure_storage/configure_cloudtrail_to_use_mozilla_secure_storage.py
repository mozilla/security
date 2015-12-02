from cfnlambda import handler_decorator, PythonObjectEncoder
import json
import boto3
from botocore.vendored import requests
import botocore.exceptions
import logging

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)

DEFAULT_SNS_REGION = 'us-east-1'
STACK_NAME = 'MozillaSecuredCloudTrail'
base_template = '''{
  "AWSTemplateFormatVersion":"2010-09-09",
  "Description":"CloudTrail for the region %(region)s which sends logs and SNS notification to the Mozilla secured CloudTrail storage account",
  "Parameters" : {
    "BucketName" : {
      "Type" : "String",
      "Description" : "The S3 Bucket name to store CloudTrail logs in"
    },
    "SNSAccountId" : {
      "Type" : "String",
      "Default" : "",
      "Description" : "The AWS Account ID of the CloudTrail secure storage account"
    },
    "SNSRegion" : {
      "Type" : "String",
      "Default" : "%(default_sns_region)s",
      "Description" : "The region that the CloudTrail secure storage account's SNS topic is in"
    }
  },
  "Conditions" : {
    "SNSAccountIdDefined" : {
       "Fn::Not" : [{
          "Fn::Equals" : [
             {"Ref" : "SNSAccountId"},
             ""
          ]
       }]
    }
  },
  "Resources":{
    "CloudTrail":{
      "Type":"AWS::CloudTrail::Trail",
      "Properties":{
        "S3BucketName": {"Ref": "BucketName"},
        "SnsTopicName": {
          "Fn::If" : [
            "SNSAccountIdDefined",
            {
              "Fn::Join":[
                "",
                [
                  "arn:aws:sns:",
                  {
                    "Ref":"SNSRegion"
                  },
                  ":",
                  {
                    "Ref":"SNSAccountId"
                  },
                  ":MozillaCloudTrailLogs",
                  {
                    "Ref":"AWS::AccountId"
                  }
                ]
              ]
            },
            {"Ref" : "AWS::NoValue"}
          ]
        },
        "IsLogging":true,
        "IncludeGlobalServiceEvents":false
      }
    }
  }
}
'''


def get_account_id(event=None):
    if event is not None and 'StackId' in event:
        return event['StackId'].split(':')[4]

    try:
        # We're running in an ec2 instance, get the account id from the
        # instance profile ARN
        return requests.get(
            'http://169.254.169.254/latest/meta-data/iam/info/',
            timeout=1).json()['InstanceProfileArn'].split(':')[4]
    except:
        pass

    try:
        # We're not on an ec2 instance but have api keys, get the account
        # id from the user ARN
        return boto3.client('iam').get_user()['User']['Arn'].split(':')[4]
    except:
        pass

    return False


def get_regions():
    return [x['RegionName'] for x
            in boto3.client('ec2').describe_regions()['Regions']]


def stack_present(StackName, region):
    client_cloudformation = boto3.client('cloudformation',
                                         region_name=region)
    try:
        return client_cloudformation.describe_stacks(
            StackName=StackName)['Stacks'][0]
    except botocore.exceptions.ClientError as e:
        if 'ValidationError' in e.message:
            logger.debug('There is no stack %s in %s.' %
                         (STACK_NAME, region))
            return False
        else:
            raise


def delete_stacks(dryrun=False):
    for region in get_regions():
        client_cloudformation = boto3.client('cloudformation',
                                             region_name=region)
        if not stack_present(STACK_NAME, region):
            continue
        if not dryrun:
            logger.debug('Deleting stack %s in %s.' %
                         (STACK_NAME, region))
            client_cloudformation.delete_stack(StackName=STACK_NAME)
            logger.info('Dryrun preventing deletion of CloudFormations stack '
                        'in region %s' % region)


def deploy_stacks(bucketname,
                  snsregion,
                  snsaccountid,
                  accountid,
                  dryrun=False):
    logger.debug('%s' % {'bucketname': bucketname,
                         'snsregion': snsregion,
                         'snsaccountid': snsaccountid,
                         'dryrun': dryrun})

    output = {'Account ID': accountid,
              'Existing CloudTrails': {},
              'New CloudTrails': {},
              'Existing CloudFormation Stacks': {}}

    # Iterate over each region, loading the CloudFormation template in each
    # to configure CloudTrail
    # Note : Default Centos 7 boto (version 2.25.0 only lists 2 regions
    # supported)

    # The assumption is that ec2 regions will be equal to or greater than
    # CloudTrail regions (as there is no way to determine all supported
    # CloudTrail regions).
    logger.debug('Preparing to iterate over regions %s' % get_regions())
    for region in get_regions():
        client_cloudtrail = boto3.client('cloudtrail', region_name=region)
        try:
            current_cloudtrails = client_cloudtrail.describe_trails()[
                'trailList']
        except botocore.exceptions.EndpointConnectionError:
            # This is an AWS region that doesn't support CloudTrail
            continue

        # Load the base template
        cloudformation = json.loads(base_template %
                                    {'region': region,
                                     'default_sns_region': DEFAULT_SNS_REGION})

        # Send all global (non region specific) CloudTrail log lines
        # (e.g. IAM calls) to us-east-1
        if region == 'us-east-1':
            cloudformation['Resources']['CloudTrail'][
                'Properties']['IncludeGlobalServiceEvents'] = True

        cloudformation_template = json.dumps(cloudformation,
                                             sort_keys=True,
                                             indent=4,
                                             separators=(',', ': '))

        # notification_arns = ([get_status_topic(snsregion, snsaccountid)]
        #                      if snsaccountid is not None
        #                      else None)
        notification_arns = []
        # Disabling notification_arns as CloudFormation will only send
        # SNS notifications to SNS topics in the same region that the
        # CloudFormation stack is in (despite the fact that the region
        # name is embedded in the topic ARN (grumble)).
        # If we were to create ForeignAccountStatus SNS topics in every
        # region we could then send each stack's notifications to the
        # topic in it's own region.

        cloudformation_args = {
            'StackName': STACK_NAME,
            'TemplateBody': cloudformation_template,
            'Parameters': [{'ParameterKey': 'BucketName',
                            'ParameterValue': bucketname},
                           {'ParameterKey': 'SNSAccountId',
                            'ParameterValue': snsaccountid
                            if snsaccountid is not None
                            else ''},
                           {'ParameterKey': 'SNSRegion',
                            'ParameterValue': snsregion}],
            'NotificationARNs': notification_arns}

        client_cloudformation = boto3.client('cloudformation',
                                             region_name=region)
        existing_stack = stack_present(STACK_NAME, region)
        if existing_stack:
            output['Existing CloudFormation Stacks'][region] = existing_stack
            if not dryrun:
                client_cloudformation.update_stack(**cloudformation_args)
            else:
                logger.info('Dryrun preventing update of CloudTrail in region'
                            ' %s' % region)
            continue

        if len(current_cloudtrails) == 1:
            # A CloudTrail is already configured

            # Record the current settings
            output['Existing CloudTrails'][region] = current_cloudtrails[0]

            # We'll assume nobody is configuring CloudTrail with CloudFormation
            # already and so we won't worry about identifying parent
            # CloudFormation stacks or cleaning them up

            # Delete the CloudTrail
            logger.info('Deleting CloudTrail %s' %
                        current_cloudtrails[0]['Name'])
            if not dryrun:
                client_cloudtrail.delete_trail(
                    Name=current_cloudtrails[0]['Name'])
            else:
                logger.info('Dryrun preventing deletion of CloudTrail %s' %
                            current_cloudtrails[0]['Name'])
        elif len(current_cloudtrails) > 1:
            raise Exception('AWS returned more than 1 CloudTrail for the '
                            'region %s which should be impossible' %
                            region)

        logger.info('Creating CloudTrail in region %s' % region)
        if not dryrun:
            logger.debug('CloudFormation template is "%s"' %
                         cloudformation_template)
            output['New CloudTrails'][region] = (
                client_cloudformation.create_stack(**cloudformation_args))
        else:
            output['New CloudTrails'][region] = {"Dryrun StackId": "none"}
            logger.info('Dryrun preventing creation of CloudTrail in region'
                        ' %s' % region)

    return output


def report_status(data, snsregion, snsaccountid):
    message = json.dumps(data,
                         sort_keys=True,
                         indent=4,
                         separators=(',', ': '),
                         cls=PythonObjectEncoder)
    if snsaccountid is not None:
        client = boto3.client('sns', region_name=snsregion)
        client.publish(
            TargetArn=get_status_topic(snsregion, snsaccountid),
            Message=message)
    else:
        print(message)
    logger.info(message)


def get_status_topic(snsregion, snsaccountid):
    return "arn:aws:sns:%s:%s:ForeignAccountStatus" % (
        snsregion, snsaccountid)


@handler_decorator(delete_logs=False)
def configure_cloudtrail_to_use_mozilla_secure_storage(event, context):
    """Deploy CloudTrail CloudFormation templates in all regions

    CloudFormation custom resource property inputs :
        BucketName : The S3 bucket name to use for secure storage.

    CloudFormation custom resource attribute outputs :
        result : String describing the result of the action.
    """
    snsregion = 'us-west-2'
    snsaccountid = '088944123687'
    if 'BucketName' not in event['ResourceProperties']:
        raise ValueError(
            'BucketName argument not present in ResourceProperties')

    if event['RequestType'] == 'Create':
        result = deploy_stacks(
            bucketname=event['ResourceProperties']['BucketName'],
            snsregion=snsregion,
            snsaccountid=snsaccountid,
            accountid=get_account_id(event),
            dryrun=False)
        report_status(
            data=result,
            snsregion=snsregion,
            snsaccountid=snsaccountid)
        logger.info('result is %s' % json.dumps(result))
    elif event['RequestType'] == 'Delete':
        delete_stacks()
    else:
        logger.info('Skipping due to request type %s' % event['RequestType'])
