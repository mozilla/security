Overview
========

Configure CloudTrail in all AWS regions by deploying CloudFormation templates.

Installation
============

You can install this from github with this pip command.

::

    pip install -e 'git+https://github.com/mozilla/security.git#egg=deploy_cloudtrail_cloudformations&subdirectory=operations/aws-cloudtrail-storage/deploy_cloudtrail_cloudformations'


Usage
=====

::

    usage: deploy_cloudtrail_cloudformations [-h] [--snsaccountid SNSACCOUNTID]
                       [--snsregion SNSREGION] [--dryrun]
                       bucketname
    
    Deploy Mozilla secure CloudTrail CloudFormation template in every region
    
    positional arguments:
      bucketname            Secure CloudTrail storage S3 bucket name
    
    optional arguments:
      -h, --help            show this help message and exit
      --snsaccountid SNSACCOUNTID
                            AWS account ID of the secure CloudTrail storage
                            account
      --snsregion SNSREGION
                            AWS region of the secure CloudTrail storage account's
                            SNS topic (default: us-east-1)
      --dryrun              Don't actually make any changes
