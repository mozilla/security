node default {
  include 'python'
  include 'ipquery'
  include 'apache'
  include 'apache::mod::ssl'
  include 'apache::mod::wsgi'

  # Workaround for bug https://github.com/stankevich/puppet-python/issues/196
  include 'epel'
  Class['epel'] -> Class['python']
}