import json

def generate_gitlab_ci(levels, projects, branch_name):
    gitlab_ci_content = ""

    # Add GitLab CI configuration header
    gitlab_ci_content += "stages:\n"

    # Add stages based on the levels
    for level in range(1, len(levels) + 1):
        gitlab_ci_content += f"  - level-{level}\n"

    gitlab_ci_content += "\n"

    # Add jobs for each project
    for project in projects:
        project_name = project["name"]
        project_stage = project["stage"]

        gitlab_ci_content += f"{project_name}:\n"
        gitlab_ci_content += f"  stage: {project_stage}\n"
        gitlab_ci_content += "  trigger:\n"
        gitlab_ci_content += f"    project: release_management/{project_name}\n"
        gitlab_ci_content += f"    branch: {branch_name}\n"
        gitlab_ci_content += "    strategy: depend\n"
        gitlab_ci_content += "\n"

    return gitlab_ci_content


# Read the levels and projects from the JSON file
def read_levels_projects_from_json(json_file_path):
    with open(json_file_path, "r") as json_file:
        data = json.load(json_file)
        levels = data
        projects = []
        for level, projects_at_level in data.items():
            for project_name in projects_at_level:
                project = {
                    "name": project_name,
                    "stage": f"level-{level}"
                }
                projects.append(project)
        return levels, projects


# Main function to generate the .gitlab-ci.yml file
def generate_gitlab_ci_yaml(json_file_path, output_file_path, branch_name):
    levels, projects = read_levels_projects_from_json(json_file_path)
    gitlab_ci_content = generate_gitlab_ci(levels, projects, branch_name)

    # Write the .gitlab-ci.yml file
    with open(output_file_path, "w") as output_file:
        output_file.write(gitlab_ci_content)


# Example usage
json_file_path = "./levels_to_project.json"
output_file_path = ".gitlab-ci.yml"
branch_name = "CAV-FEATURE-TOPOSORT-EXP"
generate_gitlab_ci_yaml(json_file_path, output_file_path, branch_name)
