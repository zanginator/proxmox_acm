import json
import datetime
import time
import os
import platform  # For getting the OS
import subprocess  # For executing something in shell

# ACM imports
import proxmox_acm_node_info as pni
import config

from proxmoxer import ProxmoxAPI
from simple_term_menu import TerminalMenu

__author__ = "zanginator"

# Running variables
api_host = "PlaceHolder"


def ping(host):
    # For directing output to null so it isn't printed
    fnull = open(os.devnull, 'w')
    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]
    # Run the damn command and pipe the output to Null
    return subprocess.call(command, stdout=fnull, stderr=subprocess.STDOUT) == 0


def cluster_status() -> str:
    for node in config.proxmoxAPI.cluster.resources.get(type='node'):
        if node["id"]:
            try:
                config.cluster_info[node["id"]] = node["status"]
            except:
                config.cluster_info[node["id"]] = "error"
    return json.dumps(config.cluster_info, separators=(',', ':'), indent=4)


def preview_info(menu_item) -> str:
    if menu_item == "Node Status":
        try:
            return str(cluster_status())
        except:
            return "Error with host contact."
    elif menu_item == "Node Information":
        return "View Node Specific Data."
    return str(datetime.datetime.now())


def main():
    # Print some ASCI art, because why not!
    print(config.logo)

    # Call proxmox_setup() to setup API connect
    proxmox_setup()

    # Setup the Menu
    terminal_main_menu_items = ["Node Status", "Node Information", "Cluster", "Raw Cluster Resource", "Quit"]
    terminal_main_menu = TerminalMenu(title="Main Menu\nConnected with: " + api_host + "\n",
                                      menu_entries=terminal_main_menu_items, preview_command=preview_info,
                                      preview_size=0.75, clear_screen=True)

    menu_switcher = {
        1: pni.main,
        2: cluster_stat,
        3: stat_all,
        4: exitapp
    }

    # Run the Menu
    while not config.terminal_main_menu_exit:
        selection = terminal_main_menu.show()

        if not selection == 0:
            func = menu_switcher.get(selection)
            func()


def cluster_stat():
    cluster_running_stat = config.proxmoxAPI.cluster.status.get()
    print(cluster_running_stat)
    time.sleep(10)
    return


def stat_all():
    cluster_resource = config.proxmoxAPI.cluster.resources.get(type='node')
    cluster_resource_stat = json.dumps(cluster_resource, separators=(',', ':'), indent=4, sort_keys=True)
    print(cluster_resource_stat)
    cluster_resource_2 = config.proxmoxAPI.cluster.status.get()
    cluster_resource_stat_2 = json.dumps(cluster_resource_2, separators=(',', ':'), indent=4, sort_keys=True)
    print(cluster_resource_stat_2)
    time.sleep(10)
    return


def exitapp():
    print("Stopping Application")
    config.terminal_main_menu_exit = True
    return


# This method makes a decision as to which host it shall contact.
# We run a simple ping to the host, if it responds we setup the API for it.
# This runs periodically and before a command is executed in-case a host
# shuts down or becomes unavaliable.
def getHost():
    temp = config.host
    for host in temp:
        if host["host"]:
            try:
                if ping(host["host"]):
                    print("Host Connection Established.")
                    global api_host
                    api_host = str(host["host"])
                    return str(host["host"])
                print("Host not reachable, trying next Host.")
            except:
                print("Error in getHost()")
    return


# This setups the ProxmoxAPI for proxmoxer.
def proxmox_setup():
    host_connection: bool = False
    while not host_connection:
        host = getHost()
        config.proxmoxAPI = ProxmoxAPI(host, port=config.port, user=config.user, token_name=config.token_name,
                                       token_value=config.token_value, verify_ssl=False)
        try:
            config.proxmoxAPI.version.get()
            print("Host Connection Verified.")
            host_connection = True
        except:
            print("Host Connection Rejected.\nTrying Again.")
    return


if __name__ == "__main__":
    main()