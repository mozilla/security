# RoleName argument in CloudFormation makes `manage_iam_role` unnecessary

With the addition of the `RoleName` argument to the `AWS::IAM::Role` CloudFormation object around [August 2016](http://web.archive.org/web/20160822015322/http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iam-role.html), this `manage_iam_role` code should no longer be necessary.

# Package manage_iam_role and upload to S3

dir="`mktemp --directory`"
pip install cfnlambda --no-deps -t "$dir"
cp manage_iam_role.py "$dir"
zip --junk-paths $dir/manage_iam_role.zip "$dir/manage_iam_role.py" "$dir/cfnlambda.py"
aws --profile infosec-prod --region us-west-2 s3 cp "$dir/manage_iam_role.zip" s3://infosec-lambda-us-west-2/
aws --profile infosec-prod --region us-east-1 s3 cp "$dir/manage_iam_role.zip" s3://infosec-lambda-us-east-1/
rm -rf "$dir"

# Package for testing
dir="`mktemp --directory`"
# pip install cfnlambda --no-deps -t "$dir"
cp -v /home/gene/code/github.com/gene1wood/cfnlambda/cfnlambda.py "$dir"
cp -v manage_iam_role.py "$dir"
zip --junk-paths $dir/manage_iam_role_dev.zip "$dir/manage_iam_role.py" "$dir/cfnlambda.py"
aws --profile infosec-prod --region us-west-2 s3 cp "$dir/manage_iam_role_dev.zip" s3://infosec-lambda-us-west-2/
aws --profile infosec-prod --region us-east-1 s3 cp "$dir/manage_iam_role_dev.zip" s3://infosec-lambda-us-east-1/
rm -rf "$dir"
