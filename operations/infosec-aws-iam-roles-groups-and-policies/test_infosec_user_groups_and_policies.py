import boto3

class TestInfosecPolicies():
    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.policies = {
            'InfosecRoleAssumptionPolicy': '''
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Resource": [
                            "arn:aws:iam::371522382791:role/InfosecRead",
                            "arn:aws:iam::371522382791:role/InfosecAdmin",
                            "arn:aws:iam::656532927350:role/InfosecRead",
                            "arn:aws:iam::656532927350:role/InfosecAdmin"
                        ],
                        "Effect": "Allow"
                    }
                ]
            }
            ''',
            'SelfManageMFAPolicy': '''
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": [
                            "iam:CreateVirtualMFADevice",
                            "iam:EnableMFADevice",
                            "iam:ResyncMFADevice",
                            "iam:DeleteVirtualMFADevice"
                        ],
                        "Resource": [
                            "arn:aws:iam::371522382791:mfa/${aws:username}",
                            "arn:aws:iam::371522382791:user/${aws:username}",
                            "arn:aws:iam::371522382791:mfa/*/${aws:username}",
                            "arn:aws:iam::371522382791:user/*/${aws:username}"
                        ],
                        "Effect": "Allow",
                        "Sid": "AllowUsersToCreateEnableResyncDeleteTheirOwnVirtualMFADevice"
                    },
                    {
                        "Condition": {
                            "Bool": {
                                "aws:MultiFactorAuthPresent": "true"
                            }
                        },
                        "Action": [
                            "iam:DeactivateMFADevice"
                        ],
                        "Resource": [
                            "arn:aws:iam::371522382791:mfa/${aws:username}",
                            "arn:aws:iam::371522382791:user/${aws:username}",
                            "arn:aws:iam::371522382791:mfa/*/${aws:username}",
                            "arn:aws:iam::371522382791:user/*/${aws:username}"
                        ],
                        "Effect": "Allow",
                        "Sid": "AllowUsersToDeactivateTheirOwnVirtualMFADevice"
                    },
                    {
                        "Action": [
                            "iam:ListMFADevices",
                            "iam:ListVirtualMFADevices",
                            "iam:ListUsers"
                        ],
                        "Resource": "*",
                        "Effect": "Allow",
                        "Sid": "AllowUsersToListMFADevicesandUsersForConsole"
                    }
                ]
            }
            '''
        }
        cls.client = boto3.client('iam')

    # http://boto3.readthedocs.io/en/latest/reference/services/iam.html#IAM.Client.simulate_custom_policy
    def test_infosec_role_assumption_policy_for_allowed_read_user(self):
        response = self.client.simulate_custom_policy(
            PolicyInputList=[self.policies['InfosecRoleAssumptionPolicy']],
            ActionNames=['sts:AssumeRole'],
            ResourceArns=['arn:aws:iam::371522382791:role/InfosecRead']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'


    # u'ContextKeyNames': ['aws:MultiFactorAuthPresent', 'aws:username']
    def test_self_manage_mfa_policy_create_mfa_for_allowed_user(self):
        response = self.client.simulate_custom_policy(
            PolicyInputList=[self.policies['SelfManageMFAPolicy']],
            ActionNames=["iam:CreateVirtualMFADevice"],
            CallerArn='arn:aws:iam::371522382791:user/path/to/jdoe',
            ResourceArns=[
                'arn:aws:iam::371522382791:mfa/jdoe'
                'arn:aws:iam::371522382791:user/jdoe'
                'arn:aws:iam::371522382791:mfa/path/to/jdoe'
                'arn:aws:iam::371522382791:user/path/to/jdoe'
            ],
            ContextEntries=[
                {
                    'ContextKeyName': 'aws:username',
                    'ContextKeyValues': ['jdoe'],
                    'ContextKeyType': 'string'
                },
            ],
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'


