import logging
import os
import json
import subprocess
import sys

from sqlalchemy import create_engine, text, insert


# from db.src.postgres.common.sqlAlchemy import SQLAlchemyProcessor as PostgresProcessor

def export_env_variables():
    # Define the path to your shell script
    script_path = "./sh/export_env_variables.sh"

    # Execute the shell script
    subprocess.call(script_path)


def connect_to_db():
    dbUserName = os.environ.get('dbUserName')
    dbPassword = os.environ.get('dbPassword')
    dbPort = os.environ.get('dbPort')
    dbHost = os.environ.get('dbHost')
    dbSchema = 'prod'
    dbURI = f"postgresql://{dbUserName}:{dbPassword}@{dbHost}:{dbPort}/{dbSchema}"
    logging.debug(f"dbURI: {dbURI} ")
    sqlp = create_engine(dbURI, echo=True)
    return sqlp


def getResultsFromSQL(sqlp, sqlQuery):
    str_sql = text(sqlQuery)
    results = sqlp.connect().execute(str_sql).fetchall()
    return results


def get_build_hierarchy(sqlp):
    sql_query = "select git_repo_name from release_build_hierarchy where release_collection_id=1 and git_repo_name " \
                "not in (select git_repo_name from git_repos where is_builder)"
    projects = getResultsFromSQL(sqlp, sql_query)
    projects = [result[0] for result in projects]
    return projects


def change_to_list_and_dump_to_json(dictionary, filename):
    dictionary_list_val = {}
    for key, val in dictionary.items():
        if type(val) == set:
            dictionary_list_val[key] = list(val)
        else:
            dictionary_list_val[key] = val

    dump_projects_to_json(dictionary_list_val, filename)


def remove_self_dependencies(adjacency_list):
    adjacency_list_without_self_loops = {}
    for key, val in adjacency_list.items():
        adjacency_list_without_self_loops[key] = set()
        for dependency in val:
            if dependency == key:
                continue
            adjacency_list_without_self_loops[key].add(dependency)
    return adjacency_list_without_self_loops


def build_order(artifacts_per_project, dependencies_per_project):
    # Create a reverse mapping of artifacts to projects
    artifact_to_project = {}
    for project, artifacts in artifacts_per_project.items():
        for artifact in artifacts:
            artifact_to_project[artifact] = project

    change_to_list_and_dump_to_json(artifact_to_project, './artifacts_to_project.json')
    adjacency_list = {}
    for project, dependencies in dependencies_per_project.items():
        adjacency_list[project] = set()
        for dependency in dependencies:
            if dependency != project and dependency in artifact_to_project:
                adjacency_list[project].add(artifact_to_project[dependency])

    adjacency_list = remove_self_dependencies(adjacency_list)
    change_to_list_and_dump_to_json(adjacency_list, './project_to_project.json')

    # Initialize a dictionary to store the levels of each project
    project_to_levels = {}
    levels_to_project = {}
    level = 1

    # Perform topological sorting
    while adjacency_list:
        # Find projects with no remaining dependencies
        projects_with_no_dependencies = [
            project for project, dependencies in adjacency_list.items() if len(dependencies) == 0
        ]

        if not projects_with_no_dependencies:
            # There are remaining dependencies, but they form a cycle
            raise Exception("Dependency cycle detected")

        # Remove the projects with no dependencies from the adjacency list
        for project in projects_with_no_dependencies:
            del adjacency_list[project]
            project_to_levels[project] = level
            if level not in levels_to_project:
                levels_to_project[level] = []
            levels_to_project[level].append(project)

            # Remove the project from the dependencies of other projects
            for dependencies in adjacency_list.values():
                dependencies.discard(project)

        level += 1

    change_to_list_and_dump_to_json(levels_to_project, "./levels_to_project.json")
    return levels_to_project



def build_order_check(artifacts_per_project, dependencies_per_project):
    # Create a reverse mapping of artifacts to projects
    artifact_to_project = {}
    for project, artifacts in artifacts_per_project.items():
        for artifact in artifacts:
            artifact_to_project[artifact] = project

    change_to_list_and_dump_to_json(artifact_to_project, './artifacts_to_project.json')
    adjacency_list = {}
    for project, dependencies in dependencies_per_project.items():
        adjacency_list[project] = set()
        for dependency in dependencies:
            if dependency != project and dependency in artifact_to_project:
                adjacency_list[project].add(artifact_to_project[dependency])

    adjacency_list = remove_self_dependencies(adjacency_list)
    change_to_list_and_dump_to_json(adjacency_list, './project_to_project.json')

    # Initialize a dictionary to store the levels of each project
    project_to_levels = {}
    levels_to_project = {}
    level = 1
    path = []  # Track the path while performing topological sorting

    def topological_sort(project):
        nonlocal level, path

        if project in path:
            cycle_start = path.index(project)
            cyclic_path = path[cycle_start:]
            raise Exception(f"Dependency cycle detected: {cyclic_path}")

        path.append(project)

        dependencies = adjacency_list.get(project, set())
        for dependency in dependencies:
            topological_sort(dependency)

        path.pop()

        if project not in project_to_levels:
            project_to_levels[project] = level
            if level not in levels_to_project:
                levels_to_project[level] = []
            levels_to_project[level].append(project)

        level += 1

    try:
        # Perform topological sorting for each project
        for project in adjacency_list.keys():
            topological_sort(project)
    except Exception as e:
        print(e)
        return None

    change_to_list_and_dump_to_json(levels_to_project, "./levels_to_project.json")
    return levels_to_project


