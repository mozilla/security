import boto3
import pytest

class TestMozdefPolicies():
    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.client = boto3.client('iam')

    # http://boto3.readthedocs.io/en/latest/reference/services/iam.html#IAM.Client.simulate_custom_policy
    def test_allowed_list_buckets(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['s3:ListAllMyBuckets']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'


    def test_allowed_list_bucket_contents(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['s3:ListBucket'],
            ResourceArns=[
                'arn:aws:s3:::%s' % config['BackupBucketName'],
                'arn:aws:s3:::%s' % config['BlocklistBucketName'],
                'arn:aws:s3:::%s' % config['IPSpaceBucketName'],
            ]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'


    def test_allowed_write_to_mozdefes2backups(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['s3:PutObject', 's3:DeleteObject'],
            ResourceArns=['arn:aws:s3:::%s/example_file.txt' % config['BackupBucketName'],]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_allowed_write_to_mozilla_infosec_blocklist(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['s3:PutObject'],
            ResourceArns=['arn:aws:s3:::%s/example_file.txt' % config['BlocklistBucketName']]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_denied_write_to_bucket(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['s3:PutObject'],
            ResourceArns=[
                'arn:aws:s3:::BucketThatIsNotAllowed/example_file.txt']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'implicitDeny'

    def test_allowed_read_from_mozilla_ipspace(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['s3:GetObject'],
            ResourceArns=['arn:aws:s3:::%s/example_file.txt' % config['IPSpaceBucketName']]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_denied_read_from_bucket(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['s3:GetObject'],
            ResourceArns=['arn:aws:s3:::BucketThatIsNotAllowed/example_file.txt']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'implicitDeny'

    def test_allowed_list_cloudtrail_bucket_contents(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['s3:ListBucket'],
            ResourceArns=['arn:aws:s3:::AnyBucketAtAll']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_allowed_get_cloudtrail_log(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['s3:GetObject'],
            ResourceArns = ['arn:aws:s3:::AnyBucketAtAll/AWSLogs/012345678901/CloudTrail/ap-northeast-1/2017/02/15/012345678901_CloudTrail_ap-northeast-1_20170215T0000Z_UVpGnwCcvkdew1nf.json.gz']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_allowed_describe_cloudtrails(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['cloudtrail:DescribeTrails']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_allowed_get_session_token(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['sts:GetSessionToken']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_allowed_assume_security_audit_role(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['sts:AssumeRole'],
            ResourceArns=['arn:aws:iam::012345678901:role/InfosecClientRoles-InfosecSecurityAuditRole-01245ABCDEFG']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_denied_assume_security_audit_role(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['sts:AssumeRole'],
            ResourceArns=['arn:aws:iam::012345678901:role/SomeRoleThatIsNotAllowed']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'implicitDeny'

    def test_allowed_infosec_sqs_actions(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=[
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage"
              ],
            ResourceArns=[config['InfosecQueueArn']]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_denied_infosec_sqs_actions(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=[
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage"
              ],
            ResourceArns=['arn:aws:sqs:us-west-2:012345678901:SomeOtherSQSQueue']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'implicitDeny'

    def test_denied_infosec_sqs_send_message(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=["sqs:SendMessage"],
            ResourceArns=[config['InfosecQueueArn']]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'implicitDeny'

    def test_allowed_mig_sqs_actions(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=[
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage"
              ],
            ResourceArns=[config['MIGQueueArn']]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_denied_mig_sqs_send_message(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=["sqs:SendMessage"],
            ResourceArns=[config['MIGQueueArn']]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'implicitDeny'

    def test_allowed_fxa_sqs_actions(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=[
                "sqs:GetQueueUrl",
                "sqs:SendMessage"
              ],
            ResourceArns=[config['FxaQueueArn']]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_denied_fxa_sqs_actions(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=[
                "sqs:GetQueueUrl",
                "sqs:SendMessage"
              ],
            ResourceArns=['arn:aws:sqs:us-west-2:012345678901:SomeOtherSQSQueue']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'implicitDeny'

    def test_denied_fxa_sqs_delete_message(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=["sqs:DeleteMessage"],
            ResourceArns=[config['FxaQueueArn']]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'implicitDeny'

    def test_allowed_assume_fxa_role(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=['sts:AssumeRole'],
            ResourceArns=['arn:aws:iam::361527076523:role/ExampleRole']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_allowed_vpc_blackholing(self, config):
        response = self.client.simulate_principal_policy(
            PolicySourceArn=config['source_arn'],
            ActionNames=[
                "ec2:DescribeRouteTables",
                "ec2:DescribeNetworkInterfaces",
                "ec2:CreateRoute"
              ]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'
