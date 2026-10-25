r"""What the engine says about every team that stood still. One block per game.

Needs games played with the engine patch (apply_llm_engine.py, or the older apply_llm_diag.py) and report
script 12 or later. A team "stands still" when it has three or more men and its leader moves less than 25 m
from one report to the next.

For each game: a count of which order was at the front of the queue of the unit that commands the leader's
vehicle (or of the leader, on foot), over every report in which a team stood still, at base and in the field;
then the three things the trial of 9 October found holding teams, counted in the field (hiding on the
engine's own order, attacking on the engine's own order, and a driver left in command of his vehicle who
still follows the driving order of the commander he lost), with the combat mode those units were in and
how many of them are never handed targets; then what the rest of each team was doing (subgroups away on
the engine's own attack or hide order while the leader stood, and men more than 150 m from their leader
in every report); then each standstill of MINUTES or more with the engine's words at its start, middle
and end.

A team that stands at a flag because the relay told it to hold the town it took (relay 25) is counted on a
line of its own, "holding a town", and not as standing in the field.

Two lines are warnings and are printed only when they apply:
  - a game that reports engine level 2 in which a driver in command still holds a driving order: the fix
    is not in the game that was run (the level comes from the diagnostics file, not from the fixed file)
  - a unit that is never handed targets and stands on the engine's own attack order: a target given to
    it before the mission script reached it

Usage:  python tools\frozen_diag.py FOLDER [MINUTES]
        FOLDER   a folder of session_*.jsonl logs (default: the logs folder)
        MINUTES  list standstills at least this long (default 4)
If the folder holds a manifest_*.json from run_trials.ps1, each game is labelled with its kind and round."""
import json, sys, os, glob, collections
d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LONG = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
def dist(a, b): return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** .5
def words(text): return dict(w.split("=", 1) for w in str(text or "").split() if "=" in w)
def lone_driver_held(w):
    """The unit that commands the vehicle is its driver, and he follows a driving order instead of his subgroup's
    orders. Only a commander who is not the driver gives driving orders, so that commander is gone.
    Games from engine level 2 on print the driving order itself (mm=); older ones show it by plan=VEHICLE."""
    if not w or w.get("id") != w.get("pilot"): return False
    return w.get("mm", "FORMATION") != "FORMATION" or w.get("plan") == "VEHICLE"
def read_rows(path):
    """The reports of one game. A relay that was stopped in the middle of a line leaves a broken last line: skipped."""
    rows = []
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.strip().startswith("{"): continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row.get("state"), dict) and isinstance(row["state"].get("teams"), list): rows.append(row)
    return rows
def front(text):
    w = words(text)
    if not w: return "(no text)"
    if lone_driver_held(w): return "driver holds a lost commander's driving order"
    return "%s/%s" % (w.get("cmd", "?"), w.get("ctx", "-")) if w.get("cmd") != "NONE" else "no order"
labels = {}
for m in glob.glob(os.path.join(d, "manifest_*.json")):
    try:
        for g in json.load(open(m, encoding="utf-8-sig")).get("games", []):
            labels[g.get("session")] = "%s, round %s, %s" % (g.get("kind"), g.get("round"), g.get("start"))
    except (ValueError, OSError):
        pass
