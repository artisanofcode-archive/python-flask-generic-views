PLUGINS = %w(vagrant-auto_network vagrant-hostsupdater vagrant-exec vagrant-triggers)

PLUGINS.reject! { |plugin| Vagrant.has_plugin? plugin }

unless PLUGINS.empty?
  print "The following plugins will be installed: #{PLUGINS.join ", "} continue? [y/n]: "
  if ['yes', 'y'].include? $stdin.gets.strip.downcase
    PLUGINS.each do |plugin|
      system("vagrant plugin install #{plugin}")
      puts
    end
  end
  puts "Please run again"
  exit 1
end

AutoNetwork.default_pool = "172.16.0.0/24"

$host_directory = File.expand_path(File.dirname(__FILE__))
$directory = "/home/vagrant/flask-generic-views"
$virtualenv = "/home/vagrant/env"

$provision = <<SCRIPT
#!/bin/sh

apt-get -y --force-yes install software-properties-common

[ ! -f /etc/apt/sources.list.d/fkrull-deadsnakes-trusty.list ] && sudo add-apt-repository ppa:fkrull/deadsnakes

# PACKAGES
if [ ! -f /root/.last-update ] || [ $(expr $(date +%s) / 60 / 60 / 24) -gt $(expr $(cat /root/.last-update) / 60 / 60 / 24) ]; then
  sudo apt-get -y update
  date +%s | sudo tee /root/.last-update > /dev/null
fi

apt-get -y --force-yes install python2.6 python2.7 python3.3 python3.4 python3.5 pypy python3-pip python-virtualenv git

# APPLICATION

[ ! -d #{$virtualenv} ] && su -c "virtualenv -p $(which python3) #{$virtualenv}" - vagrant

su -c "cd #{$directory} && #{$virtualenv}/bin/pip install -e .[all]" - vagrant
su -c "cd #{$directory} && #{$virtualenv}/bin/pip install tox pytest hypothesis sphinx wheel" - vagrant
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.box = "puppetlabs/ubuntu-14.04-64-nocm"

  config.vm.network "private_network", :auto_network => true

  config.vm.synced_folder ".", $directory, :type => :nfs

  config.vm.hostname = "flask-generic-views.vm"

  config.vm.provision "shell", :inline => $provision

  config.ssh.forward_agent = true

  config.vm.provider "vmware_fusion" do |v|
    v.vmx["memsize"] = "1024"
    v.vmx["numvcpus"] = "2"
  end

  config.hostsupdater.remove_on_suspend = true

  config.exec.commands "*", directory: $directory

  config.exec.commands "*", env: { "PATH" => "#{$virtualenv}/bin:$PATH" }

  config.exec.commands %w[make python py.test]

  def command?(cmd)
    exts = ENV['PATHEXT'] ? ENV['PATHEXT'].split(';') : ['']
    ENV['PATH'].split(File::PATH_SEPARATOR).each do |path|
      exts.each { |ext|
        exe = File.join(path, "#{cmd}#{ext}")
        return exe if File.executable?(exe) && !File.directory?(exe)
      }
    end

    return nil
  end

  if command? 'watchman'
    config.trigger.after [:up, :resume], :stdout => true do
      run "watchman watch #{$host_directory}"

      run "watchman -- trigger #{$host_directory} docs 'docs/**/*.rst' 'docs/**/*.py' 'flask_generic_views/**/*.py' -X 'docs/_build/**' -- vagrant exec 'make docs && echo'"
    end

    config.trigger.before [:halt, :suspend, :destroy], :stdout => true do
      run "watchman watch-del #{$host_directory}"
    end
  end
end