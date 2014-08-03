# -*- encoding: utf8 -*-
from fabric.api import env, settings, cd
from fabric.contrib.files import exists
from fabric.operations import local, sudo, run, put


# Default configurations
env.hosts = ['trilhus@universo42.com.br']

env.project_name = "filhosdeasgard"
env.install_to = "/webapps/filhosdeasgard"
env.git_repo = "https://github.com/joepreludian/filhosdeasgard.git"
env.site_url = "filhosdeasgard.com"
env.site_port = "80"

# Environment params
env.virtualenv_folder = '%s/env/bin' % env.install_to
env.nginx_upstream_resource = "%s_upstream" % env.project_name
env.gunicorn_socket_file = "%(virtualenv_folder)s/sock" % env

env.log_error_file = "%s/env/logs/nginx-error.log" % env.install_to
env.log_acess_file = "%s/env/logs/nginx-access.log" % env.install_to

env.static_dir = "%s/static/" % env.install_to  # MUST have ending slash
env.media_dir = "%s/media/" % env.install_to

env.circusd_file = "/opt/circus/watchers/%(project_name)s.ini" % env
env.nginx_file = "/etc/nginx/sites-enabled/%(project_name)s.conf" % env


## Target PC - Default command behaviors
def on_mac():
    env.commands = {
        'virtualenv': '/opt/local/bin/virtualenv',
        'bower': '/opt/local/bin/bower'
    }


def on_linux():
    env.commands = {
        'virtualenv': '/usr/bin/virtualenv',
        'bower': '/opt/nodejs/bin/bower'  # Because of Debian custom Install
    }



# env.install_to -> Set on command line tool to set where is gonna be installed the root of site
def isset_dir(path):
    with settings(warn_only=True):
        path = 'test -d %s' % path
        command_return = local(path, capture=True)

        return True if command_return.return_code == 0 else False


#
# Actions
#


def clone_repo():
    run('git clone %(git_repo)s %(install_to)s' % env)
    with cd(env.install_to):
        run('mkdir env')
        run('mkdir env/logs')


def create_nginx():
    template_file = """
server {

    listen   %(site_port)s;
    server_name %(site_url)s;

    client_max_body_size 4G;

    access_log %(log_acess_file)s;
    error_log %(log_error_file)s;

    location / {
        root %(install_to)s/;
    }

}""" % env

    f = open('nginx.conf' % env, 'w')
    f.write(template_file)
    f.close()

    put(local_path="nginx.conf", remote_path=env.nginx_file, use_sudo=True)


def restart_services():
    with settings(warn_only=True):
        sudo('/etc/init.d/nginx reload')
        #sudo('/opt/circus/bin/circusctl reload')


def sync_bower():
    with cd(env.install_to):
        run('%s install' % env.commands['bower'])

#
# Main functions
#
def setup():

    clone_repo()
    create_nginx()
    #sync_bower()

    restart_services()


def deploy():

    sync_bower()
    create_nginx()

    with cd(env.install_to):
        run('git pull')

    restart_services()


def uninstall():
    sudo('rm -Rf %(install_to)s' % env)
    sudo('rm -Rf %(nginx_file)s' % env)
    restart_services()