for f in sorted(glob.glob(os.path.join(d, "session_*.jsonl"))):
    rows = read_rows(f)
    if len(rows) < 5:
        continue
    name = os.path.basename(f)
    print("\n==== %s%s" % (name, ("  (%s)" % labels[name]) if name in labels else ""))
    if not any(t.get("diag") for r in rows for t in r["state"]["teams"]):
        print("   no engine diagnostics in this game (engine not rebuilt with apply_llm_engine.py, or report script older than 12)")
        continue
    level = next((r["state"]["engine_level"] for r in rows if "engine_level" in r["state"]), None)
    print("   engine level: %s" % ("%d%s" % (level, "" if level >= 2 else "  (the driver fix is NOT in this game)") if level is not None
                                   else "not reported (scripts before the fifth pack of 9 October: diagnostics only)"))
    prev = {}; run = {}; runs = []; tally = collections.Counter(); kicks = collections.defaultdict(list)
    held = collections.Counter(); modes = collections.Counter(); no_targets = 0; with_text = 0
    away = collections.Counter(); behind = 0; team_reports = 0; fix_missing = []; early_target = []
    for r in rows:
        s = r["state"]; minute = s["minute"]
        holding = r.get("holding") or {}
        for k in r.get("kicks") or []:
            if ": kick " in k:
                kicks[k.split(":")[0].split()[0]].append(minute)
        for t in s["teams"][1:]:
            n = t["name"]
            if t["men"] >= 3 and "pos" in t:
                team_reports += 1; behind += t.get("left_behind") or 0
            if t["men"] < 3 or "pos" not in t:
                prev.pop(n, None)
                if n in run: runs.append(run.pop(n))
                continue
            still = n in prev and dist(t["pos"], prev[n]) < 25
            prev[n] = t["pos"]
            if not still:
                if n in run: runs.append(run.pop(n))
                continue
            where = "holding a town" if n in holding else "at base" if (t.get("base_dist") or 0) < 300 else "in the field"
            diag = t.get("diag") or {}
            tally[(where, front(diag.get("vehicle")))] += 1
            w = words(diag.get("vehicle"))
            if w:
                with_text += 1
                modes[w.get("sem", "?")] += 1
                no_targets += 1 if (w.get("noai", "0").isdigit() and int(w["noai"]) & 1) else 0
                if level is not None and level >= 2 and w.get("id") == w.get("pilot") and w.get("mm", "FORMATION") != "FORMATION":
                    fix_missing.append("%s at %.1f (mm=%s)" % (n, minute, w.get("mm")))
                if w.get("noai", "0").isdigit() and int(w["noai"]) & 1 and w.get("cmd") in ("ATTACK", "ATTACKFIRE") and w.get("ctx") in ("AUTO", "AUTOSILENT"):
                    early_target.append("%s at %.1f" % (n, minute))
                for part in str(diag.get("group") or "").split(" / "):
                    g = words(part)
                    if g.get("main") == "0" and g.get("ctx") in ("AUTO", "AUTOSILENT") and g.get("cmd") in ("HIDE", "ATTACK", "ATTACKFIRE") and g.get("n", "0") != "0":
                        away["hide" if g["cmd"] == "HIDE" else "attack"] += 1
                if where == "in the field":
                    if lone_driver_held(w): held["driver"] += 1
                    elif w.get("ctx") in ("AUTO", "AUTOSILENT") and w.get("cmd") in ("HIDE", "ATTACK", "ATTACKFIRE"):
                        held["hide" if w["cmd"] == "HIDE" else "attack"] += 1
            e = run.setdefault(n, {"team": n, "start": minute, "samples": [], "where": where})
            e["end"] = minute
            e["samples"].append((minute, t, diag))
    runs += list(run.values())
    for where in ("at base", "in the field", "holding a town"):
        part = [(k[1], v) for k, v in tally.items() if k[0] == where]
        if where == "holding a town" and not part: continue
        total = sum(v for _, v in part) or 1
        print("   standing %s, order at the front of the queue (%d team-reports): %s" % (
            where, sum(v for _, v in part), ", ".join("%s %d%%" % (k, round(100 * v / total)) for k, v in sorted(part, key=lambda x: -x[1])) or "none"))
    print("   what held the unit commanding the leader's vehicle, in the field (team-reports): hiding on the engine's own order %d, "
          "attacking on the engine's own order %d, a driver holding a lost commander's driving order %d" % (held["hide"], held["attack"], held["driver"]))
    if with_text:
        print("   those units while standing (%d team-reports): combat mode %s; never handed targets %d%%" % (
            with_text, ", ".join("%s %d%%" % (k, round(100 * v / with_text)) for k, v in sorted(modes.items(), key=lambda x: -x[1])),
            round(100 * no_targets / with_text)))
    print("   the rest of each team: subgroups away on the engine's own order while the leader stood: hiding %d, attacking %d; "
          "men more than 150 m from their leader, per team-report: %.2f (%d team-reports)" % (
              away["hide"], away["attack"], behind / team_reports if team_reports else 0, team_reports))
    if fix_missing:
        print("   WARNING: this game reports engine level 2, but a driver in command of his vehicle still holds a driving order: %s%s. "
              "The fix in TransportCore.cpp is not in the game that was run. Run apply_llm_engine.py again and rebuild."
              % (", ".join(fix_missing[:6]), " ..." if len(fix_missing) > 6 else ""))
    if early_target:
        print("   NOTE: a unit that is never handed targets stood on the engine's own attack order: %s%s. "
              "It was given that target before the mission script reached it." % (", ".join(early_target[:6]), " ..." if len(early_target) > 6 else ""))
    long_ones = sorted((e for e in runs if e["end"] - e["start"] >= LONG), key=lambda e: e["start"])
    if not long_ones:
        print("   no standstill of %g minutes or more" % LONG)
    for e in long_ones:
        t0 = e["samples"][0][1]
        kicked = [k for k in kicks.get(e["team"], []) if e["start"] <= k <= e["end"] + 2]
        print("   %-8s %5.1f to %5.1f (%4.1f min) %s, %d m from base, %d men: %s%s" % (
            e["team"], e["start"], e["end"], e["end"] - e["start"], e["where"], t0.get("base_dist") or 0, t0["men"], t0.get("has", "")[:60],
            ("; kicked %d times" % len(kicked)) if kicked else ""))
        picks = [e["samples"][0], e["samples"][len(e["samples"]) // 2], e["samples"][-1]] if len(e["samples"]) > 2 else e["samples"]
        shown = set()
        for minute, t, diag in picks:
            if minute in shown: continue
            shown.add(minute)
            extra = "leader %s, damage %s, split %s" % (t.get("leader_seat"), t.get("leader_vehicle_damage", "-"), t.get("crew_split", "-"))
            print("      %5.1f  %s" % (minute, extra))
            for key, label in (("vehicle", "vehicle "), ("leader", "leader  "), ("group", "subgroups")):
                if diag.get(key) and not (key == "leader" and diag.get("leader") == diag.get("vehicle")):
                    print("             %s %s" % (label, diag[key]))
            if not diag:
                print("             (no text on this report)")
