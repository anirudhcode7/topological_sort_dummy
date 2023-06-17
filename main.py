import os
import json
from xml.etree import ElementTree as ET


def parse_pom_artifacts(pom_file):
    artifacts = []

    try:
        tree = ET.parse(pom_file)
        root = tree.getroot()
        build_element = root.find("./build")
        if build_element is not None:
            plugins_element = build_element.find("./plugins")
            if plugins_element is not None:
                for plugin_element in plugins_element.findall("./plugin"):
                    artifact_id_element = plugin_element.find("./artifactId")
                    if artifact_id_element is not None:
                        artifacts.append(artifact_id_element.text.strip())
    except (ET.ParseError, IOError):
        pass

    return artifacts


def find_projects(folder_path):
    projects = []

    for project_name in os.listdir(folder_path):
        project_path = os.path.join(folder_path, project_name)
        if os.path.isdir(project_path):
            pom_file = os.path.join(project_path, "pom.xml")
            package_file = os.path.join(project_path, "package.json")

            if os.path.isfile(pom_file):
                projects.append({
                    "type": "java",
                    "name": project_name,
                    "pom_file": pom_file
                })
            elif os.path.isfile(package_file):
                projects.append({
                    "type": "node",
                    "name": project_name,
                    "package_file": package_file
                })

            for sub_dir_name in os.listdir(project_path):
                sub_dir_path = os.path.join(project_path, sub_dir_name)
                if os.path.isdir(sub_dir_path):
                    pom_file = os.path.join(sub_dir_path, "pom.xml")
                    package_file = os.path.join(sub_dir_path, "package.json")
                    if os.path.isfile(pom_file):
                        projects.append({
                            "type": "java",
                            "name": project_name,
                            "pom_file": pom_file
                        })
                    elif os.path.isfile(package_file):
                        projects.append({
                            "type": "node",
                            "name": project_name,
                            "package_file": package_file
                        })
    return projects


def dump_projects_to_json(projects, json_file_path):
    with open(json_file_path, "w") as f:
        json.dump(projects, f, indent=4)


def read_projects_from_json(json_file_path):
    with open(json_file_path, "r") as f:
        projects = json.load(f)
    return projects


clone_dir = os.path.abspath("/home/anirudh.ponna/git/test/cloned_projects_full")
print(clone_dir)

# Find projects in the folder
projects = find_projects(clone_dir)

# Dump projects to a JSON file
json_file_path = "./projects.json"
dump_projects_to_json(projects, json_file_path)

# Read projects from the JSON file
projects = read_projects_from_json(json_file_path)
