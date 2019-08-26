# OIDC Identity Provider CloudFormation Template Custom Resource

This template and associated Lambda function and custom resource add support to \
AWS CloudFormation for the [AWS IAM OpenId Connect Identity Provider][1]
resource type.

## Usage

Launch the CloudFormation stack using the [`Makefile`](Makefile) by running a
command like

```shell script
make S3_BUCKET=my-s3-bucket-name deploy-cloudformation-stack
```

This will launch the stack with example URL, Client IDs and Thumbprints.

To pass your actual settings, either
* Run `make` and pass in the values, for example
  ```shell script
  export S3_BUCKET=my-s3-bucket-name
  export CLIENT_ID_LIST=clientid1,clientid2
  export THUMBPRINT_LIST=34567890abcdef1234567890abcdef1234567890,4567890abcdef1234567890abcdef1234567890a
  make deploy-cloudformation-stack
  ```
* Edit the `Makefile` and set new defaults
* Launch the stack with the defaults, then do a stack update and pass in the
  real values

## Why a separate Lambda file

The code to handle creation updating and deletion of the OIDC Identity Provider
couldn't fit into the [4096 characters][2] allowed for embedded code without
heavily obfuscating the code.

## Inspiration

This project was inspired by the [cfn-identity-provider][3] by [Colin Panisset][4]
of [Cevo][5] which provides a similar function but for the SAML identity provider

[1]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html
[2]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-lambda-function-code.html#cfn-lambda-function-code-zipfile
[3]: https://github.com/cevoaustralia/cfn-identity-provider
[4]: https://github.com/nonspecialist
[5]: https://cevo.com.au/
