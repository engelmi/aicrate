---
name: git-vcs-wiki
description: |
    Build and maintain a local knowledge base from issues, pull requests, source code and git history of Open Source projects. Use when the user wants to list issues or pull requests from a project, view a single issue, get a summary of an issue or search for duplicates, add or update the knowledge base for a project.
license: Complete terms in LICENSE.txt
---


# Git VCS Wiki

A local knowledge base from issues, pull requests, source code and git history of Open Source projects.


## Wiki root

Resolve the wiki root path in this order:

1. Explicit path from the user.
3. Default: `./git-vcs-wiki/` relative to workspace root.

All scripts accept `--root-dir <path>`.


## Scripts

Python scripts are located in the `scripts/` directory next to this file.

**Path resolution:** `<skill-dir>` is the directory containing this `SKILL.md` file. Determine its absolute path and use it when invoking scripts. The wiki root and the skill directory are different locations. Invoke scripts like this:

```bash
python3 <skill-dir>/scripts/fetch_issues.py --root-dir <wiki-root-dir>
```

| Script | Purpose |
|---|---|
| `scripts/setup.sh` | Install commonly used packages. |
| `scripts/fetch_issues.py` | Enrich the raw knowledge base of projects with issues and pull requests. |

The following sections describe how and when to use them.


## Update the wiki

There are multiple parts of the Git VCS Wiki which can be updated:

- Pull Requests and Issues

The following sections describe how to update these parts individually.

### Common prerequisites

Ensure common prerequisites are met by running:

```bash
$ bash <skill-dir>/scripts/setup.sh
```

### Pull Requests and Issues

#### Inputs

**Wiki Root Dir** - the root directory of the Git VCS Wiki
**Project URL** - containing the host, namespace and project name
**--token** - optional, custom API token

#### Fetching pull requests and issues

Install required python packages via `pip install -r <skill-dir>/scripts/requirements.txt`.

Then inform the user that `Fetching the pull requests and issues for <project> takes a while, running it in background` and run the `fetch_issues` python script as a background process:

```bash
$ python <skill-dir>/scripts/fetch_issues.py --root-dir <wiki-root-dir> --project-url <project-url>
```

After the process completes, provide an answer summarizing the project.


## Gotchas

- **Rate Limit exceeded**. When too many API requests are sent in a short interval, the rate limit might get exceeded and a backoff is triggered. Continue monitoring the process in background and provide frequent updates on the remaining duration if possible.

## Answering questions using the Git VCS Wiki

### Summarizing a project

Use only the Git VCS Wiki. Read all files in `<wiki-root-dir>/<platform>/<project name>` and provide a summary using the following format:

```
# Summary of <project name>

Last time update: <last_update_timestamp>

## Data Collected:  

<wiki-root-dir>/<platform>/<project name>
├── issues/
│   ├── open/ (5 issues)
│   └── closed/ (30 issues)
└── pulls/
    ├── open/ (0 PRs)
    └── closed/ (80 PRs)      

## Open Issues:

    List the 5 issues most recently created in the form:
    - #<issue number> - <issue title>

## Common Labels:

    List the 5 most frequently occurring labels:
    - <label>

## Recent Activities:

    List the 5 most recent activities in the form:
    - <create timestamp> - <description of recent activity>

Add an optional note if there is still a background process fetching pull request and issue data for the wiki.
```

## Directory structure

```
<wiki-root>/                -- root directory of the git vcs wiki
├── github/                 -- stored data for projects hosted on github
    ├── <project-1>/        -- data from a specific project
        ├── issues/         -- raw issue data
        │   ├── open/
        │   └── closed/
        ├── pulls/          -- raw pull request data
        │   ├── open/
        │   └── closed/
        └── last_updated    -- contains the timestamp of the last update
├── gitlab/                 -- stored data for projects hosted on gitlab
    ├── <project-2>/        -- data from a specific project
        ├── issues/         -- raw issue data
        │   ├── open/       
        │   └── closed/     
        ├── pulls/          -- raw pull request data
        │   ├── open/       
        │   └── closed/     
        └── last_updated    -- contains the timestamp of the last update
```
