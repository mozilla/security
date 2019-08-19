# Clean Security Roles

This tool
* Fetches the list of AWS IAM Role ARNs stored in the [CloudFormation Cross Account Outputs](https://github.com/mozilla/cloudformation-cross-account-outputs)
  table
* Attempts to assume each one
* Gathers a list of AWS accounts for which role assumption fails
* If `DRY_RUN` is True, output the list of AWS accounts which role assumption
  failed for
* If `DRY_RUN` is False, delete all records from the [CloudFormation Cross Account Outputs](https://github.com/mozilla/cloudformation-cross-account-outputs)
  table for each AWS account for which role assumption failed

The reason this is necessary is that when an AWS account is closed, the
CloudFormation stacks within that account do not shutdown (triggering cleanup of
records from the DynamoDB table) they are just deleted. This tool cleans up
those left over records

## Usage

1. Deploy the CloudFormation template
2. Run the Lambda function manually
3. Look at the resulting AWS accounts which have security audit roles that can't
   be assumed. Confirm that each of those are AWS accounts that have been closed
4. If all of the accounts have been closed, change `DRY_RUN` to False in the
   Lambda function and run it a second time to delete the DynamoDB records
5. Either switch `DRY_RUN` back to True or delete the CloudFormation template
