Overview
========
ip2instance iterates through multiple AWS accounts, assuming IAM Roles in each account using the STS AssumeRole function and fetches information about instances in those accounts.

Configuration
=============
The ip2instance configuration file is located at `/etc/ip2instance.yaml` . To configure ip2instance create this file and populate it with your `role_session_name` and `roles`

role_session_name
-----------------
The `role_session_name` is an "identifier for the assumed role session. The session name is included as part of the AssumedRoleUser" according to the `AWS Documentation <http://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html>`_

roles
-----
The roles is a list of `ARNs <http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html>`_ of all IAM Roles in foreign AWS accounts which ip2instance should assume when searching for instances.

Example Configuration
---------------------
Here is an example configuration for two foreign AWS accounts

::

    role_session_name: ip2instance
    roles:
    - arn:aws:iam::123456789012:role/security-audit-role-SecurityAuditRole-12XHTR13TAWGH  # 293989542403 Finance
    - arn:aws:iam::345678901234:role/security-audit-role-SecurityAuditRole-FLGUX9CF36X6   # 345678901234 Client Frontend Development Team
 

Usage
=====

::

    ip2instance > instance-list.txt

How to Build
============
Here's how to build this into an RPM on a `RHEL 6 derivative <https://en.wikipedia.org/wiki/Red_Hat_Enterprise_Linux_derivatives>`_

::

    sudo yum install http://ftp.linux.ncsu.edu/pub/epel/6/i386/epel-release-6-8.noarch.rpm
    sudo yum install rubygems ruby-devel gcc python-setuptools rpm-build
    sudo easy_install pip
    sudo gem install fpm
    git clone https://github.com/mozilla/security.git
    
    cd security/operations/ip2instance # This is required
    fpm -s python -t rpm --workdir ../ ./setup.py
