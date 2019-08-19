STACK_NAME		:= SecurityAuditRoleCleaner
PROD_LAMBDA_CODE_STORAGE_S3_BUCKET_NAME	:= public.us-west-2.infosec.mozilla.org
LAMBDA_CODE_STORAGE_S3_PREFIX		:= security-audit-role-cleaner

LAMBDA_CODE_STORAGE_S3_PREFIX_ARG	:= $(if $(LAMBDA_CODE_STORAGE_S3_PREFIX),--s3-prefix $(LAMBDA_CODE_STORAGE_S3_PREFIX),"")

.PHONE: deploy
deploy:
	# Confirm that we have access to AWS
	aws sts get-caller-identity --output text >/dev/null
	# This tempfile is required because of https://github.com/aws/aws-cli/issues/2504
	$(eval TMPFILE := $(shell mktemp --suffix .yaml))
	aws cloudformation package --template clean-security-roles.yaml \
		--s3-bucket $(PROD_LAMBDA_CODE_STORAGE_S3_BUCKET_NAME) \
		$(LAMBDA_CODE_STORAGE_S3_PREFIX_ARG) \
		--output-template-file $(TMPFILE)
	aws cloudformation deploy --template-file $(TMPFILE) --stack-name $(STACK_NAME) \
	 	--capabilities CAPABILITY_IAM
	rm $(TMPFILE)
