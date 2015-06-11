Overview
========

Web application to allow SAML authenticated users to search multiple AWS accounts for instances by IP

Configuration
=============
The ipquery configuration file is located at `/etc/ipquery.yaml`. To configure
ipquery create this file and populate it with your configuration settings.

secret_key
----------
A unique secret key to secure Flask sessions

metadata_url_for
----------------
A dictionary of all SAML identity providers with the name of the identity
provider as the key and the identity providers SAML metadata URL as the
value.

idp_name
--------
The name of the preferred SAML identity provider.

acs_url_scheme
--------------
Set this to `http` or `https` depending on how you're serving up the web UI.

PREFERRED_URL_SCHEME
--------------------
Set this to `http` or `https` depending on how you're serving up the web UI.

loglevel
--------
The `level <https://docs.python.org/2/library/logging.html#levels>`_ to set for logging.

ip2instance_role_session_name
-----------------------------
A session name to identify the IAM role assumption

ip2instance_roles
-----------------
A list of all AWS IAM Role ARNs to assume and use to scan for instances.

ip2instance_policy
------------------
The IAM Policy to constrain the access that ipquery will use when assuming
roles to scan for instances.

Example Configuration
---------------------
Here is an example configuration for two foreign AWS accounts

::

    --- 
      secret_key: "11111111-1111-1111-1111-111111111111"
      idp_name: oktadev
      metadata_url_for: 
        oktadev: "http://idp.oktadev.com/metadata"
      PREFERRED_URL_SCHEME: https
      acs_url_scheme: https
      ip2instance_roles: 
        - "arn:aws:iam::012345678901:role/MyIPQueryRole"
        - "arn:aws:iam::123456789012:role/MyIPQueryRole"

Usage
=====

::

    ipquery