def extract_xpath_value(pom_file, xpath_expression):
    command = ['./sh/extract_xpath_value.sh', pom_file, xpath_expression]
    output = subprocess.check_output(command, universal_newlines=True)
    return output.strip()


def parse_npm_artifacts(package_json_file):
    artifacts = []
    with open(package_json_file, 'r') as file:
        data = json.load(file)
        artifactName = data.get("name", "")
        artifacts.append(artifactName)
        return artifacts


def parse_npm_dependencies(package_json_file):
    with open(package_json_file, 'r') as file:
        data = json.load(file)
        dependencies = data.get("dependencies", {})
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


def parse_all_artifacts_and_dependencies(folder_path, build_hierarchy_projects):
    artifacts_per_project = {}
    dependencies_per_project = {}
    for project_name in os.listdir(folder_path):
        if project_name in build_hierarchy_projects:
            project_path = os.path.join(folder_path, project_name)
            if project_name not in artifacts_per_project.keys():
                artifacts_per_project[project_name] = []
            if project_name not in dependencies_per_project.keys():
                dependencies_per_project[project_name] = []
            if os.path.isdir(project_path):
                pom_file = os.path.join(project_path, "pom.xml")
                package_file = os.path.join(project_path, "package.json")

                if os.path.isfile(pom_file):
                    artifacts = parse_pom_artifacts(pom_file)
                    artifacts_per_project[project_name].extend(artifacts)
                    dependencies = parse_pom_dependencies(pom_file)
                    dependencies_per_project[project_name].extend(dependencies)

                if os.path.isfile(package_file):
                    artifacts = parse_npm_artifacts(package_file)
                    artifacts_per_project[project_name].extend(artifacts)
                    dependencies = parse_npm_dependencies(package_file)
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

                        if os.path.isfile(package_file):
                            artifacts = parse_npm_artifacts(package_file)
                            artifacts_per_project[project_name].extend(artifacts)
                            dependencies = parse_npm_dependencies(package_file)
                            dependencies_per_project[project_name].extend(dependencies)

    for key, value in artifacts_per_project.items():
        artifacts_per_project[key] = list(set(value))

    for key, value in dependencies_per_project.items():
        dependencies_to_keep = []
        for dependency in value:
            found = False
            for project, artifacts in artifacts_per_project.items():
                if dependency in artifacts:
                    found = True
                    break
            if found:
                dependencies_to_keep.append(dependency)
        dependencies_per_project[key] = list(set(dependencies_to_keep))
    return artifacts_per_project, dependencies_per_project


def find_projects(folder_path, build_hierarchy_projects):
    projects = []

    for project_name in os.listdir(folder_path):
        if project_name in build_hierarchy_projects:
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
        json.dump(projects, f, indent=4, sort_keys=True)


def read_projects_from_json(json_file_path):
    with open(json_file_path, "r") as f:
        projects = json.load(f)
    return projects


if __name__ == "__main__":
    export_env_variables()
    sqlp = connect_to_db()
    build_hierarchy_projects = get_build_hierarchy(sqlp)
    clone_dir = os.path.abspath("/home/anirudh.ponna/git/test/cloned_projects_full")

    # Find projects in the folder
    projects = find_projects(clone_dir, build_hierarchy_projects)

    artifacts, dependencies = parse_all_artifacts_and_dependencies(clone_dir, build_hierarchy_projects)
    # dependencies = parse_pom_dependencies(
    #     '/home/anirudh.ponna/git/test/cloned_projects_full/avx_scheduler/crontab-mgmt/pom.xml')
    # print(dependencies)

    # Dump projects to a JSON file
    json_file_path = "./projects.json"
    json_artifact_path = "./project_to_artifacts.json"
    json_dependencies_path = "./project_to_dependencies.json"
    json_artifacts_to_project = "./artifacts_to_project.json"
    json_project_to_project = "./project_to_project.json"
    dump_projects_to_json(projects, json_file_path)
    dump_projects_to_json(artifacts, json_artifact_path)
    dump_projects_to_json(dependencies, json_dependencies_path)

    project_to_project = build_order_check(artifacts, dependencies)

    print("Artifacts length:", len(artifacts))
    print("Dependencies length:", len(dependencies))

    # Read projects from the JSON file
    projects = read_projects_from_json(json_file_path)
