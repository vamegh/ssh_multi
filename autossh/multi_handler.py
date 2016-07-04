#!/usr/bin/python
#
##
##########################################################################
#                                                                        #
#       ssh_multi :: autossh/multi_handler                               #
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

import concurrent
import concurrent.futures
import datetime
import os
import re
import sys
import time
import yaml

try:
    import builtins
except ImportError:
    builtins = __builtins__

from autossh import ssh_handler

def warning_message(ip_list='', cmd_list='', options=''):
  print ("""*** Warning ***
  * You are about to run the following commands on the following hosts: \n""")
  for hostname, ip in ip_list.items():
    for names in cmd_list:
      print ('* ' + str(hostname) +
             ' :: ip ' + str(ip_list[hostname]) +
             ' :: Command :: ' + str(cmd_list[names]['command']))

  if options.force:
    response = "YES"
  else:
    response = str(raw_input("Are you sure you want to proceed ? (type YES to proceed): "))

  return response

def spawn_thread(hostname='', ip_address='', cmd_list='', username='',
                 password='', auth_method='', port='', ssh_key='',
                 key_check='', options=''):
  commands = []

  for names in cmd_list:
    command = cmd_list[names]['command']
    commands.append(command)

  ssh_handler.multi_connect(hostname, ip_address, username, password,
                            port, auth_method, ssh_key, commands, key_check, options)
  return

def get_static_hosts(cmdcfg='', options=''):
  api_host = cmdcfg['api_host']
  search_opts = {}
  ip_list = {}

  if options.env:
    search_opts['env'] = options.env;
  if options.role:
    search_opts['role'] = options.role;
  if options.application:
    search_opts['app'] = options.application;

  client = fleetclient.Client(api_host)
  data = client.get_hosts(search_opts)

  for host in data['hosts']:
    address = host['address']
    fqdn = host['fqdn']
    if options.dc:
     if re.match(options.dc,fqdn):
      ip_list[fqdn] = address
    else:
      ip_list[fqdn] = address

  ip_count = len(ip_list)
  ## lets just let it run full throttle to max 20 threads for now.
  ## re-enabled thread limiter for display reason
  #max_threads = ip_count / 2
  max_threads = ip_count

  if max_threads < 1:
    max_threads = 1
  if max_threads > 25:
    max_threads = 25
  if options.listhosts:
    for hostname, ip in ip_list.items():
      print ('* ' + str(hostname) +
             ' :: ip ' + str(ip_list[hostname]))
    sys.exit(1)

  return max_threads, ip_count, ip_list

def thread_process(ip_count='', ip_list='', max_threads='', cmdcfg='', cmd_list='', options=''):
  ssh_timeout = cmdcfg['ssh_timeout']
  username = cmdcfg['login_user']
  password = cmdcfg['login_pass']
  auth_method = cmdcfg['auth_method']
  port = cmdcfg['ssh_port']
  key_check = cmdcfg['host_key_check']
  ssh_key = cmdcfg['ssh_private_key']

  with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
    for hostname, ip_address in ip_list.items():
      try:
        future_to_ssh = executor.submit(spawn_thread, hostname, ip_address, cmd_list, username, password, auth_method, port, ssh_key, key_check, options)
      except Exception as exc:
        print('generated an exception: %s' % (exc))
        traceback.print_exc()

def single_process(ip_count='', ip_list='', max_threads='', cmdcfg='', cmd_list='', options=''):
  ssh_timeout = cmdcfg['ssh_timeout']
  username = cmdcfg['login_user']
  password = cmdcfg['login_pass']
  auth_method = cmdcfg['auth_method']
  port = cmdcfg['ssh_port']
  key_check = cmdcfg['host_key_check']
  ssh_key = cmdcfg['ssh_private_key']

  for hostname, ip_address in ip_list.items():
    spawn_thread(hostname=hostname, ip_address=ip_address, cmd_list=cmd_list,
                 username=username, password=password, auth_method=auth_method,
                 port=port, ssh_key=ssh_key, key_check=key_check, options=options)

