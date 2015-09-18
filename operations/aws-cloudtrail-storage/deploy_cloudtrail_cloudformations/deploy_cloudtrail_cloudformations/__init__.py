#!/usr/bin/env python

import boto.cloudtrail
import boto.cloudformation
import boto.sns
import boto
import json
import argparse
import logging
# logging.basicConfig(level=logging.DEBUG)

DEFAULT_SNS_REGION = 'us-east-1'
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

def get_options():
    parser = argparse.ArgumentParser(description='Deploy Mozilla secure '
                 'CloudTrail CloudFormation template in every region')
    parser.add_argument('bucketname',  
                help="Secure CloudTrail storage S3 bucket name")
    parser.add_argument('--snsaccountid', 
                help="AWS account ID of the secure CloudTrail storage "
                "account")
    parser.add_argument('--snsregion', default=DEFAULT_SNS_REGION, 
                help="AWS region of the secure CloudTrail storage "
                "account's SNS topic (default: %s)" % DEFAULT_SNS_REGION)
    parser.add_argument('--dryrun', action='store_true',
                help="Don't actually make any changes")
    return parser.parse_args()

def get_account_id():
    metadata = boto.utils.get_instance_metadata(timeout=1, num_retries=1)
    if 'iam' in metadata:
        # We're running in an ec2 instance, get the account id from the instance
        # profile ARN
        return metadata['iam']['info']['InstanceProfileArn'].split(':')[4]
    else:
        try:
            # We're not on an ec2 instance but have api keys, get the account id
            # from the user ARN
            return boto.connect_iam().get_user().arn.split(':')[4]
        except:
            # We don't have IAM or user credentials
            return False

def deploy_stacks(args):
    # args.bucketname, args.snsregion, args.snsaccountid
    output = {'Account ID': get_account_id(),
              'Existing CloudTrails':{},
              'New CloudTrails':{}}
    
    # Iterate over each region, loading the CloudFormation template in each
    # to configure CloudTrail
    # Note : Default Centos 7 boto (version 2.25.0 only lists 2 regions supported)
    for region in boto.cloudtrail.regions():
        conn_cloudtrail = boto.cloudtrail.connect_to_region(region.name)
        current_cloudtrails = conn_cloudtrail.describe_trails()['trailList']
        if len(current_cloudtrails) == 1:
            # A CloudTrail is already configured
            
            # Record the current settings
            output['Existing CloudTrails'][region.name] = current_cloudtrails[0]
            
            # We'll assume nobody is configuring CloudTrail with CloudFormation already
            # and so we won't worry about identifying parent CloudFormation stacks or
            # cleaning them up
    
            # Delete the CloudTrail
            logging.info('Deleting CloudTrail %s' % 
                         current_cloudtrails[0]['Name'])
            if not args.dryrun:
                conn_cloudtrail.delete_trail(current_cloudtrails[0]['Name'])
            else:
                logging.info('Dryrun preventing deletion of CloudTrail %s' % 
                             current_cloudtrails[0]['Name'])
        elif len(current_cloudtrails) > 1:
            raise Exception('AWS returned more than 1 CloudTrail for the '
                            'region %s which should be impossible' % 
                            region.name)
        
        # Load the base template
        cloudformation = json.loads(base_template % {'region': region.name,
                                                     'default_sns_region': DEFAULT_SNS_REGION})
        
        # Send all global (non region specific) CloudTrail log lines 
        # (e.g. IAM calls) to us-east-1
        if region.name == 'us-east-1':
            cloudformation['Resources']['CloudTrail']['Properties']['IncludeGlobalServiceEvents'] = True
        
        cloudformation_template = json.dumps(cloudformation, 
                                             sort_keys=True,
                                             indent=4,
                                             separators=(',', ': '))
        conn_cloudformation = boto.cloudformation.connect_to_region(region.name)
    
        logging.info('Creating CloudTrail in region %s' % region.name)
        if not args.dryrun:
            output['New CloudTrails'][region.name] = conn_cloudformation.create_stack(
                            stack_name = 'MozillaSecuredCloudTrail',
                            template_body = cloudformation_template,
                            parameters = [("BucketName", args.bucketname),
                                          ("SNSAccountId", args.snsaccountid if args.snsaccountid is not None else ''),
                                          ("SNSRegion", args.snsregion)],
                            notification_arns=[get_status_topic(args)] if args.snsaccountid is not None else None)
            # notification_arns behavior changes between boto 2.25.0 (the version present in Centos 7) 
            # and 2.26.0.
            # https://github.com/boto/boto/commit/4191aefa51292668847544998fa1add6e9f37e79
            # In 2.26.0 an after notification_arns is None not an empty list
        else:
            output['New CloudTrails'][region.name] = {"Dryrun StackId": "none"}
            logging.info('Dryrun preventing creation of CloudTrail in region %s'
                         % region.name)

    return output

def report_status(data, args):
    if args.snsaccountid is not None:
        conn_sns = boto.sns.connect_to_region(args.snsregion)
        conn_sns.publish(target_arn=get_status_topic(args),
                         message=json.dumps(data))
    else:
        print(json.dumps(data))
    logging.info(json.dumps(data, 
               sort_keys=True,
               indent=4,
               separators=(',', ': ')))


def get_status_topic(args):
    return "arn:aws:sns:%s:%s:ForeignAccountStatus" % (
                args.snsregion, args.snsaccountid)

def main():
    #  us-west-2 088944123687 mozilla-cloudtrail-logs
    # mozilla-cloudtrail-logs --snsaccountid 088944123687 --snsregion us-west-2 --dryrun
    args = get_options()
    result = deploy_stacks(args)
    report_status(result, args)

if __name__ == "__main__":
    main()