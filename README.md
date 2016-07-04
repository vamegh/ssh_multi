
** This is still WIP / Not Finished **

This is still work in progress / wont work as is.



# ssh_multi
python ssh multi host tool -- yaml configuration.

## Introduction
This can be used to replace mcollective for simple tasts.

It Uses concurrent.futures and a modified version of the client Paramiko class / demo provided by paramiko, to be able to ssh a list of hosts which can be specified via a config file. It will try agent / ssh-key and username / passwords to connect through, once connected it will run any of the commands as defined withing the config file.  The commands are fully configuratble.

Due to the fact that its concurrent, this should be actually quite fast. Its limited to a max 25 concurrent "threads" or sessions, it will queue anything greater than this.




