import boto3
import dateutil.parser
import json

client = boto3.client('ec2')
response = client.describe_regions()
region_list = [x['RegionName'] for x in response['Regions']]

AMAZON_LINUX_NAME_PREFIX="amzn-ami-"

amis = []

RegionMap = {}
for region in region_list:
    RegionMap[region] = {}

for region_name in region_list:
    client = boto3.client('ec2', region_name=region_name)
    response = client.describe_images(
        Owners=['amazon'],
    )
    for image in response['Images']:
        image[u'Region'] = region_name
        amis.append(image)

for hardware in [
        ('hvm', 'ebs'),
        ('hvm', 's3'),
        ('hvm', 'gp2'),
        ('pv', 'ebs'),
        ('pv', 's3')]:
    ami_list = [x for x
                in amis
                if 'Name' in x
                and x['Name'].startswith(
                    AMAZON_LINUX_NAME_PREFIX +
                    hardware[0])
                and x['Name'].endswith(hardware[1])
                and '-beta' not in x['Name']
                and '.rc' not in x['Name']]
    for region in region_list:
        regional_ami_list = [x for x in ami_list if x['Region'] == region]
        if len(regional_ami_list) == 0:
            continue
        regional_ami_list.sort(
            reverse=True,
            key=lambda x: dateutil.parser.parse(x['CreationDate']))
        newest_ami = regional_ami_list[0]
        RegionMap[region][''.join(hardware)] = newest_ami[u'ImageId']

print(json.dumps({"Mappings": {"RegionMap": RegionMap}},
           sort_keys=True,
           indent = 2,
           separators = (',', ': ')))