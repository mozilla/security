# # Class: ipquery
#
# Installs and configures the ipquery tool with Apache mod_wsgi.
#
# ## Parameters
#
# See params.pp
class ipquery (
  $flask_secret_key = $ipquery::params::flask_secret_key,
  $idp_name = $ipquery::params::idp_name,
  $install_dir = $ipquery::params::install_dir,
  $ip2instance_roles = $ipquery::params::ip2instance_roles,
  $saml_url = $ipquery::params::saml_url,
  $tls_cert_filename = $ipquery::params::tls_cert_filename,
  $tls_certificate = $ipquery::params::tls_certificate,
  $tls_certificate_key = $ipquery::params::tls_certificate_key,
  $tls_key_filename = $ipquery::params::tls_key_filename,
  $username = $ipquery::params::username,
  $virtualenv_dir = $ipquery::params::virtualenv_dir,
  $wsgi_filename = $ipquery::params::wsgi_filename,
) inherits ipquery::params {

  include 'epel' # Workaround for bug https://github.com/stankevich/puppet-python/issues/196
  include 'python'
  include 'apache'
  include 'apache::mod::ssl'
  include 'apache::mod::wsgi'

  $docroot = "${install_dir}/docroot"

  file { [ $install_dir, $docroot ]:
      ensure => 'directory',
  }

  user { $username:
    comment => 'IPQuery Service User',
    shell   => '/sbin/nologin',
  }

  python::virtualenv { $virtualenv_dir :
    require => File[$install_dir],
  }

  package { ['gcc',
    'libffi-devel',
    'xmlsec1',
    'xmlsec1-openssl',
    'openssl-devel',
    'libyaml-devel']: }

  python::pip { 'ipquery' :
    virtualenv => $virtualenv_dir,
    owner      => 'root',
    require    => [
      File[$install_dir],
      User[$username],
      Class['python'],
      Package['gcc'],
      Package['libffi-devel'],
      Package['xmlsec1'],
      Package['xmlsec1-openssl'],
      Package['openssl-devel'],
      Package['libyaml-devel'],
      Python::Virtualenv[$virtualenv_dir],
      Class['epel'], # Workaround for bug https://github.com/stankevich/puppet-python/issues/196
      
    ],
    notify     => Class['apache::service'],
  }

  file { $wsgi_filename:
    content => template('ipquery/ipquery.wsgi.erb'),
    notify  => Class['apache::service'],
  }

  file { '/etc/ipquery.yaml':
    content => template('ipquery/ipquery.yaml.erb'),
    notify  => Class['apache::service'],
  }

  file { $tls_key_filename:
    content => $tls_certificate_key,
    mode    => '0600',
    notify  => Class['apache::service'],
  }

  file { $tls_cert_filename:
    content => $tls_certificate,
    notify  => Class['apache::service'],
  }

  apache::vhost { 'ipquery.opsec.mozilla.com':
    wsgi_script_aliases => {
      '/' => $wsgi_filename
    },
    wsgi_daemon_process => $username,
    wsgi_process_group  => $username,
    docroot             => $docroot,
    port                => '443',
    ssl                 => true,
    ssl_cert            => $tls_cert_filename,
    ssl_key             => $tls_key_filename,
    require             => [
      File[$tls_cert_filename],
      File[$tls_key_filename],
      User[$username],
      File[$wsgi_filename],
      File[$docroot],
      Python::Pip['ipquery'],
    ]
  }
}
