ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PARENTDIR       := $(realpath ../)
AWS_REGION = us-west-2
S3_BUCKET_NAME  := public.us-west-2.infosec.mozilla.org
S3_BUCKET_TEMPLATE_PATH	:= infosec-security-roles/cf
S3_BUCKET_TEMPLATE_URI	:= s3://$(S3_BUCKET_NAME)/$(S3_BUCKET_TEMPLATE_PATH)
HTTP_BUCKET_TEMPLATE_URI	:= https://s3.amazonaws.com/$(S3_BUCKET_NAME)/$(S3_BUCKET_TEMPLATE_PATH)

all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]].*:' Makefile

.PHONY: cfn-lint test
test: cfn-lint
cfn-lint: ## Verify the CloudFormation templates pass linting tests
	-cfn-lint *.yml

.PHONY: upload-templates
upload-templates:
	AWS_REGION=$(AWS_REGION) aws s3 sync ./ $(S3_BUCKET_TEMPLATE_URI) --exclude="*" --include="*.yml"

.PHONY: create-individual-stacks
create-individual-stacks:
	AWS_REGION=us-west-2 aws cloudformation create-stack --stack-name guardduty-member-role \
	  --capabilities CAPABILITY_IAM \
	  --template-url $(HTTP_BUCKET_TEMPLATE_URI)/guardduty-member-account-role-mozilla.yml
	AWS_REGION=us-west-2 aws cloudformation create-stack --stack-name enterprise-information-security-audit-role \
	  --capabilities CAPABILITY_IAM \
	  --template-url $(HTTP_BUCKET_TEMPLATE_URI)/eis-security-audit-trusting-role.yml
	AWS_REGION=us-west-2 aws cloudformation create-stack --stack-name enterprise-information-security-incident-response-role \
	  --capabilities CAPABILITY_IAM \
	  --template-url $(HTTP_BUCKET_TEMPLATE_URI)/eis-incident-response-role-break-glass.yml

.PHONY: create-unified-stack
create-unified-stack:
	AWS_REGION=us-west-2 aws cloudformation create-stack --stack-name InfosecClientRoles \
	  --capabilities CAPABILITY_IAM \
	  --template-url $(HTTP_BUCKET_TEMPLATE_URI)/infosec-security-audit-incident-response-guardduty-roles-cloudformation.yml

.PHONY: create-old-unified-stack
create-old-unified-stack:
	AWS_REGION=us-west-2 aws cloudformation create-stack --stack-name InfosecClientRoles \
	  --capabilities CAPABILITY_IAM \
	  --template-url https://s3.amazonaws.com/infosec-cloudformation-templates/infosec-security-audit-incident-response-roles-cloudformation.json

.PHONY: update-unified-stack
update-unified-stack:
	AWS_REGION=us-west-2 aws cloudformation update-stack --stack-name InfosecClientRoles \
	  --capabilities CAPABILITY_IAM \
	  --template-url $(HTTP_BUCKET_TEMPLATE_URI)/infosec-security-audit-incident-response-guardduty-roles-cloudformation.yml
