import boto3
import json
import botocore.exceptions

TRUSTED_ACCOUNT = 'arn:aws:iam::371522382791:root'
S3_BUCKET = 'infosec-internal-data'
S3_KEY = 'iam-roles/roles.json'
ROLE_TYPE = 'InfosecSecurityAuditRole'

def role_arn_to_session(**args):
    """
    Usage :
    session = role_arn_to_session(
        RoleArn='arn:aws:iam::012345678901:role/example-role',
        RoleSessionName='ExampleSessionName')
    client = session.client('sqs')
    """
    client = boto3.client('sts')
    response = client.assume_role(**args)
    return boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken'])


client_s3 = boto3.client('s3')
response = client_s3.get_object(
    Bucket=S3_BUCKET,
    Key=S3_KEY
)
roles = json.load(response['Body'])

# Iterate over all accounts that trust the TRUSTED_ACCOUNT account
for role in [x for x in roles
             if x['TrustedEntity'] == TRUSTED_ACCOUNT]:
    # print(role['Arn'])
    try:
        session = role_arn_to_session(
            RoleArn=role['Arn'],
            RoleSessionName='TestingAccess',
            DurationSeconds=900
        )
        exception = False
    except botocore.exceptions.ClientError:
        exception = True
    if not exception:
        if role['Type'] == ROLE_TYPE:
            client_iam = session.client('iam')
            response_iam = client_iam.list_account_aliases()
            alias = (response_iam['AccountAliases'][0]
                     if len(response_iam['AccountAliases']) > 0
                     else None)
        else:
            alias = None
        print "SUCCESS %s \"%s\" %s" % (
            role['Arn'],
            alias,
            session.get_credentials().access_key)
    else:
        print "FAILURE %s" % role['Arn']
