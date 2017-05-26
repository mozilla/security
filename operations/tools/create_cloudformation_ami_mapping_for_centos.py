import boto3
import dateutil.parser
import json

client = boto3.client('ec2')
response = client.describe_regions()
region_list = [x['RegionName'] for x in response['Regions']]

# https://wiki.centos.org/Cloud/AWS#head-224024c7b3b083bd574bec6861bcdfd3487a5418
CENTOSORG_CENTOS_7_PRODUCT_CODE = "aw0evgkw8e5c1q413zgy5pjce"

amis = []

RegionMap = {}
for region in region_list:
    RegionMap[region] = {}

for region_name in region_list:
    client = boto3.client('ec2', region_name=region_name)
    response = client.describe_images(
        Owners=['aws-marketplace'],
        Filters=[
            {
                'Name': 'product-code',
                'Values': [
                    CENTOSORG_CENTOS_7_PRODUCT_CODE
                ]
            }
        ]
    )
    for image in response['Images']:
        image[u'Region'] = region_name
        amis.append(image)

for region in region_list:
    regional_ami_list = [x for x in amis if x['Region'] == region]
    if len(regional_ami_list) == 0:
        continue
    regional_ami_list.sort(
        reverse=True,
        key=lambda x: dateutil.parser.parse(x['CreationDate']))
    newest_ami = regional_ami_list[0]
    RegionMap[region]['CentOS7x8664EBSHVM'] = newest_ami[u'ImageId']

print(json.dumps({"Mappings": {"RegionMap": RegionMap}},
                 sort_keys=True,
                 indent = 2,
                 separators = (',', ': ')))
