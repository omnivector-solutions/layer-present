#!/usr/bin/python3
# Copyright (c) 2016, James Beedy <jamesbeedy@gmail.com>

import os
import subprocess

from charmhelpers.core.templating import render
from charmhelpers.core import hookenv
from charmhelpers.core import host
from charmhelpers.core.host import chdir
from charmhelpers.contrib.python.packages import pip_install

from charms.reactive import (
    when,
    when_not,
    set_flag,
)
from charms.layer import options

from charms.layer.nginx import configure_site


config = hookenv.config()


@when('nginx.available', 'codebase.available')
@when_not('presentation.available')
def install_presentation():

    """ Install presentation
    """

    opts = options('git-deploy')

    hookenv.status_set('maintenance', 
                       'Installing and building the presentation.')

    # Build and install
    with chdir(os.path.join(opts.get('target'), 'current')):
        with open('requirements.txt', 'r') as f:
            for i in list(map(lambda b: b.strip('\n'), f.readlines())):
                pip_install(i)

        sphinx_build_cmd = 'sphinx-build -b html source %s' % opts.get('target')
        subprocess.call(sphinx_build_cmd.split(), shell=False)
    present_chown_cmd = 'chown -R www-data:www-data %s' % opts.get('target')
    subprocess.call(present_chown_cmd.split(), shell=False)   
    
    # Configure nginx vhost
    configure_site('present', 'present.vhost', app_path=opts.get('target'))

    # Open presentation front-end port
    hookenv.open_port(config['port'])

    # Set status
    hookenv.status_set('active', 
                       'Presentation is active on port %s' % config['port'])
    # Set flag
    set_flag('presentation.available')


@when_not('status')
def set_status():
    hookenv.status_set('active', 
                       'Presentation is active on port %s' % config['port'])


@when('nginx.available', 'website.available')
def configure_website(website):
    website.configure(port=config['port'])
