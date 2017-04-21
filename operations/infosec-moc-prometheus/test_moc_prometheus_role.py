import boto3

class TestInfosecPolicies():
    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.policies = {
            'ControlMOCPrometheusInstance':'''
            {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Action": [
                    "ec2:StopInstances",
                    "ec2:StartInstances",
                    "ec2:RebootInstances"
                  ],
                  "Resource": "*",
                  "Condition": {
                    "StringEquals" : {
                      "ec2:ResourceTag/TechnicalContact" : "moc@mozilla.com"
                    }
                  }
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "ec2:DescribeInstances"
                  ],
                  "Resource": "*"
                }
              ]
            }
            '''
        }
        cls.client = boto3.client('iam')

    # http://boto3.readthedocs.io/en/latest/reference/services/iam.html#IAM.Client.simulate_custom_policy
    def test_stop_instance_for_allowed_instance(self):
        response = self.client.simulate_custom_policy(
            PolicyInputList=[self.policies['ControlMOCPrometheusInstance']],
            ActionNames=['ec2:StopInstances'],
            ContextEntries=[
                {
                    'ContextKeyName': 'ec2:ResourceTag/TechnicalContact',
                    'ContextKeyValues': [
                        'moc@mozilla.com',
                    ],
                    'ContextKeyType': 'string'
                }
            ]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'

    def test_stop_instance_for_prohibited_instance(self):
        response = self.client.simulate_custom_policy(
            PolicyInputList=[self.policies['ControlMOCPrometheusInstance']],
            ActionNames=['ec2:StopInstances']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'implicitDeny'

    def test_terminate_instance(self):
        response = self.client.simulate_custom_policy(
            PolicyInputList=[self.policies['ControlMOCPrometheusInstance']],
            ActionNames=['ec2:TerminateInstances'],
            ContextEntries=[
                {
                    'ContextKeyName': 'ec2:ResourceTag/TechnicalContact',
                    'ContextKeyValues': [
                        'moc@mozilla.com',
                    ],
                    'ContextKeyType': 'string'
                }
            ]
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'implicitDeny'

    def test_describe_instances(self):
        response = self.client.simulate_custom_policy(
            PolicyInputList=[self.policies['ControlMOCPrometheusInstance']],
            ActionNames=['ec2:DescribeInstances']
        )
        assert response['EvaluationResults'][0]['EvalDecision'] == 'allowed'
