import os
import json
import subprocess


def extract_xpath_value(pom_file, xpath_expression):
    command = ['./sh/extract_xpath_value.sh', pom_file, xpath_expression]
    output = subprocess.check_output(command, universal_newlines=True)
    return output.strip()


def get_package_name(package_json_file):
    with open(package_json_file) as file:
        data = json.load(file)
        return data.get("name", "")


def get_dependencies(package_json_file):
    with open(package_json_file) as file:
        data = json.load(file)
        dependencies = data.get("dependencies", {})
        print(dependencies)
        return dependencies


def parse_pom_artifacts(pom_file):
    artifacts = []
    xpath_expression = "./ns:project/ns:artifactId"
    artifactId = extract_xpath_value(pom_file, xpath_expression)
    if artifactId is not None:
        artifacts.append(artifactId)
    return artifacts


def parse_pom_dependencies(pom_file):
    dependencies = []
    command = ['./sh/extract_internal_dependencies.sh', pom_file]
    output = subprocess.check_output(command, universal_newlines=True)
    if output is not None and len(output) != 0:
        dependencies = output.strip().split('\n')
    dependencies = [dep for dep in dependencies if dep]
    return dependencies


def parse_all_pom_artifacts_and_dependencies(folder_path):
    artifacts_per_project = {}
    dependencies_per_project = {}
    for project_name in os.listdir(folder_path):
        project_path = os.path.join(folder_path, project_name)
        if project_name not in artifacts_per_project.keys():
            artifacts_per_project[project_name] = []
        if project_name not in dependencies_per_project.keys():
            dependencies_per_project[project_name] = []
        if os.path.isdir(project_path):
            pom_file = os.path.join(project_path, "pom.xml")
            if os.path.isfile(pom_file):
                artifacts = parse_pom_artifacts(pom_file)
                artifacts_per_project[project_name].extend(artifacts)
                dependencies = parse_pom_dependencies(pom_file)
                dependencies_per_project[project_name].extend(dependencies)

            for sub_directory_name in os.listdir(project_path):
                sub_directory_path = os.path.join(project_path, sub_directory_name)
                if os.path.isdir(sub_directory_path):
                    pom_file = os.path.join(sub_directory_path, "pom.xml")
                    if os.path.isfile(pom_file):
                        artifacts = parse_pom_artifacts(pom_file)
                        artifacts_per_project[project_name].extend(artifacts)
                        dependencies = parse_pom_dependencies(pom_file)
                        dependencies_per_project[project_name].extend(dependencies)

    for key, value in artifacts_per_project.items():
        artifacts_per_project[key] = list(set(value))

    for key, value in dependencies_per_project.items():
        dependencies_per_project[key] = list(set(value))

    return artifacts_per_project, dependencies_per_project


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

# Find projects in the folder
projects = find_projects(clone_dir)

artifacts, dependencies = parse_all_pom_artifacts_and_dependencies(clone_dir)

# dependencies = parse_pom_dependencies(
#     '/home/anirudh.ponna/git/test/cloned_projects_full/avx_scheduler/crontab-mgmt/pom.xml')
# print(dependencies)

# Dump projects to a JSON file
json_file_path = "./projects.json"
json_artifact_path = "./artifacts.json"
json_dependencies_path = "./dependencies.json"
dump_projects_to_json(projects, json_file_path)
dump_projects_to_json(artifacts, json_artifact_path)
dump_projects_to_json(dependencies, json_dependencies_path)

# Read projects from the JSON file
projects = read_projects_from_json(json_file_path)
