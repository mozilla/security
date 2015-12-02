Package configure_cloudtrail_to_use_mozilla_secure_storage and upload to S3

dir="`mktemp --directory`"
pip install cfnlambda --no-deps -t "$dir"
cp -v configure_cloudtrail_to_use_mozilla_secure_storage.py "$dir"
zip --junk-paths $dir/configure_cloudtrail_to_use_mozilla_secure_storage.zip "$dir/configure_cloudtrail_to_use_mozilla_secure_storage.py" "$dir/cfnlambda.py"
aws --profile infosec-prod --region us-west-2 s3 cp "$dir/configure_cloudtrail_to_use_mozilla_secure_storage.zip" s3://infosec-lambda-us-west-2/
aws --profile infosec-prod --region us-east-1 s3 cp "$dir/configure_cloudtrail_to_use_mozilla_secure_storage.zip" s3://infosec-lambda-us-east-1/
rm -rf "$dir"
