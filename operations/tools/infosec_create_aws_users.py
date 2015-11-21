import boto3
import botocore
import sys
from random import choice

PATH = '/eis/'

# List based on https://wiki.mozilla.org/Security/InfoSec#Members
USERS = ['gene',
         'jvehent',
         'gdestuynder',
         'jbryner',
         'ameihm',
         'jclaudius',
         'mpurzynski',
         'asmith',
         'apking',
         'amuntner']
GROUP = 'Enterprise-Information-Security'

def make_random_password(length=16,
                         allowed_chars='abcdefghjkmnpqrstuvwxyz'
                         'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'):
    "Generates a random password with the given length and given allowed_chars"
    # Note that default value of allowed_chars does not have "I" or letters
    # that look like it -- just to avoid confusion.
    return ''.join([choice(allowed_chars) for i in range(length)])

if len(sys.argv) > 1:
    boto3.setup_default_session(profile_name=sys.argv[1])

client = boto3.client('iam')

response = client.update_account_password_policy(
    MinimumPasswordLength=16,
    RequireSymbols=False,
    RequireNumbers=False,
    RequireUppercaseCharacters=False,
    RequireLowercaseCharacters=False,
    AllowUsersToChangePassword=True,
    PasswordReusePrevention=6
)
print(response)

try:
    response = client.create_group(
        Path=PATH,
        GroupName=GROUP
    )
    print(response)
except botocore.exceptions.ClientError as e:
    if '(EntityAlreadyExists)' in e.message:
        print("Group %s already exists, skipping" % GROUP)
    else:
        raise

response = client.attach_group_policy(
    GroupName=GROUP,
    PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
)
print(response)

for user in USERS:
    try:
        response = client.create_user(Path=PATH,
                                      UserName=user)
    except botocore.exceptions.ClientError as e:
        if '(EntityAlreadyExists)' in e.message:
            print("User %s already exists, skipping" % user)
        else:
            raise

    response = client.add_user_to_group(GroupName=GROUP,
                                        UserName=user)
    password = make_random_password()

    try:
        response = client.create_login_profile(UserName=user,
                                               Password=password,
                                               PasswordResetRequired=True)
        print('%s : %s' % (user, password))
    except botocore.exceptions.ClientError as e:
        if '(EntityAlreadyExists)' in e.message:
            print("Password for user %s already set, skipping" % user)
        else:
            raise
