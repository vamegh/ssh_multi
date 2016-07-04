#
##
##########################################################################
#                                                                        #
#       ssh_multi :: autossh/config_handler                              #
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

import getpass
import yaml
import sys
import os.path

def read_yaml(config_file=''):
  with open(config_file, "r") as config:
    yaml_data = yaml.safe_load(config)
  return yaml_data

## check the config file (raw) do some basic command line processing,
## to see if all or just some of the check conditions should be processed
def read_cfg(options='', args='', parser=''):
  hosts_config=''
  user_config=''
  multi_config=''
  git_config=''

  with open(options.config, "r") as configyml:
    cfg_data = yaml.safe_load(configyml)

  try:
    hosts_config = cfg_data['hosts_config']
  except KeyError as e:
    print ("no hosts config file supplied skipping")
  try:
    user_config = cfg_data['user_config']
  except KeyError as e:
    print ("no user config file supplied skipping")
  try:
    multi_config = cfg_data['multi_config']
  except KeyError as e:
    print ("no multi config file supplied skipping")
  try:
    git_config = cfg_data['git_config']
  except KeyError as e:
    print ("no git config file supplied skipping")

  if hosts_config:
    hosts_data = read_yaml(config_file=hosts_config)
    cfg_data.update(hosts_data)
  if user_config:
    user_config = os.path.expanduser(user_config)
    user_data = read_yaml(config_file=user_config)
    cfg_data.update(user_data)
  if multi_config:
    multi_data = read_yaml(config_file=multi_config)
    cfg_data.update(multi_data)
  if git_config:
    git_data = read_yaml(config_file=git_config)
    cfg_data.update(git_data)
  return cfg_data

def check_default(options='', args='', parser=''):
  if not options.host:
    parser.print_help()
    sys.exit(1)
  return options

def multi_check(options='', parser='', rawcmds=''):
  cmd_checks = {}
  cmd_checks["ssh_commands"] = {}

  if options.show:
    for cmd_names in list(rawcmds["ssh_commands"].keys()):
      print (cmd_names)
    sys.exit(0)
  if options.listhosts:
    '''cmd_checks = rawcmds'''
  elif options.allcmds:
    '''cmd_checks = rawcmds'''
  elif options.name:
    for name in (options.name):
      if name in list(rawcmds["ssh_commands"].keys()):
        cmd_checks['ssh_commands'][name] = rawcmds['ssh_commands'][name]
    rawcmds.update(cmd_checks)
  elif options.custom:
    counter = 0
    for name in (options.custom):
      counter += 1
      count_str = str(counter)
      command_name = "custom-command_" + count_str
      cmd_checks['ssh_commands'].update({command_name:{'command':name}})
    rawcmds.update(cmd_checks)
  else:
    parser.print_help()
    sys.exit(1)
  return rawcmds

## parse the config file, add in none defaults if nothing has been set for the cmdcheck hash / dict
def scan_yaml(cmdcheck=''):
  git_config = {}
  hosts_config = {}

  for key in cmdcheck:
    ## git information / config cleaning
    if key == "git":
      git_config = cmdcheck[key]
    if key == "ssh_commands":
      ssh_commands = cmdcheck[key]

  try:
    ssh_pass = cmdcheck["ssh_pass"]
  except KeyError as e:
    new_pass = getpass.getpass('ssh password / key passphrase: ')
    if len(new_pass) == 0:
      cmdcheck["ssh_pass"] = "none"
    else:
      cmdcheck["ssh_pass"] = new_pass

  try:
    ssh_user = cmdcheck["ssh_user"]
  except KeyError as e:
    new_user = getpass.getuser()
    cmdcheck["ssh_user"] = new_user

  for key in git_config:
    try:
      clone_path = git_config[key]["clone_path"]
    except KeyError as e:
      new_key = e.args[0]
      git_config[key][new_key] = "none"
    try:
      clone_path = git_config[key]["remote_repo"]
    except KeyError as e:
      new_key = e.args[0]
      git_config[key][new_key] = "none"

  ## for ssh_multi
  for key in ssh_commands:
    try:
      name = ssh_commands[key]["name"]
    except KeyError as e:
      new_key = e.args[0]
      ssh_commands[key][new_key] = "none"
    try:
      command = ssh_commands[key]["command"]
    except KeyError as e:
      new_key = e.args[0]
      ssh_commands[key][new_key] = "none"
    try:
      output_variable = ssh_commands[key]["output_variable"]
    except KeyError as e:
      new_key = e.args[0]
      ssh_commands[key][new_key] = "none"
    try:
      position = ssh_commands[key]["position"]
    except KeyError as e:
      new_key = e.args[0]
      ssh_commands[key][new_key] = "none"


  return cmdcheck, git_config, ssh_commands

def create_provisioner(host_data=''):
  cfg_file = {}

  app_name = host_data["app"]
  srv_role = host_data["role"]
  srv_dc = host_data["dc"]

  srv_volumes = []
  srv_loc = host_data["location"]
  srv_size = host_data["size"]
  srv_template = host_data["template"]
  srv_net = host_data["networks"]
  srv_nodes = host_data["nodes"]
  srv_volumes = host_data["volumes"]

  cfg_file['app'] = app_name
  cfg_file['compute'] = {}
  cfg_file['compute'][srv_role] = {}
  cfg_file['compute'][srv_role]['version'] = 1
  cfg_file['compute'][srv_role][srv_loc] = {}
  cfg_file['compute'][srv_role][srv_loc]['size'] = srv_size
  cfg_file['compute'][srv_role][srv_loc]['volumes'] = {}
  if len(srv_volumes) == 1:
    cfg_file['compute'][srv_role][srv_loc]['volumes'] = [{'size':  srv_volumes[0]}]
  else:
    cfg_file['compute'][srv_role][srv_loc]['volumes'] = [{'size':  int(10240)}]
    for vols in srv_volumes[1:]:
      cfg_file['compute'][srv_role][srv_loc]['volumes'].append({'size': int(vols)})
  cfg_file['compute'][srv_role][srv_loc]['template'] = srv_template
  cfg_file['compute'][srv_role][srv_loc]['networks'] = srv_net
  cfg_file['compute'][srv_role][srv_loc]['zones'] ={}
  cfg_file['compute'][srv_role][srv_loc]['zones'][srv_dc] = int(srv_nodes)
  return cfg_file

def write_provisioner(config='', data=''):
  with open(config, 'w') as outfile:
      outfile.write(yaml.dump(data, default_flow_style=False))

def laters(message=''):
  print ("Exiting Now : ",message)
  print ("Was it as good for you as it was for me ? ")
  sys.exit(1)

def clean_laters(message=''):
  print ("Exiting Now : ",message)
  print ("Was it as good for you as it was for me ? ")
  sys.exit(0)

