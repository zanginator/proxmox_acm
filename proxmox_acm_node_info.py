from simple_term_menu import TerminalMenu
import json

# ACM imports
import config

nodeSelect = False
node = ""

# Get cluster status (yes this is the same as the one in the main method.
# Should look at splitting this out to make it callable from more places easily.
def clusterStatus():
    with open('cluster_info.json') as json_file:
        data = json.load(json_file)
        temp = data['node_status']

        for node in config.proxmoxAPI.cluster.resources.get(type='node'):
            if node["node"]:
                try:
                    line = {"id": node["node"], "status": node["status"]}
                except:
                    line = {"id": "Error", "status": "Error"}
            temp.append(line)

        print(temp)
    return (data)


def selectedNode(nodeName):
    global node
    node = nodeName
    return (nodeName)


def nodeSelection():
    # Get Node information
    info = clusterStatus()

    terminal_node_select_menu_items = []

    # Assemble String for Menu
    for node in info["node_status"]:
        if node["status"] == "online":
            terminal_node_select_menu_items.append(str(node["id"]))

    terminal_node_select_menu_exit = False
    terminal_node_select_menu = TerminalMenu(
        title="Main Menu -> Node Menu -> Select A Node\nPlease select a node to query.\n",
        menu_entries=terminal_node_select_menu_items, preview_command=selectedNode, clear_screen=True)

    while not terminal_node_select_menu_exit:
        selection = terminal_node_select_menu.show()
        if not selection == -1:
            terminal_node_select_menu_exit = True

    return


def nodeStats(menuItem):
    if menuItem == "CPU Info":
        stat = config.proxmoxAPI.nodes(node).status.get()
        cpuStat = stat["cpuinfo"]
        return ("Cpu Info:\n  Model: " + cpuStat["model"] + "\n  Cores: " + str(
            cpuStat["cores"]) + "\n  Threads: " + str(cpuStat["cpus"]) + "\n  Sockets: " + str(
            cpuStat["sockets"]) + "\n  Current Clock (MHz): " + str(cpuStat["mhz"]))
    elif menuItem == "Memory Info":
        stat = config.proxmoxAPI.nodes(node).status.get()
        memStat = stat["memory"]
        return ("Memory Info:\n  Free: " + str(
            round(((memStat["free"]) / 1024 / 1024 / 1024), 2)) + "GB\n  Used: " + str(
            round(((memStat["used"]) / 1024 / 1024 / 1024), 2)) + "GB\n  Total: " + str(
            round(((memStat["total"]) / 1024 / 1024 / 1024), 2)) + "GB")
    elif menuItem == "Network Info":
        return ("Network Info:\n  Nothing is displayed here yet.")
    elif menuItem == "Other Stat":
        stat = config.proxmoxAPI.nodes(node).status.get()
        return ("Random Stats:\n  Load Average: " + str(stat["loadavg"]) + "\n  Uptime: " + str(stat["uptime"]) + "")

    return


# Node Sub Menu Selection.
# Allows for the user to see specific node information.
# Calls proxmox_node_info.py for information.
def node_menu():
    terminal_node_menu_exit = False
    terminal_node_menu_items = ["CPU Info", "Memory Info", "Network Info", "Other Stat", "Back to Main Menu"]
    terminal_node_menu = TerminalMenu(title="Main Menu -> Node Menu\nCurrently Querying Node: " + node + "\n",
                                      menu_entries=terminal_node_menu_items, preview_command=nodeStats,
                                      clear_screen=True)

    while not terminal_node_menu_exit:
        selection = terminal_node_menu.show()
        if selection == 4:
            terminal_node_menu_exit = True
    return


def main():
    if not nodeSelect:
        nodeSelection()
    node_menu()