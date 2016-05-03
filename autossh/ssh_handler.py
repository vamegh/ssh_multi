#
##
##########################################################################
#                                                                        #
#       ssh_multi :: autossh/ssh_handler                                 #
#                                                                        #
#       ssh_multi (c) 2015-2016 Vamegh Hedayati                          #
#       paramiko (c) Jeff Forcier https://github.com/paramiko/paramiko   #
#                                                                        #
#       Vamegh Hedayati <vhedayati AT ev9 DOT eu>                        #
#                                                                        #
#       Please see parmiko-license for License Information               #
#                             GNU/LGPL v2.1 1999                         #
##########################################################################
##
#

## This is the original version which is just a bunch of functions -- but tested and working.

import base64
from binascii import hexlify
import os
import paramiko
import re
import select
import socket
import sys
import time
import traceback
from paramiko.py3compat import input

try:
    import builtins
except ImportError:
    builtins = __builtins__

## most of this is directly from https://github.com/paramiko/paramiko/blob/master/demos/demo.py, the demo example, why re-invent the wheel?

def agent_auth(transport, username):
  """
  Attempt to authenticate to the given transport using any of the private
  keys available from an SSH agent.
  """
  agent = paramiko.Agent()
  agent_keys = agent.get_keys()
  if len(agent_keys) == 0:
    return

  for key in agent_keys:
    #print('Trying ssh-agent key %s' % hexlify(key.get_fingerprint()))
    try:
      transport.auth_publickey(username, key)
      #print('... ssh-agent auth success!')
      return
    except paramiko.SSHException:
      error = "next_key"
      #print('... ssh-agent auth failure. Trying next key ...')

def manual_auth(transport, username, hostname, auth_method, ssh_keypath, password):
  if len(ssh_keypath) == 0:
    ssh_keypath = os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
    #print ("private ssh key path not provided using " + ssh_keypath)

  if auth_method == 'key':
    try:
      key = paramiko.RSAKey.from_private_key_file(ssh_keypath)
    except paramiko.PasswordRequiredException:
      key = paramiko.RSAKey.from_private_key_file(ssh_keypath, password)
    transport.auth_publickey(username, key)
  elif auth_method == 'pass':
    transport.auth_password(username, password)

def get_host_keys():
  try:
    host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
  except IOError:
    try:
      host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
    except IOError:
      print('*** Unable to open host keys file')
      host_keys = {}
  return host_keys

def connect(hostname, ip_address, username, password, port, auth_method, ssh_keypath, commands, key_check, options):

  host = ip_address

  if port is None:
    port = '22'
  if hostname is None:
    return "HOSTNAME_ERROR"
  else:
    try:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.connect((host, port))
    except Exception as e:
      print('*** Connect failed: ' + str(e))
      traceback.print_exc()
      return "SOCKET_CONNECTION_ERROR"

  try:
    t = paramiko.Transport(sock)
    try:
      t.start_client()
    except paramiko.SSHException:
      print('*** SSH negotiation failed.')
      return "TRANSPORT_CONNECTION_ERROR"

    # check server's host key -- this is important.
    if key_check == "ignore":
      key = t.get_remote_server_key()
    elif key_check == "quiet":
      host_keys = get_host_keys()
      key = t.get_remote_server_key()
      if host_keys[hostname][key.get_name()] != key:
        print('*** ERROR: Host key has changed -- SKIPPING THIS HOST!!!')
        return "KEY_ERROR"
        #t.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
      host_keys = get_host_keys()
      key = t.get_remote_server_key()
      if hostname not in host_keys:
        print('*** WARNING: Unknown host key!')
      elif key.get_name() not in host_keys[hostname]:
        print('*** WARNING: Unknown host key!')
      elif host_keys[hostname][key.get_name()] != key:
        print('*** WARNING: Host key has changed -- SKIPPING THIS HOST!!!')
        return "KEY_ERROR"
      else:
        print('*** Host key OK.')

    if auth_method == "pass":
      manual_auth(t, username, host, auth_method, ssh_keypath, password)
      if not t.is_authenticated():
        print('*** Authentication failed. :(')
        t.close()
        sys.exit(1)
        return "AUTH_ERROR"

    elif auth_method == "key":
      agent_auth(t, username)
      if not t.is_authenticated():
        manual_auth(t, username, host, auth_method, ssh_keypath, password)
      if not t.is_authenticated():
        print('*** Authentication failed. :(')
        t.close()
        return "AUTH_ERROR"
    else:
      return "AUTH_ERROR"

    run_commands(t, commands, hostname, options)
  except Exception as e:
    #print("\033[94m" + hostname + "\033[0m >> " + '* LOGIN Failure: ' + str(e.__class__) + ': ' + str(e))
    print("\033[94m" + hostname + "\033[0m >> " + '* Login Failure: ' + str(e))
    #traceback.print_exc()
    try:
      t.close()
    except:
      pass
    return "EXCEPTION_CONNECTION_ERROR"

def exec_command(transport, command, bufsize=-1, timeout=None, get_pty=False):
  ## from https://github.com/paramiko/paramiko/blob/master/paramiko/client.py
  #transport.accept
  transport.set_keepalive(5)
  chan = transport.open_session()
  if get_pty:
    chan.get_pty()
  chan.settimeout(timeout)
  chan.exec_command(command)
  # open_state = transport.is_active
  # auth_state = transport.is_authenticated
  # print ("open state, auth_state == ", open_state, auth_state)
  stdin = chan.makefile('wb', bufsize)
  stdout = chan.makefile('r', bufsize)
  stderr = chan.makefile_stderr('r', bufsize)
  return chan, stdin, stdout, stderr

def run_commands(transport, commands, hostname, options):
  ## modified from http://sebastiandahlgren.se/2012/10/11/using-paramiko-to-send-ssh-commands/
  for command in commands:
    chan, stdin, stdout, stderr = exec_command(transport, command)
    if options.realtime:
      while not stdout.channel.exit_status_ready():
        # Only print data if there is data to read in the channel
        if stdout.channel.recv_ready():
          rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
          if len(rl) > 0:
            # Print data from stdout
            sys.stdout.write("\033[94m" + "host - " + hostname + "\033[0m >> " + stdout.channel.recv(1024).decode('utf-8'))

      for line in stderr.read().splitlines():
        print("\033[91m" + "STDERR :: host - " + hostname + "\033[0m >> " + line.decode('utf-8'))
    else:
      for line in stdout.read().splitlines():
        print("\033[94m" + "host - " + hostname + "\033[0m >> " + line.decode('utf-8'))
      for line in stderr.read().splitlines():
        print("\033[91m" + "STDERR :: host - " + hostname + "\033[0m >> " + line.decode('utf-8'))
    chan.close()
  transport.close

