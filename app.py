from flask import Flask 
from clubhouse import ClubhouseClient
import pandas as pd

app = Flask(__name__)
app.config.from_pyfile("config.py")

# @app.route("/")
# def index():
# 	return "Welcome to the index page."

@app.route("/dashboard/")
def dash():
	clubhouse = ClubhouseClient(app.config["CLUBHOUSE_TOKEN"])

	# MEMBERS TABLE ---------->
	members_json = clubhouse.get("members", json=True)
	# Convert JSON array to pandas DataFrame
	members = pd.json_normalize(members_json) 
	# Keep desired columns
	members = members[["profile.display_icon.url", 
					 "profile.name",
					 "profile.email_address",
					 "profile.mention_name",
					 "role",
					 "profile.deactivated",
					 "profile.two_factor_auth_activated"]]
	# Rename columns
	members.rename(columns= {"profile.display_icon.url": "Profile Photo", 
							"profile.name": "Name",
							"profile.email_address": "Email",
							"profile.mention_name": "Username",
							"role": "Admin",
							"profile.deactivated": "Active",
							"profile.two_factor_auth_activated": "2FA Enabled"},
				   inplace=True)
	# Update "Profile Photo" column so html will display images instead of image paths
	members["Profile Photo"] = [path_to_image_html(path) for path in members["Profile Photo"]]
	# Update "Active" column to be the opposite of the "profile.deactivated" values
	members["Active"] = ~members["Active"]
	# Update "Active" column to display symbols instead of True/False
	members["Active"] = ["&#9989"  if is_active else "&#10060" for is_active in members["Active"]]
	# Update "Admin" column to be True when "role" is "admin"
	members["Admin"] = [role == "admin" for role in members["Admin"]]
	# Update "Admin" column to display symbols instead of True/False
	members["Admin"] = ["&#9989"  if is_admin else "&#10060" for is_admin in members["Admin"]]
	# Update "2FA Enabled" column to display symbols instead of True/False
	members["2FA Enabled"] = ["&#9989"  if is_2fa else "&#10060" for is_2fa in members["2FA Enabled"]]
	# Convert table to html 
	members_html = """<h1>Members</h1>""" + members.to_html(index=False, escape=False)

	# PROJECTS TABLE ---------->
	projects_json = clubhouse.get("projects", json=True)
	projects = pd.json_normalize(projects_json) 
	projects = projects[["name",
						"team_id",
						"stats.num_stories",
						"follower_ids",
						"archived",
						"created_at"]]
	projects.rename(columns= {"name": "Name", 
							 "stats.num_stories": "Stories",
							 "follower_ids": "Followers",
							 "archived": "Active",
							 "created_at": "Created At"},
				    inplace=True)
	# Update the "Followers" column to show counts (and list of followers when hover)
	projects["Followers"] = [hover(f_ids) for f_ids in projects["Followers"]]
	# Update the "Active" column to be the opposite of the "archived" values
	projects["Active"] = ~projects["Active"]
	# Update "Active" column to display symbols instead of True/False
	projects["Active"] = ["&#9989"  if is_active else "&#10060" for is_active in projects["Active"]]
	
	# Create teams table and join it with projects table to get team names
	teams_json = clubhouse.get("teams", json=True)
	teams = pd.json_normalize(teams_json)
	teams = teams[["id", "name"]]
	teams.rename(columns={"id": "team_id", "name": "Team Name"}, inplace=True)
	projects = projects.merge(teams, how="inner", on="team_id")

	# Remove team ids from the projects table, rearrange columns, and convert to html
	projects = projects.drop("team_id", axis=1)
	projects = projects[["Name", "Team Name", "Stories", "Followers", "Active", "Created At"]]
	projects_html = """<h1>Projects</h1>""" + projects.to_html(index=False, escape=False)

	# Combine and return html for members and projects tables
	# Borrowed some of the style elements from here: https://www.w3schools.com/css/css_table.asp
	return """
	<style>
	table {
		border: 1px;
		width: 100%;
	}

	td, th {
		font-family: Arial, Helvetica, sans-serif;
	    border-collapse: collapse;
	    border: 0px;
	    padding: 8px;
	}

	tr:nth-child(even){background-color: #f2f2f2;}

	tr:hover {background-color: #ddd;}

	th {
	    padding-top: 12px;
	    padding-bottom: 12px;
	    text-align: left;
	    background-color: #4082f4;
	    color: white;
	}
	</style>
	""" + members_html + projects_html

def path_to_image_html(path):
	if pd.isnull(path):
		return ""
	return "<img src=\"" + path + "?token=" + app.config["CLUBHOUSE_TOKEN"] + "\">"

def hover(f_ids):
	return "<span title=\"" + str(f_ids) + "\">" + str(len(f_ids)) + "</span>"

