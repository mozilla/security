TEMPLATE_FILENAME	:= oidc_identity_provider.yml
# S3_BUCKET			:=
S3_PREFIX			:= oidc-identity-provider
STACK_NAME			:= OIDCIdentityProvider
URL					:= https://example.com/
CLIENT_ID_LIST		:= id1,id2
THUMBPRINT_LIST		:= 1234567890abcdef1234567890abcdef12345678,234567890abcdef1234567890abcdef123456789
PARAMETERS			:= "Url=$(URL)" "ClientIDList=$(CLIENT_ID_LIST)" "ThumbprintList=$(THUMBPRINT_LIST)"

# For example call
# make S3_BUCKET=public.us-west-2.security.allizom.org deploy-cloudformation-stack

ifndef S3_BUCKET
$(error S3_BUCKET is not set)
endif


.PHONE: deploy-cloudformation-stack
deploy-cloudformation-stack:
	./deploy.sh \
		"$(TEMPLATE_FILENAME)" \
		"$(S3_BUCKET)" \
		"$(S3_PREFIX)" \
		"$(STACK_NAME)" \
		"$(PARAMETERS)"
