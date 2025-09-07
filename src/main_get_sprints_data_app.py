import os
import requests
import json
import csv

from dotenv import load_dotenv
from src.correct_and_transform_sprints_data import get_transformed_sprints_data

# Load environment variables from .env file
load_dotenv()

# Replace with your actual API token
API_TOKEN = os.getenv("API_TOKEN")

# Replace with your actual team ID
TEAM_ID = os.getenv("TEAM_ID")


def fetch_clickup_data():
    print("Fetching data from ClickUp API...")
    sprint_raw_data = []

    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json"
    }

    # Get all spaces
    response = requests.get(
        f"https://api.clickup.com/api/v2/team/{TEAM_ID}/space",
        headers=headers
    )
    spaces = response.json()["spaces"]

    # For each space, get all folders/lists and tasks
    for space in spaces:
        space_id = space["id"]
        
        # Get folders
        folders_response = requests.get(
            f"https://api.clickup.com/api/v2/space/{space_id}/folder",
            headers=headers
        )
        folders = folders_response.json()["folders"]
        
        for folder in folders:
            folder_id = folder["id"]
            
            # Get lists (sprints)
            lists_response = requests.get(
                f"https://api.clickup.com/api/v2/folder/{folder_id}/list",
                headers=headers
            )
            lists = lists_response.json()["lists"]
            
            for list_item in lists:
                list_id = list_item["id"]
                sprint_name = list_item["name"]
                
                # Get tasks
                tasks_response = requests.get(
                    f"https://api.clickup.com/api/v2/list/{list_id}/task?include_closed=true&include_timl=true",
                    headers=headers
                )
                tasks = tasks_response.json()["tasks"]
                
                for task in tasks:
                    # Extract time estimate and convert to hours
                    time_estimate_hours = 0
                    if "time_estimate" in task and task["time_estimate"]:
                        # Convert milliseconds to hours
                        time_estimate_hours = task["time_estimate"] / 3600000
                    
                    # Get task title
                    task_title = task.get("name", "Untitled Task")
                    
                    # Get task status
                    task_status = task.get("status", {}).get("status", "Unknown")
                    
                    # Get assignees
                    assignees = task.get("assignees", [])
                    
                    if assignees:
                        for assignee in assignees:
                            sprint_raw_data.append({
                                "sprint_name": sprint_name,
                                "assignee": assignee["username"],
                                "time_estimate_hours": time_estimate_hours,
                                "task_title": task_title,
                                "task_id": task["id"],
                                "task_status": task_status
                            })
                    else:
                        # Unassigned tasks
                        sprint_raw_data.append({
                            "sprint_name": sprint_name,
                            "assignee": "Unassigned",
                            "time_estimate_hours": time_estimate_hours,
                            "task_title": task_title,
                            "task_id": task["id"],
                            "task_status": task_status
                        })
    
    return sprint_raw_data


def process_sprint_data(sprint_raw_data):
    print("Processing sprint data...")
    # Group data by sprint
    sprints = {}
    
    for item in sprint_raw_data:
        sprint_name = item["sprint_name"]
        assignee = item["assignee"]
        time_estimate = item["time_estimate_hours"]
        task_title = item["task_title"]
        task_id = item["task_id"]
        
        # Initialize sprint if not exists
        if sprint_name not in sprints:
            sprints[sprint_name] = {
                "list_of_assignees": [],
                "list_of_unique_tasks_titles": [],
                "unique_task_titles": set(),  # Helper to track unique tasks by title
                "committed_story_points": 0,
                "delivered_story_points": {}
            }
        
        # Add assignee if not already in list
        if assignee not in sprints[sprint_name]["list_of_assignees"]:
            sprints[sprint_name]["list_of_assignees"].append(assignee)
            sprints[sprint_name]["delivered_story_points"][assignee] = {
                "list_of_assigned_tasks": [],
                "completed_story_points": 0,
                "percentage_of_completion": 0.0
            }
        
        # Track unique tasks by title and add to total committed points only once
        if task_title not in sprints[sprint_name]["unique_task_titles"]:
            sprints[sprint_name]["unique_task_titles"].add(task_title)
            sprints[sprint_name]["list_of_unique_tasks_titles"].append(task_title)
            sprints[sprint_name]["committed_story_points"] += time_estimate
        
        # Add task to assignee's list if not already there
        if task_title not in sprints[sprint_name]["delivered_story_points"][assignee]["list_of_assigned_tasks"]:
            sprints[sprint_name]["delivered_story_points"][assignee]["list_of_assigned_tasks"].append(task_title)
            # Only add to completed_story_points if the task is in COMPLETE status
            if item["task_status"].lower() == "complete":
                sprints[sprint_name]["delivered_story_points"][assignee]["completed_story_points"] += time_estimate
    
    # Calculate percentage of completion for each assignee
    for sprint_name, sprint_data in sprints.items():
        total_committed = sprint_data["committed_story_points"]
        if total_committed > 0:
            for assignee, assignee_data in sprint_data["delivered_story_points"].items():
                completed = assignee_data["completed_story_points"]
                assignee_data["percentage_of_completion"] = (completed / total_committed) * 100
    
    # Remove the helper set before serializing to JSON
    for sprint_data in sprints.values():
        sprint_data.pop("unique_task_titles", None)
    
    # Convert to the final format: list of dicts with sprint name as key
    final_sprints = []
    for sprint_name, sprint_data in sprints.items():
        final_sprints.append({sprint_name: sprint_data})
    
    return final_sprints


def save_to_json(data, filename):
    print(f"Saving data to {filename}...")
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def generate_csv_from_json(json_file, csv_file):
    print(f"Generating CSV from {json_file}...")
    # Read the JSON data
    with open(json_file, "r") as f:
        sprints_data = json.load(f)
    
    # Prepare data for CSV
    csv_data = []
    
    for sprint_dict in sprints_data:
        for sprint_name, sprint_info in sprint_dict.items():
            for assignee, assignee_data in sprint_info["delivered_story_points"].items():
                csv_data.append([
                    sprint_name,
                    assignee,
                    assignee_data["completed_story_points"]
                ])
    
    # Write to CSV
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Sprint", "Team Member", "Story Points Delivered"])
        writer.writerows(csv_data)
    
    print(f"Data exported to {csv_file}")

def get_updated_sprints_data():
    # Fetch data from ClickUp API
    sprint_raw_data = fetch_clickup_data()
    
    # Process data into required structure
    sprints_data = process_sprint_data(sprint_raw_data)

    # Create fetched_sprints_data directory if not exist
    os.makedirs("fetched_sprints_data", exist_ok=True)

    # Save to JSON file
    json_file = "fetched_sprints_data/all_sprints_data.json"
    save_to_json(sprints_data, json_file)
    
    # Generate CSV from JSON
    csv_file = "fetched_sprints_data/sprints_data.csv"
    generate_csv_from_json(json_file, csv_file)

    # Transform all_sprints_data.json data using the existing transformation function
    get_transformed_sprints_data()

if __name__ == "__main__":
    get_updated_sprints_data()