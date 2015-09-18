#!/usr/bin/env python

from cfn_pyplates.core import CloudFormationTemplate, Mapping, Resource, JSONableDict, DeletionPolicy
from cfn_pyplates.functions import ref, join, find_in_map
import yaml
import argparse

def type_yaml_config(filename):
    try:
        with open(filename) as f:
            return yaml.load(f)
    except:
        raise argparse.ArgumentTypeError("'%s' is not a valid YAML config "
                                         "file" % filename)
def get_options():
    default_filename = "/etc/build_cloudtrail_storage.yaml"
    parser = argparse.ArgumentParser(description='Build CloudTrail Storage '
                                     'CloudFormation Template')
    parser.add_argument('-c', '--config', type=type_yaml_config, 
                        default=default_filename, 
                        help='Config filename (default: %s)' % default_filename)
    return parser.parse_args()
    
def get_account_id_from_arn(arn):
    return arn.split(":")[4]

def build_template(config):
    """
    Build a CloudFormation template allowing for secure CloudTrail log aggregation
    and fine grained access control to SNS topics for notifications of new
    CloudTrail logs
    """

    account_root_arns = (config['AccountRootARNs']
                         if 'AccountRootARNs' in config 
                            and isinstance(config['AccountRootARNs'], list)
                         else [])

    # http://docs.aws.amazon.com/general/latest/gr/rande.html#ct_region
    cloudtrail_system_accountids = {
        'us-east-1': '086441151436',
        'us-west-1': '388731089494',
        'us-west-2': '113285607260',
        'eu-west-1': '859597730677',
        'eu-central-1': '035351147821',
        'ap-southeast-2': '284668455005',
        'ap-southeast-1': '903692715234',
        'ap-northeast-1': '216624486486',
        'sa-east-1': '814480443879'}
    
    cloudtrail_system_arns = ["arn:aws:iam::%s:root" % x for x in cloudtrail_system_accountids.values()]
    
    variable_map_mapping = {
        "CloudTrailLogPublishers":
            {"AccountRootARNs": account_root_arns},
        "CloudTrailSystem":
            {"SystemARNs": cloudtrail_system_arns}
    }

    cft = CloudFormationTemplate(description="AWS CloudTrail Storage Account S3 Storage Bucket")
    
    cft.mappings.add(Mapping("VariableMap", variable_map_mapping))
    
    cft.resources.add(Resource("S3Bucket", 
                               "AWS::S3::Bucket", 
                               {"BucketName":"mozilla-cloudtrail-logs"}, 
                               DeletionPolicy("Retain")))

    
    # Build the s3 bucket policy statement list to allow foreign accounts to
    # GetBucketAcl on the CloudTrail storage bucket
    # PutObject their CloudTrail logs into their account's specific directory
    bucket_policy_statements = []
    bucket_policy_statements.append({
      "Sid":"AWSCloudTrailAclCheck",
      "Effect":"Allow",
      "Principal":{
        "AWS": find_in_map("VariableMap", "CloudTrailSystem", "SystemARNs")
      },
      "Action": ["s3:GetBucketAcl"],
      "Resource": join("", "arn:aws:s3:::", ref("S3Bucket"))
    })
    
    put_object_resources = []
    for account_arn in variable_map_mapping["CloudTrailLogPublishers"]["AccountRootARNs"]:
        put_object_resources.append(
            join("", 
                 "arn:aws:s3:::", 
                 ref("S3Bucket"), 
                 "/AWSLogs/%s/*" % get_account_id_from_arn(account_arn)))
    
    bucket_policy_statements.append(
    {
      "Sid":"AWSCloudTrailWrite%s" % get_account_id_from_arn(account_arn),
      "Effect":"Allow",
      "Principal": {
        "AWS": find_in_map("VariableMap", "CloudTrailSystem", "SystemARNs")
      },
      "Action": ["s3:PutObject"],
      "Resource": put_object_resources,
      "Condition":{
        "StringEquals":{
          "s3:x-amz-acl":"bucket-owner-full-control"
        }
      }
    })
    
    
    cft.resources.add(
        Resource(
            "BucketPolicy",
            "AWS::S3::BucketPolicy",
            {
                "Bucket":ref("S3Bucket"),
                "PolicyDocument": {
                    "Id" : "BucketPolicyDocument",
                    "Version":"2012-10-17", 
                    "Statement":bucket_policy_statements
                }
            }
            )
        )

    # Create a single SNS Topic that each AWS account can publish to to report
    # on the CloudFormation progress
    cft.resources.add(
        Resource("ForeignAccountStatusTopic",
            "AWS::SNS::Topic",
            {
                "DisplayName":"Topic for foreign accounts to publish status information to",
                "TopicName":"ForeignAccountStatus"
            }
            )
        )

    cft.resources.add(
        Resource("ForeignAccountStatusTopicPolicy",
            "AWS::SNS::TopicPolicy",
            {
                "Topics":[ref("ForeignAccountStatusTopic")],
                "PolicyDocument":{
                    "Version" : "2012-10-17",
                    "Id":"ForeignAccountStatusPolicy",
                    "Statement":[
                        {
                            "Sid":"ForeignAccountStatusPolicyStatement",
                            "Effect":"Allow",
                            "Principal": {
                                "AWS": find_in_map("VariableMap","CloudTrailLogPublishers","AccountRootARNs")
                            },
                            "Action":"SNS:Publish",
                            "Resource": "*"
                        }
                     ]
                }
            }
            )
        )



    # Create SNS Topics for each AWS account and grant those accounts rights
    # to publish and subscribe to those topics     
    for account_arn in variable_map_mapping["CloudTrailLogPublishers"]["AccountRootARNs"]:
        cft.resources.add(
            Resource("Topic%s" % get_account_id_from_arn(account_arn),
                "AWS::SNS::Topic",
                {
                    "DisplayName":"Mozilla CloudTrail Logs Topic for Account %s" % get_account_id_from_arn(account_arn),
                    "TopicName":"MozillaCloudTrailLogs%s" % get_account_id_from_arn(account_arn)
                }
                )
            )
        cft.resources.add(
            Resource("TopicPolicy%s" % get_account_id_from_arn(account_arn),
                "AWS::SNS::TopicPolicy",
                {
                    "Topics":[ref("Topic%s" % get_account_id_from_arn(account_arn))],
                    "PolicyDocument":{
                        "Version" : "2012-10-17",
                        "Id":"AWSCloudTrailSNSPolicy%s" % get_account_id_from_arn(account_arn),
                        "Statement":[
                            {
                                "Sid":"AWSCloudTrailSNSPolicyStatement%s" % get_account_id_from_arn(account_arn),
                                "Effect":"Allow",
                                "Principal":{
                                    "AWS": account_arn
                                },
                                "Action":[
                                    "SNS:Publish",
                                    "SNS:GetTopicAttributes",
                                    "SNS:ListSubscriptionsByTopic",
                                    "SNS:Subscribe"
                                ],
                                "Resource": join(":", "arn:aws:sns", ref("AWS::Region"), ref("AWS::AccountId"), "MozillaCloudTrailLogs%s" % get_account_id_from_arn(account_arn))
                                # Not sure if we need a resource assertion here (other than "*") in that this PolicyDocument is a peer to a Topics entry which should contstrain
                                # the policy to apply to the topic.
                                # Maybe the difference is between an IAM Policy (which should have a resource definition) and a TopicPolicy which doesn't need it
                                # I'm unsure from this page if that's the case : http://docs.aws.amazon.com/sns/latest/dg/UsingIAMwithSNS.html
                            }
                         ]
                    }
                }
                )
            )
    return cft

def main():
    args = get_options()
    print str(build_template(args.config))

if __name__ == "__main__":
    main()