import boto3
from random import choice

PATH = '/eis/'

# List based on https://wiki.mozilla.org/Security/InfoSec#Members
USERS = ['gene',
         'jvehent',
         'gdestuynder',
         'jbryner',
         'ameihm',
         'jclaudius',
         'mpurzynski']
GROUP = 'Enterprise-Information-Security'

def make_random_password(length=16,
                         allowed_chars='abcdefghjkmnpqrstuvwxyz'
                         'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'):
    "Generates a random password with the given length and given allowed_chars"
    # Note that default value of allowed_chars does not have "I" or letters
    # that look like it -- just to avoid confusion.
    return ''.join([choice(allowed_chars) for i in range(length)])

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

response = client.create_group(
    Path=PATH,
    GroupName=GROUP
)
print(response)

response = client.attach_group_policy(
    GroupName=GROUP,
    PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
)
print(response)

for user in USERS:
    response = client.create_user(Path=PATH,
                                  UserName=user)
    response = client.add_user_to_group(GroupName=GROUP,
                                        UserName=user)
    password = make_random_password()
    print('%s : %s' % (user, password))
    response = client.create_login_profile(UserName=user,
                                           Password=password,
                                           PasswordResetRequired=True)
