# Proxmox Asymmetric Cluster Management
PACM is designed to be a an automated management tool for asymmetric proxmox clusters.
Although this does not prevent it from being used on Symmetric clusters.

## Setup
#### Python Modules
There are several required modules for python. They are:
- [proxmoxer](https://github.com/proxmoxer/proxmoxer)
- requests (for proxmoxer)
- [simple-term-menu](https://github.com/IngoMeyer441/simple-term-menu) 
- [tinydb](https://github.com/msiemens/tinydb)

These are all available on pip.

#### Proxmox User
For the API access, an API token needs to be setup. Although you could setup a token against the root@pam user, this is not adviced.
ACM does not require many privileges, so full access is not required.

First setup a role. To save confusion name it something like ACMUser.
It will need the following privileges:
- Sys.Audit
- Sys.PowerMgmt (not required as of 0.0.1)
- VM.Audit
- VM.Migrate (not required as of 0.0.1)

![ACM Roles](https://raw.githubusercontent.com/zanginator/proxmox_acm/main/images/ACM_Roles.png)

Create a user (ACM) and under API Tokens, create an access token for that user.
![ACM Users](https://raw.githubusercontent.com/zanginator/proxmox_acm/main/images/ACM_Users.png)

![ACM API Tokens](https://raw.githubusercontent.com/zanginator/proxmox_acm/main/images/ACM_API-Tokens.png)

Under permissions, add a user permission for the ACM user setup with the path as '/' and Role to the one setup up above.
Do the same for the ACM API Token.
![ACM Permissions](https://raw.githubusercontent.com/zanginator/proxmox_acm/main/images/ACM_Permissions.png)

#### Config.py
There are a few things that need to be changed in here.

```host = { "host": "xxx.xxx.xxx.xxx"},{ "host": "xxx.xxx.xxx.xxx"}```

Replace the 'xxx.xxx.xxx.xxx' with the IPs of your servers, these need to be accessible from the machine running ACM.
This needs to be repeated for all nodes in the cluster. ACM will try to establish a connection with the first, failing that it will move to the next.

```
# This is the user your token is created against. Requires the authentication domain.
user = 'acm@pam'
# The API Token Key Name
token_name = 'acm_token'
# The API Token Key Value.
token_value = 'xxxxxxx-xxxx-xxxx-xxxxxxxx'
```

Update the user to match the one you created. The token_name and token_value need to match what was create above.

Once this is done. ACM should be ready to run.

#### Qdevice

It is advised that the machine (or VM) running ACM is also added to Proxmox as a qdevice.
This is so that if the cluster drops to just one machine being online, the cluster Quorum is still maintained.
If Quorum is not available, some administrative functions may fail (and Wake-On-LAN).

## Changelog
### 0.0.3 (2020-11-25)
- Added Manual Migration of VMs
  - Accessed via the VM Menu
- Added Migration Toggle (stored in DB for persistence and for later use)

### 0.0.2 (2020-11-12)
- Cleanup of Code.
  - Applied proper Python forming to some functions.
  - Added some more comments.
- Removal of 'Network Info' in node info menu.
- Added VM information querying.
- Added Migration controls to VM and Node Menu.
- Added TinyDB to store information and settings.

### 0.0.1 (2020-11-05)
- Initial Commit

