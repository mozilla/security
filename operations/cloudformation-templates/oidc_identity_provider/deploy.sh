#!/bin/bash -e

TEMPLATE_FILENAME=$1
S3_BUCKET=$2
S3_PREFIX=$3
STACK_NAME=$4
PARAMETERS=$5

TARGET_PATH="`dirname \"${TEMPLATE_FILENAME}\"`"

# This tempfile is required because of https://github.com/aws/aws-cli/issues/2504
TMPFILE=$(mktemp --suffix .yaml)
TMPDIR=$(mktemp --directory)
ln --verbose --no-dereference --force --symbolic $TMPDIR "${TARGET_PATH}/build"
trap "{ rm --verbose --force $TMPFILE;rm --force --recursive $TMPDIR;rm --verbose --force build; }" EXIT

pip install --target "${TARGET_PATH}/build/" -r "${TARGET_PATH}/requirements.txt"
cp --verbose "${TARGET_PATH}/"*.py "${TARGET_PATH}/build/"

aws cloudformation package \
  --template $TEMPLATE_FILENAME \
  --s3-bucket $S3_BUCKET \
  --s3-prefix $S3_PREFIX \
  --output-template-file $TMPFILE

if [ "$(aws cloudformation describe-stacks --query "length(Stacks[?StackName=='${STACK_NAME}'])")" = "1" ]; then
  # Stack already exists, it will be updated
  wait_verb=stack-update-complete
else
  # Stack doesn't exist it will be created
  wait_verb=stack-create-complete
fi

aws cloudformation deploy --template-file $TMPFILE --stack-name $STACK_NAME \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides $PARAMETERS

echo "Waiting for stack to reach a COMPLETE state"
aws cloudformation wait $wait_verb --stack-name  $STACK_NAME
