#!/usr/bin/python3
# Copyright (c) 2016, James Beedy <jamesbeedy@gmail.com>

import os
import sys
import pwd
import shutil
import subprocess

from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import when_all
from charms.reactive import only_once
from charms.reactive import set_state
from charmhelpers.core.templating import render
from charmhelpers.core import hookenv
from charmhelpers.core import host
from charmhelpers.core.host import chdir
from charmhelpers.contrib.python.packages import pip_install

from nginxlib import configure_site


PRESENT_DIR = '/srv/present'

config = hookenv.config()


def _ensure_basedir(directory):

    """ Ensure presentation basedir exists
    """
    if not os.path.isdir(directory):
        os.makedirs(directory)

    uid = pwd.getpwnam('www-data').pw_uid
    os.chown(directory, uid, -1)


@when('nginx.available')
@when_not('presentation.available')
@only_once
def install_presentation():

    """ Install presentation
    """

    # Clone repo
    hookenv.status_set('maintenance', 
                       'Installing and building the presentation.')

    git_clone_cmd = 'git clone %s /tmp/present' % config['git-repo']
    subprocess.call(git_clone_cmd.split(), shell=False)  

    # Ensure base dir exists
    _ensure_basedir(PRESENT_DIR)

    # Build and install
    with chdir('/tmp/present'):
        with open('requirements.txt', 'r') as f:
            for i in list(map(lambda b: b.strip('\n'), f.readlines())):
                pip_install(i)

        sphinx_build_cmd = 'sphinx-build -b html source %s' % PRESENT_DIR
        subprocess.call(sphinx_build_cmd.split(), shell=False)
    present_chown_cmd = 'chown -R www-data:www-data %s' % PRESENT_DIR
    subprocess.call(present_chown_cmd.split(), shell=False)   
    
    # Configure nginx vhost
    configure_site('present', 'present.vhost', app_path=PRESENT_DIR)

    # Open presentation front-end port
    hookenv.open_port(config['port'])

    # Set status
    hookenv.status_set('active', 
                       'Presentation is active on port %s' % config['port'])
    # Set state
    set_state('presentation.available')
    

@when('nginx.available', 'website.available')
def configure_website(website):
    website.configure(port=config['port'])
