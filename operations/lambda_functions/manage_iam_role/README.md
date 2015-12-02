Package manage_iam_role and upload to S3

dir="`mktemp --directory`"
pip install cfnlambda --no-deps -t "$dir"
cp manage_iam_role.py "$dir"
zip --junk-paths $dir/manage_iam_role.zip "$dir/manage_iam_role.py" "$dir/cfnlambda.py"
aws --profile infosec-prod --region us-west-2 s3 cp "$dir/manage_iam_role.zip" s3://infosec-lambda-us-west-2/
aws --profile infosec-prod --region us-east-1 s3 cp "$dir/manage_iam_role.zip" s3://infosec-lambda-us-east-1/
rm -rf "$dir"

