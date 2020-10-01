import argparse
from datetime import datetime
import git
import os
import pprint
import time
from lib.clockify_api_call import ClockifyApiCall
from lib.api_call import RequestTypes
from lib.workspace import Workspace

parser = argparse.ArgumentParser(description="Analyzes a set of git commits in the given local git repository, "
                                             "and adds them as time entries to Clockify.")

parser.add_argument("commit", nargs="+", help="Commit hash(es) to be analyzed")
parser.add_argument("--repo-location", "-rl", default=".", nargs="?",
                    help="Path to the git repository to analyze commits [Default: cwd]")

args = parser.parse_args()


def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset


def datetime_from_local_to_utc(local_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return local_datetime - offset


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
passed_commits = list(reversed(passed_commits))
first_commit_start = datetime.fromtimestamp(passed_commits[0].authored_date)

# Check to see if there is a currently-running Clockify timer
workspace = Workspace.get_all()[0]
user_api_call = ClockifyApiCall(RequestTypes.GET, "/user")
user = user_api_call.exec().json()
timers_api_call = ClockifyApiCall(RequestTypes.GET, f"/workspaces/{workspace.id}/user/{user['id']}/time-entries")
timers = timers_api_call.exec().json()

top_timer = timers[0]
timer_running = False
if not top_timer["timeInterval"]["end"]:
    # Timer is running
    print("Timer is running!")
    timer_running = True
    timer_start = datetime_from_utc_to_local(datetime.strptime(top_timer["timeInterval"]["start"], "%Y-%m-%dT%H:%M:%SZ"))
    start = timer_start if timer_start < first_commit_start else first_commit_start

    # Delete running timer (will be replaced with manual time entry)
    delete_running_api_call = ClockifyApiCall(RequestTypes.DELETE,
                                              f"/workspaces/{workspace.id}/time-entries/{top_timer['id']}")
    delete_running_api_call.exec()
else:
    # Timer is not running
    print("Timer was not running - timestamp of the first commit will be used as the 'start' point.")
    start = first_commit_start

print(f"Start: {start}")

# Iterate over passed commits
for commit in passed_commits:
    authored_date = datetime.fromtimestamp(commit.authored_date)
    message = commit.message.strip()

    if authored_date > start:
        # Add time entry
        print(f"Adding commit: {commit}: {message} {authored_date}")

        data = {
            "start": datetime_from_local_to_utc(start).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "description": message,
            "end": datetime_from_local_to_utc(authored_date).strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        # Switch start for the 'next' time entry
        start = authored_date
        new_time_entry_api_call = ClockifyApiCall(RequestTypes.POST, f"/workspaces/{workspace.id}/time-entries",
                                                  data=data)
        new_time_entry_api_call.exec()

        # Wait to allow multiple API calls
        time.sleep(5)

# If the timer was running, restart it
if timer_running:
    data = {
        "start": datetime_from_local_to_utc(datetime.now()).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "description": ""
    }

    start_timer_api_call = ClockifyApiCall(RequestTypes.POST, f"/workspaces/{workspace.id}/time-entries", data=data)
    response = start_timer_api_call.exec()

