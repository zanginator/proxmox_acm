from simple_term_menu import TerminalMenu
import json
from tinydb import where

# ACM imports
import config

node_select = False
node_selected = ""


# Get cluster status (yes this is the same as the one in the main method.
# Should look at splitting this out to make it callable from more places easily.
def cluster_status():
    with open('cluster_info.json') as json_file:
        data = json.load(json_file)
        temp = data['node_status']

        for cluster_node in config.proxmoxAPI.cluster.resources.get(type='node'):
            if cluster_node["node"]:
                try:
                    line = {"id": cluster_node["node"], "status": cluster_node["status"]}
                except:
                    line = {"id": "Error", "status": "Error"}
                finally:
                    temp.append(line)
    return data


def selected_node(node_name):
    global node_selected
    node_selected = node_name
    return node_name


def node_selection():
    # Get Node information
    # info = cluster_status()
    # Unused, although still here as this could be adapted as a method to check if the status of the cluster nodes
    # has changed or not.

    terminal_node_select_menu_items = []

    # Assemble String for Menu
    for r in config.db.table('node'):
        if r['status'] == "online":
            terminal_node_select_menu_items.append(str(r['id']))

    terminal_node_select_menu_exit = False
    terminal_node_select_menu = TerminalMenu(
        title="Main Menu -> Node Menu -> Select A Node\nPlease select a node to query.\n",
        menu_entries=terminal_node_select_menu_items, preview_command=selected_node, clear_screen=True)

    while not terminal_node_select_menu_exit:
        selection = terminal_node_select_menu.show()
        if not selection == -1:
            terminal_node_select_menu_exit = True

    return


def node_stats(menu_item):
    if menu_item == "CPU Info":
        stat = config.proxmoxAPI.nodes(node_selected).status.get()
        cpu_stat = stat["cpuinfo"]
        return ("Cpu Info:\n  Model: " + cpu_stat["model"] + "\n  Cores: " + str(
            cpu_stat["cores"]) + "\n  Threads: " + str(cpu_stat["cpus"]) + "\n  Sockets: " + str(
            cpu_stat["sockets"]) + "\n  Current Clock (MHz): " + str(cpu_stat["mhz"]))
    elif menu_item == "Memory Info":
        stat = config.proxmoxAPI.nodes(node_selected).status.get()
        mem_stat = stat["memory"]
        return ("Memory Info:\n  Free: " + str(
            round(((mem_stat["free"]) / 1024 / 1024 / 1024), 2)) + "GB\n  Used: " + str(
            round(((mem_stat["used"]) / 1024 / 1024 / 1024), 2)) + "GB\n  Total: " + str(
            round(((mem_stat["total"]) / 1024 / 1024 / 1024), 2)) + "GB")
    elif menu_item == "Other Stat":
        stat = config.proxmoxAPI.nodes(node_selected).status.get()
        return "Random Stats:\n  Load Average: " + str(stat["loadavg"]) + "\n  Uptime: " + str(stat["uptime"]) + ""
    elif menu_item == "Toggle Migration":
        result = [r.get('migration') for r in config.db.table('node').search(where('id') == node_selected)]
        return str(str(result).lower() in ["['true']"])
    return


# Node Sub Menu Selection.
# Allows for the user to see specific node information.
# Calls proxmox_node_info.py for information.
def node_menu():
    terminal_node_menu_exit = False
    terminal_node_menu_items = ["CPU Info", "Memory Info", "Other Stat", "Toggle Migration", "Back to Main Menu"]
    terminal_node_menu = TerminalMenu(title="Main Menu -> Node Menu\nCurrently Querying Node: " + node_selected + "\n",
                                      menu_entries=terminal_node_menu_items, preview_command=node_stats,
                                      clear_screen=True)

    while not terminal_node_menu_exit:
        selection = terminal_node_menu.show()
        if selection == 3:
            for r in config.db.table('node').search(where('id') == node_selected):
                result = r.get('migration')
                result_filter = str(result).lower() in ["true"]
                if result_filter:
                    # Set to false
                    config.db.table('node').update({'migration': 'false'}, doc_ids=[r.doc_id])
                else:
                    # Set to true
                    config.db.table('node').update({'migration': 'true'}, doc_ids=[r.doc_id])
        if selection == 4:
            terminal_node_menu_exit = True
    return


def main():
    if not node_select:
        node_selection()
    node_menu()
