Overview
========

Build AWS CloudTrail storage infrastructure CloudFormation template

Configuration
=============
Pass in the configuration file with the "-c" command line argument. Create a
configuration file by using the included "build_cloudtrail_storage.example.yaml
file.

The configuration file is a yaml representation of a hash with a single record.
The record has a key of "AccountRootARNs" and a value which is a list of ARNs
of each AWS account that will use this storage infrastructure.

Example Configuration
---------------------
Here is an example configuration

::

    --- 

      AccountRootARNs:
      - arn:aws:iam::123456789012:root
      - arn:aws:iam::345678901234:root
      - arn:aws:iam::567890123456:root

Usage
=====

::

    build_cloudtrail_storage > cloudformation_template.json
