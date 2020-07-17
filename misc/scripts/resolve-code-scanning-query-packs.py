import subprocess
import json
import csv
import sys
import os

"""
This script collects CodeQL queries that are part of code scanning query packs
and prints CSV data to stdout that describes which packs contain which queries.

Errors are printed to stderr. This script requires that 'git' and 'codeql' commands
are on the PATH, and should be run either from within a clone of github/codeql,
or in the parent directory thereof. It expects a directory 'codeql-go' as a sibling
of the github/codeql clone.
"""

# Define which languages and query packs to consider
languages = [ "cpp", "csharp", "go", "java", "javascript", "python"]
packs = [ "code-scanning", "security-and-quality", "security-extended" ]

# Define CodeQL search path so it'll find the CodeQL repositories in:
#  - current working directory
#  - the 'codeql' subdirectory of the cwd
#
# (and assumes the codeql-go repo is in a similar location)
codeql_search_path = ".:../codeql-go:codeql:codeql-go"


def prefix_repo_nwo(filename):
    """
    Replaces an absolute path prefix with a GitHub repository name with owner (NWO).
    This function relies on `git` being available and will do a hard sys.exit(1) with
    error message if it's not.

    For example:
        /home/alice/git/ql/java/ql/src/MyQuery.ql  
    becomes:
        github/codeql/java/ql/src/MyQuery.ql
     
    If we can't detect a known NWO (e.g. github/codeql, github/codeql-go), the
    path will be truncated to the root of the git repo:
        ql/java/ql/src/MyQuery.ql
    
    If the filename is not part of a Git repo, the return value is the
    same as the input value: the whole path.
    """
    dirname = os.path.dirname(filename)

    git_version = subprocess.run("git --version", shell=True, capture_output=True, text=True)
    if (git_version.returncode != 0):
        print("Error: your system doesn't have 'git'. Aborting.", file=sys.stderr)
        sys.exit(1)

    git_toplevel_dir_subp = subprocess.run(
        "git -C '%s' rev-parse --show-toplevel"  % dirname,
        shell=True, capture_output=True, text=True
    )

    if git_toplevel_dir_subp.returncode != 0:
        # Not a Git repo
        return filename
    
    git_toplevel_dir = git_toplevel_dir_subp.stdout.strip()
    
    # Detect 'github/codeql' and 'github/codeql-go' repositories by SHA of first commit
    first_sha = subprocess.run(
        "git -C '%s' rev-list --max-parents=0 HEAD" % dirname,
        shell=True, capture_output=True, text=True
    ).stdout.strip()

    if first_sha == "b55526aa58a5b500fe5d1be2c7edd09075711d09": prefix = "github/codeql"
    elif first_sha == "d14eb855fc88e086b587f6c9695b59eb230c79e7": prefix = "github/codeql-go"
    else: prefix = os.path.basename(git_toplevel_dir)

    return os.path.join(prefix, filename[len(git_toplevel_dir)+1:])


def single_spaces(input):
    """
    Workaround for https://github.com/github/codeql-coreql-team/issues/470 which causes
    some metadata strings to contain newlines and spaces without a good reason.
    """
    return " ".join(input.split())

# Create CSV writer and write CSV header to stdout
csvwriter = csv.writer(sys.stdout)
csvwriter.writerow([
    "Query filename", "Suite", "Query name", "Query ID", 
    "Kind", "Severity", "Precision", "Tags"
])

# Iterate over all languages and packs, and resolve which queries are part of those packs
for lang in languages:
    for pack in packs:
        # Get absolute paths to queries in this pack by using 'codeql resolve queries'
        queries_subp = subprocess.run(
            "codeql resolve queries --search-path='%s' '%s-%s.qls'" % (codeql_search_path, lang, pack),
            shell=True, capture_output=True, text=True)

        if queries_subp.returncode != 0:
            print("Couldn't find query pack '%s' for language '%s'. Do you have the right repositories in the right places (search path: '%s')?" % (pack, lang, codeql_search_path)) 
            continue

        # Investigate metadata for every query by using 'codeql resolve metadata'
        for queryfile in queries_subp.stdout.strip().split("\n"):
            query_metadata_json = subprocess.run(
                "codeql resolve metadata '%s'" % queryfile,
                shell=True, capture_output=True, text=True
            ).stdout.strip()
            
            # Turn an absolute path to a query file into an nwo-prefixed path (e.g. github/codeql/java/ql/src/....)
            queryfile_nwo = prefix_repo_nwo(queryfile)

            meta = json.loads(query_metadata_json)

            # Python's CSV writer will automatically quote fields if necessary
            csvwriter.writerow([
                queryfile_nwo, pack, single_spaces(meta['name']), meta['id'],
                meta["kind"], meta["problem.severity"], meta["precision"],
                single_spaces(meta["tags"])
            ])
            