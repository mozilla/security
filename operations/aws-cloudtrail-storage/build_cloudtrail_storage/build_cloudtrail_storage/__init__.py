#!/usr/bin/env python

from cfn_pyplates.core import CloudFormationTemplate, Mapping, Resource, JSONableDict, DeletionPolicy, DependsOn, Condition
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
                        help='Config filename (default: %s)' %
                        default_filename)
    parser.add_argument('-b', '--bucketname',
                        default='mozilla-cloudtrail-logs',
                        help='S3 bucket name (default: '
                        'mozilla-cloudtrail-logs)')
    return parser.parse_args()


def get_account_id_from_arn(arn):
    return arn.split(":")[4]


def build_template(args):
    """
    Build a CloudFormation template allowing for secure CloudTrail log
    aggregation and fine grained access control to SNS topics for notifications
    of new CloudTrail logs

    The reason that we create IAM roles for each client AWS account in order to
    enable clients to read their own CloudTrail logs, instead of merely
    delegating access to them in an S3 bucket policy is that

    "Bucket owner account can delegate permissions to users in its own account,
    but it cannot delegate permissions to other AWS accounts,
    because cross-account delegation is not supported." :
    http://docs.aws.amazon.com/AmazonS3/latest/dev/example-walkthroughs-managing-access-example4.html

    As a consequence we *can* delegate bucket permissions to client AWS
    accounts but we *can not* delegate object permissions (the log files
    themselves) to client AWS accounts.
    """
    config = args.config
    account_root_arns = (config['AccountRootARNs']
                         if 'AccountRootARNs' in config and
                         isinstance(config['AccountRootARNs'], list)
                         else [])

    cft = CloudFormationTemplate(
        description="AWS CloudTrail Storage Account S3 Storage Bucket")

    # Create the bucket
    cft.resources.add(Resource("S3Bucket",
                               "AWS::S3::Bucket",
                               {"BucketName": args.bucketname},
                               DeletionPolicy("Retain")))

    # Build the s3 bucket policy statement list
    bucket_policy_statements = []

    # Allow the CloudTrail system to GetBucketAcl on the CloudTrail storage
    # bucket
    bucket_policy_statements.append({
        "Sid": "AWSCloudTrailAclCheck",
        "Effect": "Allow",
        "Principal": {
            "Service": "cloudtrail.amazonaws.com"
        },
        "Action": ["s3:GetBucketAcl"],
        "Resource": join("", "arn:aws:s3:::", ref("S3Bucket"))
    })

    # Allow each account to read it's own logs
    for account_arn in account_root_arns:
        account_id = get_account_id_from_arn(account_arn)
        cft.resources.add(
            Resource(
                "CloudTrailLogReaderRole%s" % account_id,
                "AWS::CloudFormation::Stack",
                {
                    "TemplateURL": "https://s3.amazonaws.com/infosec-cloudformation-templates/manage_iam_role.json",
                    "Parameters": {
                        "RoleName": "CloudTrailLogReader%s" %
                                    account_id,
                        "TrustedEntities": account_arn
                    },
                    "TimeoutInMinutes": "5"
                }
            )
        )
        cft.resources.add(
            Resource(
                "CloudTrailLogReaderPolicy%s" % account_id,
                "AWS::IAM::Policy",
                {
                    "PolicyName": "CloudTrailLogReaderPolicy%s" %
                                  account_id,
                    "PolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Action": "s3:GetObject",
                            "Resource": join(
                                "",
                                "arn:aws:s3:::",
                                ref("S3Bucket"),
                                "/AWSLogs/%s/*" %
                                account_id)}]},
                    "Roles": ["CloudTrailLogReader%s" %
                              account_id]
                },
                DependsOn("CloudTrailLogReaderRole%s" % account_id)
            )
        )

    cft.resources.add(
        Resource("ReadCloudTrailBucket",
                 "AWS::IAM::ManagedPolicy",
                 {"Description": "ReadCloudTrailBucket",
                  "PolicyDocument": {
                      "Version": "2012-10-17",
                      "Statement": [
                          {"Effect": "Allow",
                           "Action": ["s3:ListAllMyBuckets",
                                      "s3:GetBucketLocation"],
                           "Resource": "*"
                           },
                          {"Effect": "Allow",
                           "Action": ["s3:GetBucketAcl",
                                      "s3:ListBucket",
                                      "s3:GetBucketTagging"],
                           "Resource": join("",
                                            "arn:aws:s3:::",
                                            ref("S3Bucket"))
                           }
                      ]
                  },
                  "Roles": ["CloudTrailLogReader%s" %
                            get_account_id_from_arn(account_arn) for
                            account_arn in account_root_arns]
                  },
                 DependsOn(["CloudTrailLogReaderRole%s" %
                            get_account_id_from_arn(account_arn) for
                            account_arn in account_root_arns])
                 ))

    bucket_policy_statements.append(
        {
            #       "Sid":"AWSCloudTrailWrite%s" % get_account_id_from_arn(account_arn),
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudtrail.amazonaws.com"
            },
            "Action": ["s3:PutObject"],
            "Resource": join("", "arn:aws:s3:::", ref("S3Bucket"), "/AWSLogs/*"),
            "Condition": {
                "StringEquals": {
                    "s3:x-amz-acl": "bucket-owner-full-control"
                }
            }
        })

    # Apply the bucket policy to the bucket
    cft.resources.add(
        Resource(
            "BucketPolicy",
            "AWS::S3::BucketPolicy",
            {
                "Bucket": ref("S3Bucket"),
                "PolicyDocument": {
                    "Id": "BucketPolicyDocument",
                    "Version": "2012-10-17",
                    "Statement": bucket_policy_statements
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
                     "DisplayName": "Topic for foreign accounts to publish status information to",
                     "TopicName": "ForeignAccountStatus"
                 }
                 )
    )

    cft.resources.add(
        Resource("ForeignAccountStatusTopicPolicy",
                 "AWS::SNS::TopicPolicy",
                 {
                     "Topics": [ref("ForeignAccountStatusTopic")],
                     "PolicyDocument": {
                         "Version": "2012-10-17",
                         "Id": "ForeignAccountStatusPolicy",
                         "Statement": [
                             {
                                 "Sid": "ForeignAccountStatusPublisher",
                                 "Effect": "Allow",
                                 "Principal": {"AWS": account_root_arns},
                                 "Action": "SNS:Publish",
                                 "Resource": ref("ForeignAccountStatusTopic"),
                             },
                             {
                                 "Sid": "ForeignAccountStatusSubscriber",
                                 "Effect": "Allow",
                                 "Principal": {
                                     "AWS": config['ForeignAccountStatusSubscribers']
                                 },
                                 "Action":[
                                     "SNS:GetTopicAttributes",
                                     "SNS:ListSubscriptionsByTopic",
                                     "SNS:Subscribe"
                                 ],
                                 "Resource": ref("ForeignAccountStatusTopic"),
                             }

                         ]
                     }
                 }
                 )
    )

    # Create SNS Topics for each AWS account and grant those accounts rights
    # to publish and subscribe to those topics
    for account_arn in account_root_arns:
        account_id = get_account_id_from_arn(account_arn)
        cft.resources.add(
            Resource(
                "Topic%s" % account_id,
                "AWS::SNS::Topic",
                {
                    "DisplayName": "Mozilla CloudTrail Logs Topic for Account %s" % account_id,
                    "TopicName": "MozillaCloudTrailLogs%s" % account_id
                }
            )
        )

        # http://docs.aws.amazon.com/sns/latest/dg/AccessPolicyLanguage_UseCases_Sns.html#AccessPolicyLanguage_UseCase4_Sns
        cft.resources.add(
            Resource(
                "TopicPolicy%s" % account_id,
                "AWS::SNS::TopicPolicy",
                {
                    "Topics": [ref("Topic%s" % account_id)],
                    "PolicyDocument": {
                        "Version": "2012-10-17",
                        "Id": "AWSCloudTrailSNSPolicy%s" % account_id,
                        "Statement": [
                            {
                                "Sid": "CloudTrailSNSPublish%s" % account_id,
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "cloudtrail.amazonaws.com"
                                },
                                "Action": "SNS:Publish",
                                "Resource": ref("Topic%s" % account_id)
                            },
                            {
                                "Sid": "CloudTrailSNSSubscribe%s" % account_id,
                                "Effect": "Allow",
                                "Principal": {
                                    "AWS": account_arn
                                },
                                "Action": [
                                    "SNS:GetTopicAttributes",
                                    "SNS:ListSubscriptionsByTopic",
                                    "SNS:Subscribe"
                                ],
                                "Resource": join(":", "arn:aws:sns", ref("AWS::Region"), ref("AWS::AccountId"), "MozillaCloudTrailLogs%s" % account_id)
                            }
                        ]
                    }
                }
            )
        )
    return cft


def main():
    args = get_options()
    print str(build_template(args))

if __name__ == "__main__":
    main()
