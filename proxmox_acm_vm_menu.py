from simple_term_menu import TerminalMenu
import json
from tinydb import where

# ACM imports
import config

vm_select = False
vm_selected = ""


# Get vm status.
def vm_status():
    with open('cluster_info.json') as json_file:
        data = json.load(json_file)
        temp = data['node_status']

        for vm in config.proxmoxAPI.cluster.resources.get(type='vm'):
            if vm["id"]:
                try:
                    line = {"id": vm["id"], "status": vm["status"]}
                except:
                    line = {"id": "Error", "status": "Error"}
                finally:
                    temp.append(line)
    return data


def selected_vm(vm_name):
    global vm_selected
    vm_selected = vm_name
    return vm_name


def vm_selection():
    # Get Node information
    # info = vm_status()
    # Unused, although still here as this could be adapted as a method to check if the status of the vm
    # has changed or not.

    terminal_vm_select_menu_items = []

    # Assemble String for Menu
    for r in config.db.table('vm'):
        if r['status'] == "running":
            terminal_vm_select_menu_items.append(str(r['id']))

    terminal_vm_select_menu_exit = False
    terminal_vm_select_menu = TerminalMenu(
        title="Main Menu -> VM Menu -> Select A VM\nPlease select a VM to query.\n",
        menu_entries=terminal_vm_select_menu_items, preview_command=selected_vm, clear_screen=True)

    while not terminal_vm_select_menu_exit:
        selection = terminal_vm_select_menu.show()
        if not selection == -1:
            terminal_vm_select_menu_exit = True

    return


def vm_stats(menu_item) -> str:
    global vm_selected
    stat = config.proxmoxAPI.cluster.resources.get(type='vm')
    if menu_item == "CPU Info":
        for info in stat:
            if info["id"] == vm_selected:
                return ("CPU Load: " + str(round((info["cpu"] * 100), 2)) + "%\nCores: " +
                        str(info["maxcpu"]) + "")
        return ""
    elif menu_item == "Memory Info":
        for info in stat:
            if info["id"] == vm_selected:
                return ("Memory Info:\n  Used: " + str(
                    round(((info["mem"]) / 1024 / 1024 / 1024), 2)) + "GB\n  Total: " + str(
                    round(((info["maxmem"]) / 1024 / 1024 / 1024), 2)) + "GB")
        return ""
    elif menu_item == "Other Stat":
        for info in stat:
            if info["id"] == vm_selected:
                return "Uptime: " + str(info["uptime"]) + "\nHosting Node: " + str(info["node"])
        return ""
    elif menu_item == "Toggle Migration":
        result = [r.get('migration') for r in config.db.table('vm').search(where('id') == vm_selected)]
        return str(str(result).lower() in ["['true']"])
    return ""


# VM Sub Menu Selection.
# Allows for the user to see specific vm information.
def vm_menu() -> None:
    terminal_vm_menu_exit = False
    terminal_vm_menu_items = ["CPU Info", "Memory Info", "Other Stat", "Toggle Migration", "Select VM",
                              "Back to Main Menu"]
    terminal_vm_menu = TerminalMenu(title="Main Menu -> VM Menu\nCurrently Querying VM: " + vm_selected + "\n"
                                    , menu_entries=terminal_vm_menu_items, preview_command=vm_stats, clear_screen=True)

    while not terminal_vm_menu_exit:
        selection = terminal_vm_menu.show()
        if selection == 3:
            # Toggle Migration status of VM
            for r in config.db.table('vm').search(where('id') == vm_selected):
                result = r.get('migration')
                result_filter = str(result).lower() in ["true"]
                if result_filter:
                    # Set to false
                    config.db.table('vm').update({'migration': 'false'}, doc_ids=[r.doc_id])
                else:
                    # Set to true
                    config.db.table('vm').update({'migration': 'true'}, doc_ids=[r.doc_id])
        elif selection == 4:
            # Go back to VM selection
            vm_selection()
        elif selection == 5:
            # Exit to main menu
            terminal_vm_menu_exit = True
    return


def main():
    if not vm_select:
        vm_selection()
    vm_menu()
