import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

import pandas as pd
from tqdm import tqdm
from woc.remote import WocMapsRemote

project_urls = [
    "https://github.com/hectornieto/pyTSEB",
    "https://github.com/e3nn/e3nn",
    "https://github.com/kosma/minmea",
    "https://github.com/digantamisra98/Mish",
    "https://github.com/pekkosk/hotbit",
    "https://github.com/metagenomics/denbi-nanopore-training",
    "https://github.com/BNUCNL/dnnbrain",
    "https://github.com/secure-compilation/different_traces",
    "https://github.com/irods/irods",
    "https://github.com/cgre-aachen/gempy",
]
projects = [urlparse(url).path.strip("/") for url in project_urls]
notebook_path = "project_report.ipynb"

# Retrieve every commit SHA from WoC.
woc = WocMapsRemote(base_url="https://worldofcode.org/api/")
project_commits = []
for project in tqdm(projects, desc="Retrieving WoC project commits"):
    woc_project = project.lower().replace("/", "_", 1)
    commits = woc.get_values("p2c", woc_project)
    project_df = pd.DataFrame(commits, columns=["sha1"])
    project_df["project"] = project
    project_commits.append(project_df)
df = pd.concat(project_commits, ignore_index=True)
df = df.drop_duplicates(["project", "sha1"])

# Retrieve commit details in WoC batches of at most 10 commits.
commit_data = []
chunks = [df["sha1"].iloc[i:i + 10] for i in range(0, len(df), 10)]
for chunk in tqdm(chunks, desc="Retrieving WoC commit details"):
    values, errors = woc.get_values_many("commit.tch", chunk.tolist())
    values = {sha: value[0] for sha, value in values.items()}
    if errors:
        print("WoC errors:", errors)
    for commit_sha, commit in values.items():
        commit_data.append(
            {
                "commit": commit_sha,
                "author": commit[2][0],
                "author_time": int(commit[2][1]),
                "message": commit[4],
            }
        )
    time.sleep(1)

df_commit_data = pd.DataFrame(commit_data).merge(
    df, left_on="commit", right_on="sha1", how="inner"
)

# Start from the complete commit list so commits without returned metadata remain rows.
commit_rows = df[["project", "sha1"]].drop_duplicates().merge(
    df_commit_data[
        ["project", "sha1", "author", "author_time", "message"]
    ].drop_duplicates(subset=["project", "sha1"]),
    on=["project", "sha1"],
    how="left",
)

# Required commit-summary CSV with the exact assignment column names.
project_summary = pd.DataFrame(
    {
        "project_wocid": commit_rows["project"].str.lower().str.replace(
            "/", "_", regex=False
        ),
        "commit_sha1": commit_rows["sha1"],
        "author": commit_rows["author"],
        "time": pd.to_datetime(
            commit_rows["author_time"], unit="s", utc=True, errors="coerce"
        ).dt.strftime("%Y-%m-%d"),
        "commit message": commit_rows["message"],
    }
)
project_summary = project_summary[
    ["project_wocid", "commit_sha1", "author", "time", "commit message"]
]
project_summary.to_csv(
    "netid_project_summary.csv", index=False, sep=";", lineterminator="\n"
)

# Keep only the requested CSV output in the working directory.
for csv_name in os.listdir("."):
    if csv_name.lower().endswith(".csv") and csv_name != "netid_project_summary.csv":
        os.remove(csv_name)

# WoC report: commit count, author count, and minimum/maximum author time.
woc_summary = (
    df_commit_data.groupby("project")
    .agg(
        woc_commits=("commit", "nunique"),
        woc_authors=("author", "nunique"),
        woc_min_time=("author_time", "min"),
        woc_max_time=("author_time", "max"),
    )
    .reset_index()
)
woc_summary["woc_min_time"] = pd.to_datetime(
    woc_summary["woc_min_time"], unit="s", utc=True
)
woc_summary["woc_max_time"] = pd.to_datetime(
    woc_summary["woc_max_time"], unit="s", utc=True
)

# GitHub report. Set GITHUB_TOKEN to increase the API rate limit.
def github_request(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "woc-project-report",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


github_rows = []
for project in tqdm(projects, desc="Retrieving GitHub metadata"):
    try:
        repository = github_request(f"https://api.github.com/repos/{project}")
        commits = github_request(
            f"https://api.github.com/repos/{project}/commits?per_page=1"
        )
        github_rows.append(
            {
                "project": project,
                "github_stars": repository["stargazers_count"],
                "github_forks": repository["forks_count"],
                "github_last_commit": (
                    commits[0]["commit"]["author"]["date"] if commits else None
                ),
            }
        )
    except urllib.error.HTTPError as error:
        github_rows.append(
            {
                "project": project,
                "github_stars": None,
                "github_forks": None,
                "github_last_commit": None,
                "github_error": f"HTTP {error.code}",
            }
        )

github_summary = pd.DataFrame(github_rows)
report = woc_summary.merge(github_summary, on="project", how="left")


def markdown_table(frame):
    """Return a small Markdown table suitable for a notebook text cell."""
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for values in frame.astype(str).itertuples(index=False, name=None):
        escaped = [str(value).replace("|", "\\|") for value in values]
        lines.append("| " + " | ".join(escaped) + " |")
    return "\n".join(lines)


github_text = github_summary[
    ["project", "github_stars", "github_forks", "github_last_commit"]
].rename(
    columns={
        "github_stars": "stars",
        "github_forks": "forks",
        "github_last_commit": "last commit date",
    }
)
woc_text = woc_summary[
    ["project", "woc_commits", "woc_authors", "woc_max_time", "woc_min_time"]
].rename(
    columns={
        "woc_commits": "number of commits",
        "woc_authors": "number of authors",
        "woc_max_time": "max time",
        "woc_min_time": "min time",
    }
)

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {"language": "markdown"},
            "source": [
                "# Assigned Project Report\n",
                "\n",
                "Statistics collected from GitHub and the World of Code Python API.\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {"language": "markdown"},
            "source": [
                "## GitHub repository statistics\n",
                "\n",
                markdown_table(github_text) + "\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {"language": "markdown"},
            "source": [
                "## World of Code statistics\n",
                "\n",
                markdown_table(woc_text) + "\n",
            ],
        },
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
with open(notebook_path, "w", encoding="utf-8") as notebook_file:
    json.dump(notebook, notebook_file, indent=2)

print(f"Wrote notebook text report to {notebook_path}")
report