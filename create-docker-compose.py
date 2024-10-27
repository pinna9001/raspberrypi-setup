#!/bin/python

import argparse
import os
import yaml
import shutil
from simple_term_menu import TerminalMenu

DOCKER_COMPOSE_FILE = "docker-compose.yml"
BACKUP_FILE = "backup.sh"

used_ports: set[str] = set()
used_volumes: set[str] = set()
used_service_names: set[str] = set()
used_container_names: set[str] = set()

def get_docker_compose_choices() -> dict[str, str]:
    result: dict[str, str] = dict()
    with os.scandir(input_dir) as dir:
        for entry in dir:
            if entry.is_dir():
                if os.path.exists(os.path.join(entry.path, DOCKER_COMPOSE_FILE)):
                    result[entry.name] = entry.path
    return result

def get_new_name(restricted_names, current_name) -> str:
    current_index = 1
    while True:
        if current_name + "-" + str(current_index) in restricted_names:
            current_index += 1
        else:
            return current_name +  "-" + str(current_index)
    

def gather_possible_collisions_points():
    global docker_compose
    if "services" in docker_compose.keys():
        for service in docker_compose["services"].keys():
            used_service_names.add(service)
            current_service = docker_compose["services"][service]
            if "container_name" in current_service.keys():
                used_container_names.add(current_service["container_name"])
        
            if "ports" in current_service.keys():
                for port_mapping in current_service["ports"]:
                    used_ports.add(port_mapping.split(":")[0])

    if "volumes" in docker_compose.keys():
        for volume in docker_compose["volumes"]:
            used_volumes.add(volume)

def rename_volumes_in_service(service, renamed_volumes):
    if not "volumes" in service.keys():
        return
    for i in range(len(service["volumes"])):
        volume_mapping = service["volumes"][i].split(":")
        if volume_mapping[0] in renamed_volumes.keys():
            volume_mapping[0] = renamed_volumes[volume_mapping[0]]
            service["volumes"][i] = ":".join(volume_mapping)

def change_ports_if_necessary(service):
    if not "ports" in service.keys():
        return
    
    for i in range(len(service["ports"])):
        port_mapping = service["ports"][i].split(":")
        port = port_mapping[0] if len(port_mapping) == 2 else port_mapping[1]
        if port in used_ports:
            while port in used_ports:
                print(f"Port {port} already used in target docker_compose.yml") 
                port = input(f"Enter new port for mapping \"{':'.join(port_mapping)}\": ")
            port_mapping[len(port_mapping) % 2] = port
            service["ports"][i] = ":".join(port_mapping)
        used_ports.add(port)

def update_depends_on(added_services_mapping):
    for service in added_services_mapping.keys():
        current_service = docker_compose["services"][added_services_mapping[service]]
        if "depends_on" in current_service.keys():
            for i in range(len(current_service["depends_on"])):
                depended_service = current_service["depends_on"][i]
                if depended_service in added_services_mapping.keys():
                    current_service["depends_on"][i] = added_services_mapping[depended_service]

def merge_volumes(volumes) -> dict[str, str]:
    renamed_volumes = dict()
    for volume in volumes.keys():
        volume_name = volume
        if volume_name in used_volumes:
            print(f"Volume {volume_name} already used in target docker_compose.yml")
            volume_name = get_new_name(used_volumes, volume_name)
            print(f"Volume {volume} got renamed to {volume_name}")
            renamed_volumes[volume] = volume_name
        docker_compose["volumes"][volume_name] = volumes[volume]
        used_volumes.add(volume_name)
    
    return renamed_volumes

def merge_services(services, renamed_volumes: dict[str, str]) -> None:
    added_services_mapping = dict()
    for service in services.keys():
        service_name = service
        print(service_name)
        if service_name in used_service_names:
            print(f"Service {service_name} already used in target docker_compose.yml")
            service_name = get_new_name(used_service_names, service_name)
            print(f"Service {service} got renamed to {service_name}")
        added_services_mapping[service] = service_name
        used_service_names.add(service_name)
        docker_compose["services"][service_name] = services[service]
        
        current_service = docker_compose["services"][service_name]

        if "container_name" in current_service.keys():
            if current_service["container_name"] in used_container_names:
                current_name = current_service["container_name"]
                print(f"Container name {current_name} already used in target docker_compose.yml")
                current_service["container_name"] = get_new_name(used_container_names, current_name)
                print(f"Container name {current_name} got renamed to {current_service['container_name']}")
            used_container_names.add(current_service["container_name"])
        
        rename_volumes_in_service(current_service, renamed_volumes)
        change_ports_if_necessary(current_service)

    update_depends_on(added_services_mapping)    

