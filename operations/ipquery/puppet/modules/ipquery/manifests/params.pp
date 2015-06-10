# # Class: params
#
# This class manages ipquery parameters
#
# ## Parameters
# @param flask_secret_key Session secret which Flask [sessions] [1] require for
#        security
# @param idp_name The name of the identity provider
# @param ip2instance_roles A JSON encoded list of [AWS IAM Role] [2] [ARNs] [3]
#        that ipquery [assumes] [4] in order to gather information about AWS ec2
#        instances. Note This is JSON encoded to work around Puppet 3.x
#        [stringified facts] [5]
# @param saml_url The URL configured with your SAML provider
# @param tls_cert_filename The filename of the SSL/TLS certificate used by
#        Apache
# @param tls_certificate The SSL/TLS certificate
# @param tls_certificate_key The SSL/TLS certificate private key
# @param tls_key_filename The filename of the SSL/TLS private key used by Apache
# @param username The user to run Flask as
# @param virtualenv_dir The directory path to create the virtual environment in
# @param wsgi_filename The filename of the [WSGI] [6] file
#
# [1]: http://flask.pocoo.org/docs/quickstart/#sessions "Flask sessions" 
# [2]: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html "IAM Roles"
# [3]: http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html "ARNs"
# [4]: http://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html "AssumeRole"
# [5]: https://docs.puppetlabs.com/puppet/latest/reference/lang_facts_and_builtin_vars.html#handling-boolean-facts-in-older-puppet-versions "stringifying facts"
# [6]: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/#creating-a-wsgi-file "Flask WSGI file"
#
class ipquery::params {
  $flask_secret_key = '11111111-1111-1111-1111-111111111111'
  $idp_name = 'example'
  $install_dir = '/opt/ipquery'
  $ip2instance_roles = '[]'
  $saml_url = 'http://idp.oktadev.com/metadata'
  $tls_cert_filename = '/etc/pki/tls/certs/cert.crt'
  $tls_certificate = '-----BEGIN CERTIFICATE-----
MIIChDCCAe2gAwIBAgIJALrQYmKb2JKTMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQxFDASBgNVBAMMC2V4YW1wbGUuY29tMB4XDTE1MDYwOTIz
MzMwMloXDTIwMDYwNzIzMzMwMlowWzELMAkGA1UEBhMCQVUxEzARBgNVBAgMClNv
bWUtU3RhdGUxITAfBgNVBAoMGEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDEUMBIG
A1UEAwwLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBALVZ
HarYXdnCWNSxUktYIIvmt9NMmLXSA6uRMdaO2zHXEx7uHLlfDOgBb+saBw+ehbpc
vBS1XahLzLGMn6DgpHtVsDfocLPA5TkxXp5ajdG2koIm+dwcAtoaOWn5ltIJrk0S
utKBLafWwjb4qORNqAYk6r7Uc5caD77aC/A2MtzVAgMBAAGjUDBOMB0GA1UdDgQW
BBSmxoosLPU6aVnTeUpjhH1i3T5eQDAfBgNVHSMEGDAWgBSmxoosLPU6aVnTeUpj
hH1i3T5eQDAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBBQUAA4GBAJ1pnYz7Tcwr
FLwVumoWGtHIZt/6tRB1Y32owabl8VzQGstgm2G1O+kPQULSluedujFRcAXL9uWK
PmVu569MF2cacdfFLkN9UtiPDnbDlkDLsJLcUE+YZ+mgzFATt7Ra42q7msvzfRDy
rCCZOCHlYGwXp98AxJJHDVjBx9uYFWSQ
-----END CERTIFICATE-----'
  $tls_certificate_key = '-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQC1WR2q2F3ZwljUsVJLWCCL5rfTTJi10gOrkTHWjtsx1xMe7hy5
XwzoAW/rGgcPnoW6XLwUtV2oS8yxjJ+g4KR7VbA36HCzwOU5MV6eWo3RtpKCJvnc
HALaGjlp+ZbSCa5NErrSgS2n1sI2+KjkTagGJOq+1HOXGg++2gvwNjLc1QIDAQAB
AoGBAJonJ6XbiGOb5eDe3qJ3RitGMwqleMZNwJrtsFy/UKpcNb+8DqSwnIr29cj2
dfwb93cEb0h3JybxUA25CNQ7QPS6cW1YuATG30uxU4aXQh54eQLp/RuD0DjwUwDf
XE72VEC3fJBNaybhlCGV2pRSqNV7S1aMfue6QzX0M+dU7NdBAkEA7Ex75E2US4f+
eeNlxCXCXcbpYy5HyRkpgsOdnveeOgAbUi6zYQM4nndLPcmT9HqzNTiJa70ShC5i
ovs4HXuKhQJBAMR3xonrMOz7+xncfFd7+QByw1hOaPs2bZEKb+runfSQ5PrCaVlh
PcaPCUvW+PoGoFDsqpAE5igojxVQPNQFIhECQAs2nfJ5k/35mCPknKGwQQb+N3kT
ayip3wRrkAFJMuMBukouGSkTZA5xDssB09mYMQTnh+3q7QQEx32Aems7v5kCQQC4
OMeF028RCEYvvbsqHSki7nmVeBCgXizm76550D10cdkD+P/nu3K9mKnS30SezU/O
EdztJmraBQ4FojMna5jBAkA7FJSajrnE1xKMkJWNhpo1KKg7ZNxKe3UdmSXdarqh
ad5fe0sb4By15wbr459Rwq+xalIhLv1qAHVROI173FYV
-----END RSA PRIVATE KEY-----'
  $tls_key_filename = '/etc/pki/tls/private/cert.key'
  $username = 'ipqueryuser'
  $virtualenv_dir = '/opt/ipquery/venv'
  $wsgi_filename = '/opt/ipquery/ipquery.wsgi'
}