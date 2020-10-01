import argparse
from datetime import datetime
import git
import os
import pprint
from lib.clockify_api_call import ClockifyApiCall
from lib.api_call import RequestTypes
from lib.workspace import Workspace

parser = argparse.ArgumentParser(description="Analyzes a set of git commits in the given local git repository, "
                                             "and adds them as time entries to Clockify.")

parser.add_argument("commit", nargs="+", help="Commit hash(es) to be analyzed")
parser.add_argument("--repo-location", "-rl", default=".", nargs="?",
                    help="Path to the git repository to analyze commits [Default: cwd]")

args = parser.parse_args()

pp = pprint.PrettyPrinter()

# cd to git repository
os.chdir(args.repo_location)

repo = git.Repo(args.repo_location, search_parent_directories=True)
commits = repo.iter_commits()
passed_commits = []

while True:
    try:
        commit = next(commits)
    except StopIteration:
        break  # Iterator exhausted: stop the loop
    else:
        if any(commit.hexsha.startswith(passed_hash) for passed_hash in args.commit):
            passed_commits.append(commit)

# Reverse to start with the oldest commit
passed_commits = reversed(passed_commits)

# Check to see if there is a currently-running Clockify timer
workspace = Workspace.get_all()[0]
user_api_call = ClockifyApiCall(RequestTypes.GET, "/user")
user = user_api_call.exec().json()
timers_api_call = ClockifyApiCall(RequestTypes.GET, f"/workspaces/{workspace.id}/user/{user['id']}/time-entries")
timers = timers_api_call.exec().json()

top_timer = timers[0]
if not top_timer["timeInterval"]["end"]:
    # Timer is running
    print("Timer is running!")
else:
    # Timer is not running
    print("Timer was not running - timestamp of the first commit will be used as the 'start' point.")

# Iterate over passed commits
for commit in passed_commits:
    authored_date = datetime.fromtimestamp(commit.authored_date)
    message = commit.message.strip()
    print(type(authored_date))
    print(f"{commit}: {message} {authored_date}")
