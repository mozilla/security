These instructions show how to both create a *trusted* IAM role (likely in 
the `infosec-prod` AWS account) and *trusting* IAM roles in foreign AWS accounts. 
This will allow other Mozilla teams with AWS accounts to delegate permissions 
to Infosec to enable Infosec to perform security audits and incident response.

The IAM policies in the *trusting* account's roles contain a list of permissions
which are based on the AWS built in "Security Audit" IAM role as well as
permissions Infosec has defined for the purposes of incident response.

# Trusting Account

Here's how to create an IAM role for the trusting account. This would be done 
by a foreign AWS account holder who wants to grant Infosec the ability to audit 
the security of their AWS account and perform incident response in the event of
a security issue.

## Create a Trusting Account using cloudformation

* The foreign AWS account holder should log into their AWS web console in
  in either the `us-west-2` region or the `us-east-1` region (the only regions
  that support AWS Lambda currently)
* Browse to the [CloudFormation section](https://console.aws.amazon.com/cloudformation/home?region=us-west-2)
* Click the `Create Stack` button
  * In the `Name` field enter something like `InfosecClientRoles`
  * In the `Source` field select `Specify an Amazon S3 template URL` and type
    in 
 
    https://s3.amazonaws.com/infosec-cloudformation-templates/infosec-security-audit-incident-response-roles-cloudformation.json

* Click the `Next` button
* Deploy the `infosec-security-audit-incident-response-roles-cloudformation.json`
  template
* On the `Options` page click the `Next` button
* On the `Review` page click the checkbox that says `I acknowledge that this
  template might cause AWS CloudFormation to create IAM resources.`
* Click the `Create` button
* When the CloudFormation stack completes the creation process and the `Status`
  field changes from `CREATE_IN_PROGRESS` to `CREATE_COMPLETE`.


## Trusting account alternatives

If the owner of the *trusting* account would *only* like to utilize Infosec's
security auditing service and to take on incident response in the event of a
security breach themselves, that account owner can instead create a *trusting*
role which only delegates permissions to Infosec related to security auditing.

To do so, load this CloudFormation template instead

https://s3.amazonaws.com/infosec-cloudformation-templates/infosec-security-audit-trusting-role-cloudformation.json

# Trusted account

Since the *trusting* accounts delegate permissions not to a specific IAM Role
within the `infosec-prod` AWS account, but instead to the entire `infosec-prod`
AWS account, any user or IAM Role in the `infosec-prod` account which is granted
permissions within the `infosec-prod` account to assume the role of the 
*trusting* account's IAM Role can do so.

The reason that we request the *trusting* accounts delegate permissions to the
`infosec-prod` account and not a specific IAM role is due to a limitation in
AWS related to multiple IAM Roles chained role assumption.
