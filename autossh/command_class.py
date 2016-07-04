#
##
##########################################################################
#                                                                        #
#       ssh_multi :: autossh/command_class                               #
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

from optparse import OptionParser

class Commands(object):
    def __init__(self, name='', version='0.0.1', message=''):
      self.app_name = name
      self.app_version = version
      self.app_message = message
      self.parser = OptionParser(version=self.app_version,
        usage='\n'.join([
          self.app_name+' [options]\n',
          'list of command are read in from the yaml config files in /etc/ssh_multi',
          'use these tools with care -- with great powers, comes even greater retardation ... ',
        ]))

    def default_options(self):
      '''These commands should be made available to all applications'''
      self.parser.add_option('-c', '--config', action='store', default='/etc/ssh_multi/config.yaml',
        help='Provide a custom configuration file, defaults to /etc/ssh_multi/config.yaml if none provided')
      self.parser.add_option('-H', '--host', action='store',
        help='hostnames to add the FQDN is required')
      self.parser.add_option('--force', action='store_true',
        help='Force the run without any questions -- use this with extreme care')
      self.parser.add_option('--realtime', action='store_true',
        help=' '.join(['Force the ssh run in real-time output mode :: this option can skip returned output',
                   'use with care, but probably better if expecting a lot of output']))

    def multi_options(self):
      self.parser.add_option('-A', '--allcmds', action='store_true',
        help=' '.join(['ssh-multi :: all of the commands listed in the config file will be run',
                       ' :: either this, the custom command or the name option must be specified']))
      self.parser.add_option('-C', '--custom', action="append",
        help=' '.join(['ssh_multi :: Add your own custom commands to be executed (repeatable)',
                      'either this, name or all options must be specified''']))
      self.parser.add_option('-l', '--listhosts', action='store_true',
        help='list all of the servers without executing a command on them')
      self.parser.add_option('-n', '--name', action='append',
        help=' '.join(['ssh_multi :: The name of a command to run as contained within the config',
             '(repeatable) either this, the custom command or the all option must be specified']))
      self.parser.add_option('--show', action="store_true",
        help='ssh_multi :: Display all available command options as contained within the config')

    def set_options(self):
      options, args = self.parser.parse_args()
      return options, args, self.parser

