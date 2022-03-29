#!/usr/bin/python

### (c) Vamegh Hedayati - 2016 LGPL License please read the License file for more info.
#from distutils.core import setup
from setuptools import setup

setup (
  name='ssh-multi',
  version='0.1',
  description='ssh-multi a tool to ssh into servers, to help with automation',
  author='Vamegh Hedayati',
  author_email='gh_vhedayati@ev9.io',
  url='https://github.com/vamegh',
  include_package_data=True,
  packages=['autossh'],
  install_requires=[
    "futures",
    "futurist==0.13.0",
    "httplib2==0.19.0",
    "ipaddress==1.0.16",
    "paramiko==2.10.1",
    "PyYAML==5.4",
    "requests==2.20.0",
    "requests-futures==0.9.7",
    "sh==1.11",
    "urllib3==1.26.5",
  ],
  scripts=[
    'bin/ssh_multi',
  ],
  package_data={ 'autossh': ['Copying', 'paramiko-license', 'LICENSE', 'README.md'], },
  data_files=[('/etc/ssh-multi', [ 'configs/hosts_config.yaml',
                                   'configs/user_config.yaml',
                                   'configs/config.yaml',
                                   'configs/multi_config.yaml',
                                   'configs/git_config.yaml',
                                   'Copying',
                                   'LICENSE',
                                   'paramiko-license',
                                   'README.md'])]
)
