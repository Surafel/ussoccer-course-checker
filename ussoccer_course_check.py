#!/usr/bin/env python3
"""Daily check for in-person U.S. Soccer grassroots 4v4 / 7v7 coaching courses.

Queries the public Learning Center API (the same one used by
https://learning.ussoccer.com/coach/courses/available/22/list), prints the
upcoming courses, and flags any not seen on a previous run.

Env overrides:
  USSOCCER_STATES   comma-separated state codes, or "ALL" (default: CA)
"""
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

API = "https://learning.ussoccer.com/api/coach/v2/courses"
CATEGORIES = {22: "4v4 In-Person", 21: "7v7 In-Person"}
STATUSES = "scheduled,registration,waitlist,application"
STATES = [s.strip().upper() for s in os.environ.get("USSOCCER_STATES", "CA").split(",") if s.strip()]
# Stored inside the repo (rather than under the home directory) so the "seen"
# state survives across ephemeral/cloud runs that start from a fresh clone.
SEEN_FILE = os.environ.get(
    "USSOCCER_SEEN_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "ussoccer_seen_courses.json"),
)
COURSE_URL = "https://learning.ussoccer.com/coach/courses/available/{cat}/details/{id}"


def fetch(category, state):
    courses, page = [], 1
    while True:
        params = {
            "id_category": category,
            "order_by": "start_date",
            "order_dir": "asc",
            "with": "course_location_primary",
            "visibilities": "published",
            "statuses": STATUSES,
            "current_page": page,
        }
        if state != "ALL":
            params["primary_location_state"] = state
        req = urllib.request.Request(
            f"{API}?{urllib.parse.urlencode(params)}",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.load(r)
        courses += body.get("data", [])
        pag = body.get("pagination", {})
        if page >= pag.get("last_page", 1):
            return courses
        page += 1


def main():
    today = dt.date.today().isoformat()
    try:
        seen = set(json.load(open(SEEN_FILE)))
    except (OSError, ValueError):
        seen = set()

    found = []
    for cat, label in CATEGORIES.items():
        for state in STATES:
            for c in fetch(cat, state):
                # The API still returns some past courses marked "scheduled".
                if (c.get("start_date") or "")[:10] < today:
                    continue
                found.append((cat, label, c))

    new = [f for f in found if str(f[2]["id_course"]) not in seen]
    print(f"U.S. Soccer in-person 4v4/7v7 check ({', '.join(STATES)}) — {dt.datetime.now():%Y-%m-%d %H:%M}")
    if not found:
        print("No upcoming in-person 4v4 or 7v7 courses listed.")
    for cat, label, c in found:
        loc = c.get("course_location_primary") or {}
        tag = "NEW " if (cat, label, c) in new else ""
        print(
            f"- {tag}[{label}] {c['title']}\n"
            f"    {c['start_date'][:10]} | {c['status']} | {loc.get('city', '?')}, {loc.get('state', '?')}"
            f" | limit {c.get('candidate_limit')}\n"
            f"    {COURSE_URL.format(cat=cat, id=c['id_course'])}"
        )

    if new:
        try:
            subprocess.run(
                ["notify-send", "-a", "OpenClaw", "U.S. Soccer courses",
                 f"{len(new)} new in-person 4v4/7v7 course(s) listed"],
                timeout=10, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass

    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen | {str(c["id_course"]) for _, _, c in found}), f)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # surface failures in the cron run log
        print(f"Course check failed: {e}", file=sys.stderr)
        sys.exit(1)
