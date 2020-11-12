import json
import datetime
import time  # Will remove once I get rid of the testing timers.
import os
import platform  # For getting the OS
import subprocess  # For executing something in shell
from proxmoxer import ProxmoxAPI
from simple_term_menu import TerminalMenu
from tinydb import TinyDB, Query

# ACM imports
import proxmox_acm_node_menu as pni
import proxmox_acm_vm_menu as pvi
import config

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
    elif menu_item == "VM Information":
        return "View VM Specific Data."
    return str(datetime.datetime.now())


def main():
    # Print some ASCI art, because why not!
    print(config.logo)

    # Call proxmox_setup() to setup API connect
    proxmox_setup()

    # Call TinyDB Setup, this requires cluster connection
    database_setup()

    # Setup the Menu
    terminal_main_menu_items = ["Node Status", "Node Information", "VM Information", "Cluster", "Raw Cluster Resource",
                                "Rebuild Database", "Quit"]
    terminal_main_menu = TerminalMenu(title="Main Menu\nConnected with: " + api_host + "\n",
                                      menu_entries=terminal_main_menu_items, preview_command=preview_info,
                                      preview_size=0.75, clear_screen=True)

    menu_switcher = {
        1: pni.main,
        2: pvi.main,
        3: cluster_stat,
        4: stat_all,
        5: rebuild_db,
        6: exit_app
    }

    # Run the Menu
    while not config.terminal_main_menu_exit:
        selection = terminal_main_menu.show()

        if not selection == 0:
            func = menu_switcher.get(selection)
            func()


def cluster_stat() -> None:
    cluster_running_stat = config.proxmoxAPI.cluster.status.get()
    print(cluster_running_stat)
    time.sleep(10)  # For Testing
    return


def stat_all() -> None:
    cluster_resource = config.proxmoxAPI.cluster.resources.get(type='node')
    cluster_resource_stat = json.dumps(cluster_resource, separators=(',', ':'), indent=4, sort_keys=True)
    print(cluster_resource_stat)
    cluster_resource_2 = config.proxmoxAPI.cluster.status.get()
    cluster_resource_stat_2 = json.dumps(cluster_resource_2, separators=(',', ':'), indent=4, sort_keys=True)
    print(cluster_resource_stat_2)
    time.sleep(10)  # For Testing
    return


# Where things will be wrapped up upon exit.
def exit_app() -> None:
    print("Stopping Application")
    config.terminal_main_menu_exit = True
    return  # Not required, but here to mark the end of 'exit_app'


# This method makes a decision as to which host it shall contact.
# We run a simple ping to the host, if it responds we setup the API for it.
# This runs periodically and before a command is executed in-case a host
# shuts down or becomes unavailable.
def get_host() -> str:
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
    # return an IP if all else fails, this makes sure that the proxmox_setup does fail.
    return "127.0.0.1"


# This setups the ProxmoxAPI for proxmoxer.
def proxmox_setup() -> None:
    host_connection: bool = False
    while not host_connection:
        # Ping a host. If it responds, try connecting with it.
        host = get_host()
        config.proxmoxAPI = ProxmoxAPI(host, port=config.port, user=config.user, token_name=config.token_name,
                                       token_value=config.token_value, verify_ssl=False)
        # Try the connection.
        try:
            config.proxmoxAPI.version.get()
            print("Host Connection Verified.")
            # Connection established, exit 'while not' loop.
            host_connection = True
        except:
            print("Host Connection Rejected.\nTrying Again.")
    return


# Setup TinyDB into config file.
# Also check if first time running.
# If first run call database_create()
def database_setup() -> None:
    print("Setting up Database")
    config.db = TinyDB('acm_db.json')
    table = config.db.table('node')
    Node = Query()
    if not table.search(Node.id.exists()):
        print("Database not created. Starting Creation")
        database_create()
    return


# Called by database_setup if the tables do not exist.
# So we need to query the nodes and vm's
def database_create() -> None:
    node_error = 0
    vm_error = 0
    print("Gathering Cluster Data")
    print("Create and Populate Node Info")
    table = config.db.table('node')
    for cluster_node in config.proxmoxAPI.cluster.resources.get(type='node'):
        if cluster_node["node"]:
            try:
                table.insert({'id': cluster_node["node"], 'status': cluster_node["status"], 'migration': 'true'})
            except:
                print("Table Creation and Insertion error.")
                node_error += 1
    if node_error > 0:
        print("Node Table Creation Error, please rebuild.")
    print("Create and Populate VM Info")
    table = config.db.table('vm')
    for vm in config.proxmoxAPI.cluster.resources.get(type='vm'):
        if vm["id"]:
            try:
                table.insert({'id': vm["id"], 'status': vm["status"], 'node': vm["node"], 'migration': 'true'})
            except:
                print("Table Creation and Insertion error.")
                vm_error += 1
    if vm_error > 0:
        print("VM Table Creation Error, please rebuild.")
    print("Database Creation Complete.")
    return


# Rebuild the database. This needs to be called if there is an issue with creation.
# As there is no updating of which nodes VMs are on... this needs to be used.
def rebuild_db():
    print("Rebuilding Database.")
    # Drop all tables.
    config.db.drop_tables()
    # Then call the creation.
    database_create()
    return

if __name__ == "__main__":
    main()