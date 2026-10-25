r"""Time spent at towns that were not taken. One block per game.

A team "at a town" has its leader within 150 m of the flag of a town its side does not own. A visit runs
from the first report that shows a team there to the first that shows none. Short visits that end in a
capture are normal. Long ones are the fault found on 9 October 2026: teams crowd round a flag, the capture
circle is never empty, and the stock mission only counts the circle when it goes from empty to occupied.

Usage:  python tools\at_town.py FOLDER [METRES] [MINUTES]
        FOLDER   a folder of session_*.jsonl logs (default: the logs folder)
        METRES   how near counts as "at the town" (default 150)
        MINUTES  list visits at least this long (default 6)
If the folder holds a manifest_*.json from run_trials.ps1, each game is labelled with its kind and round."""
import json, sys, os, glob, collections, statistics
d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
R = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0
LONG = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
def dist(a, b): return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** .5
labels = {}
for m in glob.glob(os.path.join(d, "manifest_*.json")):
    try:
        for g in json.load(open(m, encoding="utf-8-sig")).get("games", []):
            labels[g.get("session")] = "%s, round %s, %s" % (g.get("kind"), g.get("round"), g.get("start"))
    except (ValueError, OSError):
        pass
for f in sorted(glob.glob(os.path.join(d, "session_*.jsonl"))):
    rows = [r for r in (json.loads(l) for l in open(f, encoding="utf-8", errors="replace") if l.strip().startswith("{")) if isinstance(r.get("state"), dict)]
    rows = [r for r in rows if r["state"].get("towns") and all("pos" in t for t in r["state"]["towns"])]
    if len(rows) < 5:
        continue
    tpos = {t["name"]: t["pos"] for t in rows[0]["state"]["towns"]}
    going = {}; visits = []; prev = 0; at = 0.0; crowd = 0.0; total = 0.0
    for r in rows:
        s = r["state"]; minute = s["minute"]; dt = minute - prev; prev = minute
        owner = {t["name"]: t["owner"] for t in s["towns"]}
        here = collections.defaultdict(list)
        for team in s["teams"][1:]:
            if team["men"] < 3 or "pos" not in team:
                continue
            total += dt
            for name, pos in tpos.items():
                if owner[name] != "us" and dist(team["pos"], pos) <= R:
                    here[name].append(team["name"]); at += dt
                    break
        for name, teams in here.items():
            if len(teams) >= 3:
                crowd += dt * len(teams)
        for name in list(going):
            if name not in here:
                v = going.pop(name); v["end"] = minute
                v["how"] = "taken" if owner[name] == "us" else "left it, still not ours"
                visits.append(v)
        for name, teams in here.items():
            v = going.setdefault(name, {"town": name, "start": minute, "most": 0, "teams": set()})
            v["most"] = max(v["most"], len(teams)); v["teams"] |= set(teams)
    for name, v in going.items():
        v["end"] = rows[-1]["state"]["minute"]; v["how"] = "still there when the game ended, not taken"; visits.append(v)
    taken = [v["end"] - v["start"] for v in visits if v["how"] == "taken"]
    long_ones = sorted((v for v in visits if v["end"] - v["start"] >= LONG), key=lambda v: v["start"])
    recounts = rows[-1]["state"].get("recounts")
    print("\n==== %s%s" % (os.path.basename(f), ("  (%s)" % labels[os.path.basename(f)]) if os.path.basename(f) in labels else ""))
    print("   team-time within %d m of a town not ours: %d%%; of it in a crowd of three or more teams: %d%% of all team-time" % (
        R, round(100 * at / total) if total else 0, round(100 * crowd / total) if total else 0))
    print("   visits: %d, ended in a capture: %d (median %.1f minutes)%s" % (
        len(visits), len(taken), statistics.median(taken) if taken else 0,
        ("; the recount handed %d towns to East, %d to West, %d to the resistance" % (recounts["east"], recounts["west"], recounts["resistance"]))
        if recounts else "; no recount in this game"))
    if not long_ones:
        print("   no visit of %g minutes or more" % LONG)
    for v in long_ones:
        print("   %5.1f to %5.1f (%4.1f min)  %-12s up to %d teams (%s): %s" % (
            v["start"], v["end"], v["end"] - v["start"], v["town"], v["most"], ", ".join(sorted(v["teams"])), v["how"]))
