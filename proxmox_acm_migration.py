from simple_term_menu import TerminalMenu

# ACM imports
import config


def migrate_menu(vm_selected) -> None:
    terminal_migrate_menu_exit = False
    host_node = ""
    stat = config.proxmoxAPI.cluster.resources.get(type='vm')
    for info in stat:
        if info["id"] == vm_selected:
            host_node = str(info["node"])
            # Strip "qemu/" string from VM ID.
            vm_id = vm_selected[len("qemu/"):]
            break

    # get_nodes returns a list variable for the menu to use.
    terminal_migrate_menu_items = get_nodes(host_node, True)

    terminal_migrate_menu = TerminalMenu(title="Main Menu -> VM Menu\nChoose a Node to Migrate: " + vm_selected + "\n",
                                         menu_entries=terminal_migrate_menu_items, clear_screen=True)
    while not terminal_migrate_menu_exit:
        selection = terminal_migrate_menu.show()

        if selection == 0:
            terminal_migrate_menu_exit = True

        if not selection == 0:
            # Grab the target host from the list.
            # We stringify and split the string because we want to remove the '(suggested)' from the string.
            stringify_target_host = str(terminal_migrate_menu_items[selection]).split()
            target_host = stringify_target_host[0]
            # Kick the migration off.
            migrate_vm(host_node, vm_id, target_host, 1)
            terminal_migrate_menu_exit = True

    return


# returns nodes available for migration.
def get_nodes(host_node, suggested) -> list:
    # When called will return all online nodes, that isn't the host_node.
    # It will quickly look at node load and make a suggestion of where to migrate.
    # host_node is node being migrated from. suggested is a bool of if you want the system to suggest a node.

    if suggested:
        # Assemble list with suggestion.
        menu_items = get_suggested(host_node)
    else:
        menu_items = ["Cancel Migration"]
        # Assemble list without suggestion.
        for r in config.db.table('node'):
            if (r['status'] == "online") and (r['id'] != host_node):
                menu_items.append(str(r['id']))
    return menu_items


# Looks at node load and makes a suggestion of where to move a VM.
def get_suggested(host_node):
    # get the cluster stat and find the "loadavg" and "maxcpu" of each node.
    # We grab the load-average as it removes spikes within the CPU usage.
    # We divide the load-average by the maxcpu to get a decimal.
    # The reason is that as each node is different, this is sort of a way of producing a...
    # "node capacity"
    menu_items = ["Cancel Migration"]
    lowest_node_name = ""
    lowest_node_cpu = 10.00
    # For each node in cluster...
    for r in config.db.table('node'):
        # ....That is online....
        # TODO this should grab from the cluster status page instead, not the DB.
        if (r['status'] == "online") and (r['id'] != host_node):
            rdddata = config.proxmoxAPI.nodes(r['id']).rrddata.get(timeframe='hour', cf='AVERAGE')
            las_pos = int(len(rdddata)) - 1
            rdddatafilt = rdddata[las_pos]
            try:
                calc_cpu_perc = float(rdddatafilt["loadavg"]) / float(rdddatafilt["maxcpu"])
            except KeyError:
                print("Error in API call.")
                break
                # TODO something better than this.

            if calc_cpu_perc <= lowest_node_cpu:
                lowest_node_cpu = calc_cpu_perc
                lowest_node_name = str(r["id"])

            menu_items.append(str(r['id']))

    # Amend suggested to list line.
    try:
        pos = menu_items.index(lowest_node_name)
        menu_items[pos] = lowest_node_name + " (Suggested)"
    except ValueError:
        # TODO Better error code/handling?
        print("whoops")
    return menu_items


# Called to migrate a VM from one node to another.
def migrate_vm(host_node: str, vm_id: int, target_node: str, migration_type: int):
    # host_node is the node you are talking to (this should be pulled from somewhere).
    # vm_id is the target VM to be migrated.
    # target_node is the target cluster node.
    # migration_type is either 0 - offline or 1 - online migration. (usually always 1)
    return config.proxmoxAPI.nodes(host_node).qemu(vm_id).migrate.create(target=target_node, online=migration_type)


# Returns either a message or the migration status of VM's.
def migration_status_all():
    # Looks for all valid VM ids in database.
    # Calls migration_status with those ids.
    migration_status_array = []
    for r in config.db.table('vm'):
        if r['status'] == "running":
            vm_name = r['id']
            vm_id = vm_name[len("qemu/"):]
            status = migration_status(vm_id, "all")
            if (status != None) and (status == 'running'):
                migration_status_array.append(vm_id + " " + str(status))

    # See if the array is empty, so we can add a message.
    if not migration_status_array:
        migration_status_array.append("No migrations in progress.")

    # Returns an array or string.
    return migration_status_array


# Takes VM ID compares it to any known UPID and returns status
def migration_status(vm_id, task_initiator):
    # vm_id is the id of the VM to query.
    # task_initiator is passed to cluster_task_status and is the user that initiated the task.
    # If a task with vm_id is found, grab the UPID and run it to see the task status.
    # Use that upid to get status.
    # If nothing is found, then nothing is running.

    migration_tasks = {}

    migration_tasks_all = cluster_task_status("qmigrate", task_initiator)
    for tasks in migration_tasks_all:
        if tasks["id"] == str(vm_id):
            # Tasks with a attribute of saved = 0 means they are still running. As a VM can only be migrated to one
            # place, two jobs with this state for a VM will not be active. Hence we can presume 0 is running.
            try:
                if tasks["saved"] == '0':
                    migration_tasks = tasks
            except KeyError:
                # If the key 'saved' doesn't exist, then there is a migration literally just starting.
                # For example when returning to the VM menu from the manual migration menu, this can be caused.
                migration_tasks = tasks


    if migration_tasks:
        task_id = migration_tasks["upid"]
        host_node = migration_tasks["node"]
        return_task_status = task_status(task_id, host_node)
        # return status of found task
        return return_task_status
    else:
        # return nothing as nothing was found.
        return None


# Calls the cluster tasks and returns an array of them.
def cluster_task_status(task_type, task_initiator):
    # task_type refers to the type of task being hunter for. This could (for example) 'qmstart' or 'qmigrate'
    # task_initiator is the use that initiated the task. Using 'all' will return all users tasks.
    # To call a specific users tasks it has to be in the format 'user@realm!token' for calling the root user.
    # no token is required.

    tasks_return = []
    task_user_set = False
    if task_initiator != "all":
        task_user_set = True

    for tasks in config.proxmoxAPI.cluster.tasks.get():
        if tasks["type"] == task_type:
            if task_user_set and (tasks["user"] == task_initiator):
                tasks_return.append(tasks)
            elif not task_user_set:
                tasks_return.append(tasks)
    return tasks_return


# Calls the puid task status to see if it is running or stopped.
def task_status(upid, host_node):
    # upid is the task id to be queried.
    # host_node is the host to sent that query to.
    try:
        return_status = (config.proxmoxAPI.nodes(host_node).tasks(upid).status.get()).get('status')
    except:
        return_status = "Error with Host comms."
    return return_status
