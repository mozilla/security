Package publish_to_sns and upload to S3

    dir="`mktemp --directory`"
    pip install cfnlambda --no-deps -t "$dir"
    cp -v publish_to_sns.py "$dir"
    zip --junk-paths $dir/publish_to_sns.zip "$dir/publish_to_sns.py" "$dir/cfnlambda.py"
    aws --profile infosec-prod --region us-west-2 s3 cp "$dir/publish_to_sns.zip" s3://infosec-lambda-us-west-2/
    aws --profile infosec-prod --region us-east-1 s3 cp "$dir/publish_to_sns.zip" s3://infosec-lambda-us-east-1/
    rm -rf "$dir"
    
