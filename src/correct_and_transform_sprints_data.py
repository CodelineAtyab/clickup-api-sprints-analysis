import json
import os

def load_json_data(file_path):
    """Load JSON data from the given file path."""
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json_data(data, file_path):
    """Save JSON data to the given file path."""
    with open(file_path, 'w') as file:
        json.dump(data, ensure_ascii=False, indent=4, fp=file)

def collect_all_team_members(sprints_data):
    """Collect all unique team member names from the sprints data."""
    team_members = set()
    for sprint_obj in sprints_data:
        for sprint_name, sprint_info in sprint_obj.items():
            for assignee in sprint_info.get('list_of_assignees', []):
                team_members.add(assignee)
    return sorted(list(team_members))

def transform_sprint_data(sprints_data, all_team_members):
    """Transform the sprints data according to the requirements."""
    transformed_data = {
        "sprints": [],
        "team_info": all_team_members
    }
    
    for sprint_obj in sprints_data:
        for sprint_name, sprint_info in sprint_obj.items():
            # Skip if not a valid sprint
            if sprint_name == "Product Backlog":
                continue
                
            # Find team member with maximum completed_story_points
            max_points = 0
            max_points_member = None
            for member, member_info in sprint_info.get('delivered_story_points', {}).items():
                completed_points = member_info.get('completed_story_points', 0)
                if isinstance(completed_points, (int, float)) and completed_points > max_points:
                    max_points = completed_points
                    max_points_member = member
            
            if max_points_member:
                # Update committed_story_points to the maximum completed_story_points
                sprint_info['committed_story_points'] = max_points
                
                # Use the list_of_assigned_tasks from the max points member as list_of_unique_tasks_titles
                max_member_tasks = sprint_info['delivered_story_points'][max_points_member].get('list_of_assigned_tasks', [])
                sprint_info['list_of_unique_tasks_titles'] = max_member_tasks
                
                # Recalculate percentage_of_completion for all team members
                for member, member_info in sprint_info.get('delivered_story_points', {}).items():
                    completed_points = member_info.get('completed_story_points', 0)
                    if max_points > 0:
                        member_info['percentage_of_completion'] = (completed_points / max_points) * 100
                    else:
                        member_info['percentage_of_completion'] = 0
                
                # Add no_assigned_tasks_for list
                assigned_members = set(sprint_info.get('list_of_assignees', []))
                all_members_set = set(all_team_members)
                no_assigned_tasks = list(all_members_set - assigned_members)
                sprint_info['no_assigned_tasks_for'] = sorted(no_assigned_tasks)
            
            # Add the transformed sprint to the new structure
            transformed_data['sprints'].append({sprint_name: sprint_info})
    
    return transformed_data

def get_transformed_sprints_data():
    input_file = os.path.join('fetched_sprints_data', 'all_sprints_data.json')
    output_file = os.path.join('fetched_sprints_data', 'transformed_sprints_data.json')
    
    # Ensure the fetched_sprints_data directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Load, transform, and save data
    sprints_data = load_json_data(input_file)
    all_team_members = collect_all_team_members(sprints_data)
    transformed_data = transform_sprint_data(sprints_data, all_team_members)
    save_json_data(transformed_data, output_file)
    
    print(f"Data transformation completed. Results saved to {output_file}")

if __name__ == "__main__":
    get_transformed_sprints_data()
