#!/bin/bash
#
##
##########################################################################
#                                                                        #
#       ssh_multi :: setup                                               #
#                                                                        #
#       ssh_multi (c) 2015-2016 Vamegh Hedayati                          #
#                                                                        #
#       Vamegh Hedayati <gh_vhedayati AT ev9 DOT io>                     #
#                                                                        #
#       Please see Copying for License Information                       #
#                             GNU/LGPL v2.1 1999                         #
##########################################################################
##
#

path="$HOME/.ssh-multi"

if [ $HOME = "/root" ]; then
  echo "please dont run me as root or run this script using sudo -H ..."
  exit 1
fi

if [ ! -e $path/user_config.yaml ]; then
  echo "making $path ..."
  mkdir -p "$path"
  echo "copying user configuration into place ..."
  cp configs/user_config.yaml $path/user_config.yaml
fi

sudo -H pip install virtualenv
sudo rm -rf build/
sudo python setup.py install

echo "Now you need to configure $path/user_config.yaml -- set the ssh user name to be your log in names and the passwords, ssh key paths etc all to match your information"

