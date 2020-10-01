# Git Clockify Timer
This utility converts Git commits into Clockify entries using the timestamps and messages of Git commits.

## Dependencies
This utility depends the following Python libraries, which can all be installed via pip:
- `gitpython`

This utility also depends on another utility, the `jira-clockify-time-tracker`, for its Clockify API calls.
That utility can be found on [GitHub](https://github.com/JohnBarton27/jira-clockify-time-tracker). Be sure to add the 
Jira Clockify Time Tracker to your Python path.

# How to run
1. When you begin work for a session, start a new Clockify timer.
2. At any point during your work session, pass any number of consecutive commit hashes for a given local git repository 
to the `analyze_commits.py` script.
3. When you are done working, kill (discard) your running Clockify timer.

## Additional Automation
For a more seamless integration, it is recommended to tie your Clockify timer start to another command that also opens 
your IDE/etc., so that it is started automatically when you begin work.

Running the `analyze_commits.py` script can be done as part of your existing continuous integration process (using a 
tool like Jenkins, Bamboo, etc.) each time you "push" to your branch.

Killing the Clockify timer can also be tied to a "shutdown" command/script for your development environment.