def merge_compose_files(selected_service_name: str, selected_service_path: str) -> None:
    print(f"Merging service {selected_service_name} into docker-compocse.yml")
    with open(os.path.join(selected_service_path, DOCKER_COMPOSE_FILE)) as f:
        service_docker_compose = yaml.safe_load(f)

        renamed_volumes = dict()
        if "volumes" in service_docker_compose.keys():
            renamed_volumes = merge_volumes(service_docker_compose["volumes"])

        if "services" in service_docker_compose.keys():
            merge_services(service_docker_compose["services"], renamed_volumes)            

def merge_backup_script_files(selected_service_name: str, selected_service_path: str) -> None:
    global backup_scripts_to_add
    if os.path.exists(os.path.join(selected_service_path, BACKUP_FILE)):
        print(f"Adding backup script for service {selected_service_name}")
        backup_scripts_to_add.append(selected_service_name)

def write_backup_file() -> None:
    output_backup_script_file = os.path.join(output_dir, BACKUP_FILE)
    
    output_dir_abs = os.path.abspath(output_dir)
    BACKUP_SCRIPT_STARTER = f"""cd {output_dir_abs}
backup_file="backup-$(date +"%d%m%Y-%H%M%S").tar"

#insert before

tar -cf $backup_file *.tar.gz docker-compose.yml backup-scripts backup.sh
"""

    backup_script = BACKUP_SCRIPT_STARTER
    if os.path.exists(output_backup_script_file):
        with open(output_backup_script_file) as f:
           backup_script = f.read()

    if not os.path.exists(os.path.join(output_dir, "backup-scripts")):
        os.mkdir(os.path.join(output_dir, "backup-scripts"))

    for service_name in backup_scripts_to_add:
        script_path = os.path.join(input_dir, service_name, BACKUP_FILE)
        new_script_path = os.path.join(output_dir, "backup-scripts", "backup-" + service_name + ".sh")

        shutil.copyfile(script_path, new_script_path)

        index = backup_script.find("#insert before")
        if index == -1:
            print("Can't add script automatically because the target script doesn't contain insert marker.")
        backup_script = backup_script[:index] + str(os.path.join(".", "backup-scripts", "backup-" + service_name + ".sh <container_name>")) + "\n" + backup_script[index:]

    with open(output_backup_script_file, "w") as f:
        f.write(backup_script)

def service_selection_loop(choices:dict[str, str]) -> None:
    options: list[str] = list(choices.keys())
    term_menu = TerminalMenu(options, title = "Services:")
    quit_menu = TerminalMenu(["[y] Yes", "[n] No"], title = "Quit?")
    quit_requested = False

    output_docker_compose_file = os.path.join(output_dir, DOCKER_COMPOSE_FILE)
    
    global docker_compose
    
    docker_compose = dict()
    docker_compose["services"] = dict()
    docker_compose["volumes"] = dict()

    if merge_backup_scripts:
        global backup_scripts_to_add
        backup_scripts_to_add = []

    if os.path.exists(output_docker_compose_file):
        with open(output_docker_compose_file) as f:
            docker_compose = yaml.safe_load(f)
        gather_possible_collisions_points()
    
    while not quit_requested:
        menu_entry_index = term_menu.show()
        
        if menu_entry_index == None:
            pass
        elif type(menu_entry_index) == int:
            merge_compose_files(options[menu_entry_index], choices[options[menu_entry_index]])
            if merge_backup_scripts:
                merge_backup_script_files(options[menu_entry_index], choices[options[menu_entry_index]])
        else:
            # error
            exit(1)

        quit_select = quit_menu.show()
        if quit_select == 0:
           quit_requested = True
           break
    
    with open(output_docker_compose_file, "w") as f:
        yaml.safe_dump(docker_compose, f)
    if merge_backup_scripts:
        write_backup_file()

def main():
    if not os.path.exists(input_dir):
        print("Input path doesn't exist.")
        exit(1)
    if not os.path.exists(output_dir):
        print("Output path doesn't exist.")
        exit(1)
    
    choices: dict[str, str] = get_docker_compose_choices()
    service_selection_loop(choices)

if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(prog = "create-docker-compose.py", description = "Combine multiple docker-compose.ymls and backup scripts")
    parser.add_argument("-i", "--input", help = "The input directory containing a collection of different services.", required = True)
    parser.add_argument("-o", "--output", help = "The output directory", required = True) 
    parser.add_argument("-m", "--merge-backup-scripts", help = "If enabled merge the backup scripts into one big script", action = "store_true")
    arguments = parser.parse_args()
    global input_dir
    input_dir = arguments.input
    global output_dir
    output_dir = arguments.output
    global merge_backup_scripts
    merge_backup_scripts = arguments.merge_backup_scripts
    main()
