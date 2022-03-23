from csv import writer
from datetime import datetime, timedelta
import os

from github import Github

from parse_pr_comments import get_all_reruns

access_token = os.getenv("GITHUB_ACCESS_TOKEN")
g = Github(access_token)
pipelines = g.get_repo("tektoncd/pipeline")
pulls = pipelines.get_pulls(state="all")
cutoff_datetime = datetime.now() - timedelta(days=182) # six months ago
output = [] # list of [test name, PR, date, rerun count]
for pull in pulls:
    try:
        if pull.created_at < cutoff_datetime:
           break
        reruns = get_all_reruns(pull)
        for testname, count in reruns.items():
            if count == 0:
                continue
            output.append([testname, pull.number, pull.created_at.date(), count])
    except Exception as e:  # Probably rate limited
        print("Exception: %s", e)
        break

with open("rerun_counts.csv", "w", newline="") as f:
    w = writer(f, dialect="excel")
    w.writerow(["Test Name", "PR", "Date", "Rerun Count"])
    w.writerows(output)
