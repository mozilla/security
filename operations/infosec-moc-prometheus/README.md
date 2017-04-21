# To use the IAM Role

* Configure the role in your awscli config : http://docs.aws.amazon.com/cli/latest/userguide/cli-roles.html
  * The `role_arn` is `arn:aws:iam::371522382791:role/MOCPrometheusAdmin`
  * An example config block would be

        [profile infosec-prod-prometheus]
        role_arn = arn:aws:iam::371522382791:role/MOCPrometheusAdmin
        source_profile = default
* Search for instances you can administer in `us-west-2`

        AWS_DEFAULT_PROFILE="infosec-prod-prometheus" aws --region us-west-2 ec2 describe-instances --filters Name=tag:TechnicalContact,Values=moc@mozilla.com
* Perform the action you'd like to take using the instance id discovered above

        AWS_DEFAULT_PROFILE="infosec-prod-prometheus" aws --region us-west-2 ec2 reboot-instances --instance-ids i-012345689
