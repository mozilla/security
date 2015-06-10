#ipquery

####Table of Contents

1. [Overview](#overview)
2. [Module Description - What the module does and why it is useful](#module-description)
3. [Setup - The basics of getting started with the ipquery module](#setup)
    * [What the ipquery module affects](#what-the-ipquery-module-affects)
    * [Setup requirements](#setup-requirements)
    * [Beginning with the ipquery module](#beginning-with-the-ipquery-module)
4. [Usage - Configuration options and additional functionality](#usage)
5. [Reference - An under-the-hood peek at what the module is doing and how](#reference)
5. [Limitations - OS compatibility, etc.](#limitations)
6. [Development - Guide for contributing to the module](#development)

##Overview

Installs and configures the ipquery website.

##Module Description

The ipquery module deploys the [ipquery] [1] and [ip2instance] [2] packages, configures
them and serves the ipquery website using Apache httpd and mod_wsgi.

##Setup

###What the IPQuery module affects

* Creates a python virtual environement
* Installs the ipquery and ip2instance pypi packages into that virtual
  enviroinment
* Creates an ipquery configuration file so that ipquery can both
  * call ip2instance with the list of [AWS IAM Roles] [3] of the accounts to
    scan
  * integrate with your [SAML identity provider] [4] for authentication
* Installs and configures Apache httpd to serve the ipquery website using
   mod_wsgi over HTTPS

###Setup Requirements

In order to maintain backwards compatibility with Puppet 3.x and
[stringified facts] [5] the `$ip2instance_roles` parameter is a JSON encoded
list instead of a list.

###Beginning with the IPQuery module

Include the module [as you would any other] [6], passing in all of the
parameters to configure it or using hiera to override the parameter defaults
with your settings.

##Usage

To use the ipquery module you'll need to pass in the following configuration
parameters to override the defaults.

###SAML configuration

* `$idp_name` The name of the identity provider. This value is used to identify
  the SAML provider in the case where you are using multiple providers. Example
  : `oktadev`
* `$saml_url` The URL configured with your SAML provider. This URL will be
  hosted by your SAML provider and provide the SAML metadata needed to
  use them as an identity provider. Example : 
  `http://idp.oktadev.com/metadata`

###IP2Instance configuration

* `$ip2instance_roles` A JSON encoded list of [AWS IAM Role] [3] [ARNs] [7]
  that ipquery [assumes] [8] in order to gather information about AWS ec2
  instances. Note: This is JSON encoded to work around Puppet 3.x
  [stringified facts] [5]. Example : 

~~~
    "[\"arn:aws:iam::012345678901:role/MyRole\",
      \"arn:aws:iam::123456789010:role/MyRole\"]"
~~~

###Other configuration
* `$flask_secret_key` Session secret which Flask [sessions] [9] require for
  security. Example : `11111111-1111-1111-1111-111111111111`
* `$tls_cert_filename` The filename of the SSL/TLS certificate used by
  Apache. Example : `/etc/pki/tls/certs/cert.crt`
* `$tls_certificate` The SSL/TLS certificate. Example :
~~~
    "-----BEGIN CERTIFICATE-----\n
    MIIChDCCAe2gAwIBAgIJALrQYmKb2JKTMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\n
    .
    .
    .
    rCCZOCHlYGwXp98AxJJHDVjBx9uYFWSQ\n
    -----END CERTIFICATE-----"
~~~
* `$tls_certificate_key` The SSL/TLS certificate private key. Example :
~~~
    "-----BEGIN RSA PRIVATE KEY-----\n
    MIICXQIBAAKBgQC1WR2q2F3ZwljUsVJLWCCL5rfTTJi10gOrkTHWjtsx1xMe7hy5\n
    .
    .
    .
    ad5fe0sb4By15wbr459Rwq+xalIhLv1qAHVROI173FYV\n
    -----END RSA PRIVATE KEY-----"
~~~
* `$tls_key_filename` The filename of the SSL/TLS private key used by Apache
  Example : `/etc/pki/tls/private/cert.key`
* `$username` The user to run Flask as. Example : `ipqueryuser`
* `$virtualenv_dir` The directory path to create the virtual environment in.
  Example : `/opt/ipquery/venv`
* `$wsgi_filename` The filename of the [WSGI] [10] file. Example : 
  `/opt/ipquery/ipquery.wsgi`

##Reference

###Class: ipquery

Installs and configures ipquery.

Include the `ipquery` class to install ipquery:

~~~puppet
  class { 'ipquery': }
~~~

##Limitations

IPQuery expects to run on RHEL/CentOS 7.

##Development

Feel free to [fork this module] [11] and contribut pull requests.

[1]: https://github.com/mozilla/security/tree/master/operations/ipquery "IPQuery"
[2]: https://github.com/mozilla/security/tree/master/operations/ip2instance "ip2instance"
[3]: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html "IAM Roles"
[4]: https://en.wikipedia.org/wiki/Security_Assertion_Markup_Language "SAML"
[5]: https://docs.puppetlabs.com/puppet/latest/reference/lang_facts_and_builtin_vars.html#handling-boolean-facts-in-older-puppet-versions "stringifying facts"
[6]: https://docs.puppetlabs.com/puppet/latest/reference/modules_fundamentals.html#using-modules "Using Modules"
[7]: http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html "ARNs"
[8]: http://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html "AssumeRole"
[9]: http://flask.pocoo.org/docs/quickstart/#sessions "Flask sessions" 
[10]: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/#creating-a-wsgi-file "Flask WSGI file"
[11]: https://github.com/mozilla/security/tree/master/operations/ipquery/puppet/modules/ipquery "IPQuery module"
