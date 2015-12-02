import boto3
from cfnlambda import handler_decorator
import botocore.exceptions
import logging
import json

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)


def get_assume_role_policy_document(AssumeRolePolicyDocument=None,
                                    TrustedEntities=None):
    if AssumeRolePolicyDocument is not None:
        return AssumeRolePolicyDocument
    assume_role_policy_obj = json.loads('''{
      "Version":"2012-10-17",
      "Statement":[
        {
          "Effect":"Allow",
          "Principal":{
            "Service": "ec2.amazonaws.com"
          },
          "Action":[
            "sts:AssumeRole"
          ]
        }
      ]
    }''')
    if TrustedEntities is not None:
        (assume_role_policy_obj['Statement'][0]
         ['Principal']['AWS']) = TrustedEntities
        # Hopefully this is an array and not a comma delimited list
    return json.dumps(assume_role_policy_obj)


def create_iam_role(RoleName,
                    Path='/',
                    AssumeRolePolicyDocument=None,
                    TrustedEntities=None,
                    **kwargs):
    iam_client = boto3.client('iam')
    AssumeRolePolicyDocument = get_assume_role_policy_document(
        AssumeRolePolicyDocument,
        TrustedEntities)
    role = iam_client.create_role(
        Path=Path,
        RoleName=RoleName,
        AssumeRolePolicyDocument=AssumeRolePolicyDocument)
    return {'result': 'Role %s created or updated successfully' %
            RoleName,
            'Arn': role['Role']['Arn']}


def delete_iam_role(RoleName):
    try:
        iam_client = boto3.client('iam')
        iam_client.delete_role(RoleName=RoleName)
    except Exception as e:
        if (type(e) is botocore.exceptions.ClientError and
                'NoSuchEntity' in e.message):
            logger.info('Skipping deletion of Role %s as it does not '
                        'exist' % RoleName)
        else:
            raise

    return {'result': 'Role %s deleted successfully'
            % RoleName}


@handler_decorator()
def manage_iam_role(event, context):
    """Manage the creation and deletion of an IAM Role

    CloudFormation custom resource property inputs :
        RoleName : The name of the role to create.
        Path : The path of the role to create.
        AssumeRolePolicyDocument : The assume role policy document. Default : A
            policy allowing ec2 instances to assume the role
        TrustedEntities : A list of ARNs to trust.

    CloudFormation custom resource attribute outputs :
        result : String describing the result of the action.
        Arn : The ARN of the newly created IAM role
    """

    if 'RoleName' not in event['ResourceProperties']:
        raise ValueError('RoleName argument not present in ResourceProperties')

    if event['RequestType'] == 'Delete':
        result = delete_iam_role(event['ResourceProperties']['RoleName'])
    else:
        result = create_iam_role(**event['ResourceProperties'])
    return result
