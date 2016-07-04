#
##
##########################################################################
#                                                                        #
#       ssh_multi :: autossh/ssh_class                                   #
#                                                                        #
#       ssh_multi (c) 2015-2016 Vamegh Hedayati                          #
#       paramiko (c) Jeff Forcier https://github.com/paramiko/paramiko   #
#                                                                        #
#       Vamegh Hedayati <gh_vhedayati AT ev9 DOT io>                     #
#                                                                        #
#       Please see parmiko-license for License Information               #
#                             GNU/LGPL v2.1 1999                         #
##########################################################################
##
#

## This is currently untested -- changed from a bunch of functions to a class - still needs testing / work.

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

## most of this is a modification from https://github.com/paramiko/paramiko/blob/master/demos/demo.py,
## the demo example provided by paramiko, why re-invent the wheel?

class SSH_Connector(object):
  def __init__( self, transport='', ssh_data='', commands='', realtime=''):
    '''
      initialise the initial connection.
      ssh_data is a hash that needs to be passed
      this should contain ssh_user, ssh_key, ssh_pass, ssh_host, ssh_ip, port, auth_method, key_check.
      key_check should be either ignore, warn, or quiet
      auth_method is either pass or key, the rest should be self explanatory.
      optional ssh_timeout.
    '''
    self.transport=transport
    self.commands=commands
    self.realtime=realtime

    try:
      self.ssh_timeout = ssh_data['ssh_timeout']
    except KeyError as e:
      self.ssh_timeout=''
    try:
      self.user = ssh_data['ssh_user']
    except KeyError as e:
      self.user = ''
    try:
      self.passw = ssh_data['ssh_pass']
    except KeyError as e:
      self.passw = ''
    try:
      self.port = ssh_data['ssh_port']
    except KeyError as e:
      self.port = '22'
    try:
      self.auth_method = ssh_data['auth_method']
    except KeyError as e:
      self.auth_method = ''
    try:
      self.key = ssh_data['ssh_key']
    except KeyError as e:
      self.key = ''
    try:
      self.key_check = ssh_data['key_check']
    except KeyError as e:
      self.key_check = ''
    try:
      self.hostname=ssh_data['ssh_host']
    except KeyError as e:
      self.hostname=''
    try:
      self.ip=ssh_data['ssh_ip']
    except KeyError as e:
      self.ip=''

    if self.ip is None:
      self.host = self.hostname
    else:
      self.host = self.ip

  def agent_auth(self):
    """
    Attempt to authenticate to the given transport using any of the private
    keys available from an SSH agent.
    """
    agent = paramiko.Agent()
    agent_keys = agent.get_keys()
    if len(agent_keys) == 0:
      return
    for key in agent_keys:
      try:
        self.transport.auth_publickey(self.user, key)
        return
      except paramiko.SSHException:
        error = "next_key"

  def manual_auth(self):
    if len(self.key) == 0:
      self.key = os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
    if self.auth_method == 'key':
      try:
        key_get = paramiko.RSAKey.from_private_key_file(self.key)
      except paramiko.PasswordRequiredException:
        key_get = paramiko.RSAKey.from_private_key_file(self.key, self.passw)
      self.transport.auth_publickey(self.user, key_get)
    elif self.auth_method == 'pass':
      self.transport.auth_password(self.user, self.passw)

  def get_host_keys(self):
    try:
      host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
    except IOError:
      try:
        host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
      except IOError:
        print('*** Unable to open host keys file')
        host_keys = {}
    return host_keys

  def connect(self, commands=''):
    if self.host is None:
      print ("Error :: host = ", self.host, " :: Not valid")
      return "HOSTNAME_ERROR"
    else:
      try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
      except Exception as e:
        print('*** Connect failed: ' + str(e))
        traceback.print_exc()
        return "SOCKET_CONNECTION_ERROR"
    try:
      self.transport = paramiko.Transport(sock)
      try:
        self.transport.start_client()
      except paramiko.SSHException:
        print('*** SSH negotiation failed.')
        return "TRANSPORT_CONNECTION_ERROR"

      # check server's host key -- this is important.
      if self.key_check == "ignore":
        remote_key = self.transport.get_remote_server_key()
      elif self.key_check == "quiet":
        host_keys = get_host_keys()
        remote_key = self.transport.get_remote_server_key()
        if host_keys[self.hostname][remote_key.get_name()] != remote_key:
          print('*** ERROR: Host key has changed -- SKIPPING THIS HOST!!!')
          return "KEY_ERROR"
          #self.transport.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      else:
        host_keys = get_host_keys()
        remote_key = self.transport.get_remote_server_key()
        if self.hostname not in host_keys:
          print('*** WARNING: Unknown host key!')
        elif remote_key.get_name() not in host_keys[self.hostname]:
          print('*** WARNING: Unknown host key!')
        elif host_keys[self.hostname][remote_key.get_name()] != remote_key:
          print('*** WARNING: Host key has changed -- SKIPPING THIS HOST!!!')
          return "KEY_ERROR"
        else:
          print('*** Host key OK.')

      if self.auth_method == "pass":
        manual_auth()
        if not self.transport.is_authenticated():
          print('*** Authentication failed. :(')
          self.transport.close()
          sys.exit(1)
          #return "AUTH_ERROR"
      elif self.auth_method == "key":
        agent_auth()
        if not self.tranport.is_authenticated():
          manual_auth()
        if not self.transport.is_authenticated():
          print('*** Authentication failed. :(')
          self.transport.close()
          return "AUTH_ERROR"
      else:
        return "AUTH_ERROR"

      run_commands()
    except Exception as e:
      print("\033[94m" + hostname + "\033[0m >> " + '* Login Failure: ' + str(e))
      try:
        self.transport.close()
      except:
        pass
      return "EXCEPTION_CONNECTION_ERROR"

  def exec_command(command='', bufsize=-1, timeout=None, get_pty=False):
    ## from https://github.com/paramiko/paramiko/blob/master/paramiko/client.py
    #transport.accept
    self.transport.set_keepalive(5)
    chan = self.transport.open_session()
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

  def run_commands():
    ## modified from http://sebastiandahlgren.se/2012/10/11/using-paramiko-to-send-ssh-commands/
    for command in self.commands:
      chan, stdin, stdout, stderr = exec_command(command=command)
      if self.realtime:
        while not stdout.channel.exit_status_ready():
          # Only print data if there is data to read in the channel
          if stdout.channel.recv_ready():
            rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
            if len(rl) > 0:
              # Print data from stdout
              sys.stdout.write("\033[94m" + "host - " + self.hostname + "\033[0m >> " + stdout.channel.recv(1024).decode('utf-8'))
        for line in stderr.read().splitlines():
          print("\033[91m" + "STDERR :: host - " + self.hostname + "\033[0m >> " + line.decode('utf-8'))
      else:
        for line in stdout.read().splitlines():
          print("\033[94m" + "host - " + self.hostname + "\033[0m >> " + line.decode('utf-8'))
        for line in stderr.read().splitlines():
          print("\033[91m" + "STDERR :: host - " + self.hostname + "\033[0m >> " + line.decode('utf-8'))
      chan.close()
    self.transport.close

  def __del__(self):
    print ("Cleaning up ssh connections - making sure transport is closed")
    self.transport.close

