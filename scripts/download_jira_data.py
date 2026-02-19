import json
import time
import requests

jira_url = "https://issues.apache.org/jira"
search_url = jira_url + "/rest/api/2/search"

# Removed issueLinkType because the API doesn't support 'is not EMPTY' on that field
jql = "project = SPARK AND created >= -730d ORDER BY created DESC"

fields = [
    "key","created","updated","resolutiondate","duedate",
    "status","issuetype","priority","assignee","issuelinks"
]

startAt = 0
maxResults = 100  # Jira typically allows up to 100
out_path = "issues.ndjson"
out_links = "links.ndjson"

def safe_get(d, path, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

print(f"Downloading issues matching: {jql}")

with open(out_path, "w", encoding="utf-8") as out:
    while True:
        params = {
            "jql": jql,
            "startAt": startAt,
            "maxResults": maxResults,
            "fields": ",".join(fields),
        }
        r = requests.get(search_url, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()

        issues = data.get("issues", [])
        if not issues:
            break

        for issue in issues:
            out.write(json.dumps(issue) + "\n")

        startAt += len(issues)
        total = data.get("total", "?")
        print(f"Downloaded {startAt} / {total}")

        if startAt >= total:
            break

        time.sleep(0.2)  # be polite to the API

print(f"Saved: {out_path}")

print("Extracting links to links.ndjson...")
with open(out_path, "r", encoding="utf-8") as f_in, open(out_links, "w", encoding="utf-8") as f_out:
    for line in f_in:
        issue = json.loads(line)
        src = issue.get("key")
        links = safe_get(issue, ["fields", "issuelinks"], []) or []
        for l in links:
            ltype = safe_get(l, ["type", "name"])
            inward = safe_get(l, ["inwardIssue", "key"])
            outward = safe_get(l, ["outwardIssue", "key"])

            # Normalize direction: create edges src -> target when outward exists,
            # and inward -> src when inward exists
            if outward:
                f_out.write(json.dumps({"source": src, "target": outward, "type": ltype, "direction": "outward"}) + "\n")
            if inward:
                f_out.write(json.dumps({"source": inward, "target": src, "type": ltype, "direction": "inward"}) + "\n")

print(f"Saved: {out_links}")
