# These are you're hosts in JSON format, list all cluster nodes out here.
# Be sure to put your primary node first.
host = { "host": "xxx.xxx.xxx.xxx"},{ "host": "xxx.xxx.xxx.xxx"},{ "host": "xxx.xxx.xxx.xxx"}
# This shouldn't need to change unless you access the Web UI on a different port.
port = 8006
# This is the user your token is created against. Requires the authentication domain.
user = 'acm@pam'
# The API Token Key Name
token_name = 'acm_token'
# The API Token Key Value.
token_value = 'xxxxxxxxxxxxxxxxx'

proxmoxAPI = None
cluster_info = {}
terminal_main_menu_exit = False

logo = "Proxmox ACM"