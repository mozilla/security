import boto3
from cfnlambda import handler_decorator, RequestType
import botocore.exceptions
import logging
import json

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)


def get_assume_role_policy_document(AssumeRolePolicyDocument=None,
                                    TrustedEntities=[]):
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
    # We are assuming that we also want to permit the ec2 service to assume
    # this role (to enable ec2 instances to have this role assigned to them).
    # Alternatives could be lambda, other AWS services or no services.
    aws_entities = [x for x in TrustedEntities if len(x) > 0]
    if len(aws_entities) > 0:
        (assume_role_policy_obj['Statement'][0]
         ['Principal']['AWS']) = aws_entities
        # The TrustedEntities is a "CommaDelimitedList"
    return json.dumps(assume_role_policy_obj)


def create_iam_role(RoleName,
                    Path='/',
                    AssumeRolePolicyDocument=None,
                    TrustedEntities=[],
                    **kwargs):
    iam_client = boto3.client('iam')

    AssumeRolePolicyDocument = get_assume_role_policy_document(
        AssumeRolePolicyDocument,
        TrustedEntities)
    try:
        role = iam_client.create_role(
            Path=Path,
            RoleName=RoleName,
            AssumeRolePolicyDocument=AssumeRolePolicyDocument)
    except botocore.exceptions.ClientError as e:
        if 'EntityAlreadyExists' in e.message:
            # Since we don't compare the existing AssumeRolePolicyDocument with
            # the new one (because it's difficult to do a deep comparison
            # ignoring list order) this update_assume_role_policy call could
            # be unnecessary.
            iam_client.update_assume_role_policy(
                RoleName=RoleName,
                PolicyDocument=AssumeRolePolicyDocument)
            response = iam_client.get_role(RoleName=RoleName)
            arn = response['Role']['Arn']
            return {'result': 'Role %s already exists and was updated '
                    'successfully' % RoleName,
                    'Arn': arn}
        else:
            raise
    return {'result': 'Role %s created successfully' % RoleName,
            'Arn': role['Role']['Arn']}


def update_iam_role(old, new):
    iam_client = boto3.client('iam')
    # http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref-requests.html

    if old['RoleName'] != new['RoleName']:
        raise ValueError(
            'RoleName can not be updated. To update the RoleName delete %s '
            'and then create %s' % (old['RoleName'], new['RoleName']))

    response = iam_client.get_role(RoleName=new['RoleName'])
    arn = response['Role']['Arn']

    # TODO : Since the IAM Role that this lambda function creates could have
    # been changed by something other than the CloudFormaiton stack that
    # spawned it, we should compare the new values against the real current
    # values instead of the old values reported by CloudFormation
    # response['Role']['AssumeRolePolicyDocument']

    if (
        (
            'AssumeRolePolicyDocument' in new and
            'AssumeRolePolicyDocument' in old and
            new['AssumeRolePolicyDocument'] == old['AssumeRolePolicyDocument']
        ) and (
            (
                new['TrustedEntities'] is None and
                old['TrustedEntities'] is None
            ) or (
                new['TrustedEntities'] is not None and
                old['TrustedEntities'] is not None and
                set(new['TrustedEntities']) == set(old['TrustedEntities'])))):
        return {'result': 'Role %s was not updated as there were no '
                'changes' % new['RoleName'],
                'Arn': arn}

    AssumeRolePolicyDocument = get_assume_role_policy_document(
        AssumeRolePolicyDocument=(new['AssumeRolePolicyDocument']
                                  if 'AssumeRolePolicyDocument' in new
                                  else None),
        TrustedEntities=new['TrustedEntities'])

    iam_client.update_assume_role_policy(
        RoleName=new['RoleName'],
        PolicyDocument=AssumeRolePolicyDocument)

    return {'result': 'Role %s updated successfully' % new['RoleName'],
            'Arn': arn}


def delete_iam_role(RoleName):
    try:
        iam_client = boto3.client('iam')
        iam_client.delete_role(RoleName=RoleName)
    except botocore.exceptions.ClientError as e:
        if 'NoSuchEntity' in e.message:
            logger.info('Skipping deletion of Role %s as it does not exist'
                        % RoleName)
            return {'result': 'Skipping deletion of Role %s as it does not '
                    'exist' % RoleName}
        else:
            raise

    return {'result': 'Role %s deleted successfully' % RoleName}


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

    if event['RequestType'] == RequestType.DELETE:
        result = delete_iam_role(event['ResourceProperties']['RoleName'])
    elif event['RequestType'] == RequestType.UPDATE:
        result = update_iam_role(event['OldResourceProperties'],
                                 event['ResourceProperties'])
    elif event['RequestType'] == RequestType.CREATE:
        result = create_iam_role(**event['ResourceProperties'])
    return result
