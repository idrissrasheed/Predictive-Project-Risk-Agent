import json
from collections import defaultdict

# 1. Count link types per issue
issue_counts = defaultdict(lambda: defaultdict(int))

print("Loading links.ndjson...")
try:
    with open("links.ndjson", "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            link_type = rec["type"]
            
            issue_counts[rec["source"]][link_type] += 1
            issue_counts[rec["target"]][link_type] += 1
except FileNotFoundError:
    print("Error: links.ndjson not found. Please ensure download_jira_data.py has been run.")
    exit(1)

def get_count(issue, t):
    return issue_counts.get(issue, {}).get(t, 0)

scores = {}

print("Computing Structural Fragility Scores...")
for issue in issue_counts.keys():
    cloners = get_count(issue, "Cloners")
    duplicate = get_count(issue, "Duplicate")
    supercedes = get_count(issue, "Supercedes")
    splits = get_count(issue, "Issue split")

    blocker = get_count(issue, "Blocker")
    required = get_count(issue, "Required")
    dependent = get_count(issue, "dependent") + get_count(issue, "Dependent")
    child = get_count(issue, "Child-Issue")

    reference = get_count(issue, "Reference")
    problem_incident = get_count(issue, "Problem/Incident")

    rework_score = 2*cloners + 2*duplicate + 2*supercedes + 1.5*splits
    dependency_score = 3*blocker + 2*required + 2*dependent + 2*child + 2*problem_incident
    coordination_score = 0.1*reference

    risk_index = rework_score + dependency_score + coordination_score

    scores[issue] = {
        "risk_index": risk_index,
        "rework_score": rework_score,
        "dependency_score": dependency_score,
        "coordination_score": coordination_score,
        "reference": reference,
        "cloners": cloners,
        "duplicate": duplicate,
        "supercedes": supercedes,
        "splits": splits,
        "blocker": blocker,
        "required": required,
        "dependent": dependent,
        "child_issue": child,
        "problem_incident": problem_incident
    }

print("\n--- TOP RISK NODES ---")
top = sorted(scores.items(), key=lambda x: x[1]["risk_index"], reverse=True)[:10]

for issue, s in top:
    print(f"\n{issue}  risk_index={s['risk_index']:.2f}")
    print(f"  rework={s['rework_score']:.1f} | dependency={s['dependency_score']:.1f} | coord={s['coordination_score']:.1f}")
    
    # Filter only signals > 0
    signals = {k: v for k, v in s.items() if k in [
        "cloners", "duplicate", "supercedes", "splits", "blocker", 
        "required", "dependent", "child_issue", "problem_incident", "reference"
    ] and v}
    print(f"  signals: {signals}")

print("\nAnalysis complete.")
