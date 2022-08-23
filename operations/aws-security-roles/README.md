Mozilla Security Assurance provides these AWS Security Roles
to enable Mozilla AWS account owners to delegate rights to Security Assurance
to provide security services for AWS accounts.

# What do these templates do?

You can delegate rights in your AWS account (member account) to Security 
Assurance by deploying  the CloudFormation templates in this repository which
* Create a security auditing IAM role which grants Security Assurance read only
  rights to audit resources in the member account for security risks. You can 
  see what rights in the member account delegate by looking at 
  [the trust policy in this template](eis-security-audit-trusting-role.yml)
* Create an incident response IAM role which delegates full administrative
  permissions from the member account to a dedicated incident response AWS 
  account controlled by Security Assurance. This dedicated `infosec-trusted` AWS
  account is a locked down account that can only be used to both issue temporary
  STS credentials for use during a security incident and to emit a notification 
  to both Security Assurance and the member account that temporary credentials 
  have been generated. This notification is to ensure that it's not possible for
  anyone (an incident responder or a potential attacker) to gain access to a 
  member account using the incident response role without both the account 
  holder and Security Assurance being notified.
* Create a Simple Notification Service (SNS) topic that will receive
  notifications if the incident response role is used. Optionally you can
  subscribe an email address to the SNS topic during stack creation
* Create a GuardDuty member role that will allow Security Assurance to enable 
  GuardDuty in the member account and link it up with the Mozilla GuardDuty 
  master account which will publish GuardDuty findings into the Mozilla Security
  Event and Information Management system.

# How do I use these templates?

Either update your existing `InfosecClientRoles` CloudFormation stack or if you
don't have one, deploy a stack.

## Update your existing stack

### Update in the web console

* Browse to the [CloudFormation section](https://console.aws.amazon.com/cloudformation/home?region=us-west-2)
* Find the `InfosecClientRoles` (or whatever you named it) stack and check the check
  circle next to it
* In the `Actions` drop down in the upper right select `Update Stack`
  * On the `Prerequisite - Prepare template` screen select `Replace current
    template`
  * In the `Amazon S3 URL` field enter 
 
    https://s3.us-west-2.amazonaws.com/public.us-west-2.infosec.mozilla.org/infosec-security-roles/cf/infosec-security-audit-incident-response-guardduty-roles-cloudformation.yml

* Click the `Next` button
* Enter an optional email address to receive notifications at of use of the incident
  response role
* On the `Specify stack details` click the `Next` button
* On the `Configure stack options` page click the `Next` button
* On the `Review` page click the checkbox that says `I acknowledge that AWS 
  CloudFormation might create IAM resources.`
* Click the `Update stack` button
* When the CloudFormation stack completes the creation process and the `Status`
  field changes from `UPDATE_IN_PROGRESS` to `UPDATE_COMPLETE` you're done.

### Update on the command line

* Set the EMAIL_ADDRESS that you'd like to receive notifications at if/when the
  incident response role is ever used
* Enter the STACK_NAME of your existing InfosecClientRoles stack
* Enter the REGION the existing stack is deployed in 

```bash
EMAIL_ADDRESS=example@example.com
STACK_NAME=InfosecClientRoles
REGION=us-west-2
AWS_DEFAULT_REGION=${REGION} aws cloudformation update-stack \
  --stack-name ${STACK_NAME} \
  --template-url https://s3.amazonaws.com/public.us-west-2.infosec.mozilla.org/infosec-security-roles/cf/infosec-security-audit-incident-response-guardduty-roles-cloudformation.yml \
  --parameters ParameterKey=EmailAddress,ParameterValue=${EMAIL_ADDRESS} \
  --capabilities CAPABILITY_IAM
```

## Create a new stack

If you've not deployed a previous `InfosecClientRoles` stack, or you'd prefer to
delete your current stack and deploy a new one (instead of updating) here's how
to create a new stack.

### Create in the web console

* Start by clicking this button [![Deploy Roles](
https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](
https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL=https://s3.us-west-2.amazonaws.com/public.us-west-2.infosec.mozilla.org/infosec-security-roles/cf/infosec-security-audit-incident-response-guardduty-roles-cloudformation.yml&stackName=InfosecClientRoles)
* Enter an email address if you'd like to subscribe to notifications of use of the Security Incident Response role
* Click the checkbox that says `I acknowledge that this template might cause AWS CloudFormation to create IAM resources.`
* Click the `Create` button
* When the CloudFormation stack completes the creation process and the `Status`
  field changes from `CREATE_IN_PROGRESS` to `CREATE_COMPLETE` you're done.

### Create on the command line

* Set the EMAIL_ADDRESS that you'd like to receive notifications at if/when the
  incident response role is ever used

```bash
EMAIL_ADDRESS=example@example.com
AWS_DEFAULT_REGION=us-west-2 aws cloudformation create-stack \
  --stack-name InfosecClientRoles \
  --template-url https://s3.amazonaws.com/public.us-west-2.infosec.mozilla.org/infosec-security-roles/cf/infosec-security-audit-incident-response-guardduty-roles-cloudformation.yml \
  --parameters ParameterKey=EmailAddress,ParameterValue=${EMAIL_ADDRESS} \
  --capabilities CAPABILITY_IAM
```

# Are there alternatives?

If you would like to consume a subset of the three services (security auditing,
incident response and GuardDuty) instead of all three, contact Mozilla
Security Assurance for assistance.

# FAQ

* Why does the incident response role trust the entire `infosec-trusted` AWS
  account instead of a specific user or role?
  * This is due to a limitation in how AWS STS Role assumption works that
    prevents chaining trust relationships
* Why doesn't detection of the use of the incident response role happen in
  the member account instead of in the `infosec-trusted` account, wouldn't this
  be more secure?
  * Unfortunately, AWS CloudWatch Event Rules can not trigger on STS AssumeRole
    calls initiated from another account, despite the fact that [AWS copies the
    CloudTrail event](https://aws.amazon.com/blogs/security/aws-cloudtrail-now-tracks-cross-account-activity-to-its-origin/).
    Automated detection from the member account side would require custom code
    to parse and alert on CloudTrail events.
* How else can I be notified about use of the incident response role beyond the
  optional email address entered when the stack is deployed?
  * The SNS topic created in the member account will receive any notifications
    and you can subscribe anything you'd like to that topic (email, SMS, lambda)
* How do the IAM Role ARN values get communicated back to Security Assurance?
  * Previously the `InfosecClientRoles` stack contained a Lambda function which
    emitted the ARN values to SNS. In the current version this has been changed
    to a CloudFormation custom resource that uses our [CloudFormation Cross Account Outputs](https://github.com/mozilla/cloudformation-cross-account-outputs)
    system instead.
* When will GuardDuty events begin showing up in the Security Assurance SIEM?
  * The [GuardDuty Multi Account Manager](https://github.com/mozilla/guardduty-multi-account-manager/)
    runs nightly and links member accounts, such that GuardDuty data will be
    present in the Mozilla SIEM the day after the stack is deployed in the 
    member account.
