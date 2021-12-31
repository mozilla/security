# OIDC Identity Provider CloudFormation Template Custom Resource

This directory previously held a CloudFormation Custom Resource to enable provisioning 
an [AWS IAM OpenId Connect Identity Provider][1].

On February 25, 2021 AWS added [native CloudFormation support][2]
for this resource type, obviating a need for this custom resource code.

To transition to the native resource, you can't merely update the CloudFormation
stack containing the custom resource to use the new native resource as 
CloudFormation attempts to create the new resource before removing the old 
custom resource, causing a resource creation failure (due to the identity 
provider already existing).

As a result **you have to delete the current CloudFormation stack with the custom
resource and then create a new CloudFormation stack using the native resource**.

You can view the now deprecated custom resource code at commit 
[`cdb6a75bea3ed58c1f28737af65aea3ee8c723e3`][3]

[1]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html
[2]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iam-oidcprovider.html
[3]: https://github.com/mozilla/security/tree/cdb6a75bea3ed58c1f28737af65aea3ee8c723e3/operations/cloudformation-templates/oidc_identity_provider