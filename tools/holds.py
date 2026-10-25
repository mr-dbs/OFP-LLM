r"""Hold what you take (relay 25): did holding a town after taking it stop the town being taken straight back?

One block per game: how many towns were taken and how many were lost again, how many holds there were, how
long they lasted and how they ended, what happened at the flag during a hold, and the number that decides
the question: towns lost within three minutes of the holder being released. If that number is high, the
defenders waited the hold out and holding only delayed the loss. A game without holds (a stock game, a
relay before version 25, or --no-hold) shows the first lines only, for comparison.

Usage:  python tools\holds.py FOLDER [TEXT]
        FOLDER   a folder of session_*.jsonl logs (default: the logs folder)
        TEXT     only the logs with this text in their name, for example 20261010_1
If the folder holds a manifest_*.json from run_trials.ps1, each game is labelled with its kind and round,
and the last lines compare the kinds."""
import json, sys, os, glob, collections, statistics
d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
ONLY = sys.argv[2] if len(sys.argv) > 2 else ""
SOON = 3.05          # "straight back": lost within this many minutes
AT_FLAG = 60
def dist(a, b): return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** .5
def med(values): return statistics.median(values) if values else 0
def read_rows(path):
    """The reports of one game. A relay stopped in the middle of a line leaves a broken last line: skipped."""
    rows = []
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.strip().startswith("{"): continue
        try: row = json.loads(line)
        except ValueError: continue
        if isinstance(row.get("state"), dict) and isinstance(row["state"].get("towns"), list): rows.append(row)
    return rows
def why(reason):
    for text, label in (("quiet", "quiet"), ("minutes are up, and the town is not ours", "time up, town not ours"), ("minutes are up", "time up"),
                        ("its order is now", "order changed"), ("no longer fit", "team unfit"), ("team is gone", "team gone"), ("switched off", "switched off")):
        if text in reason: return label
    return reason[:30] or "?"
labels, kinds = {}, {}
for m in glob.glob(os.path.join(d, "manifest_*.json")):
    try:
        for g in json.load(open(m, encoding="utf-8-sig")).get("games", []):
            labels[g.get("session")] = "%s, round %s, %s" % (g.get("kind"), g.get("round"), g.get("start"))
            kinds[g.get("session")] = g.get("kind")
    except (ValueError, OSError):
        pass
table = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(d, "session_*.jsonl"))):
    name = os.path.basename(f)
    if ONLY not in name: continue
    rows = read_rows(f)
    if len(rows) < 5: continue
    last = rows[-1]["state"]; end_minute = last["minute"]
    tpos = {t["name"]: t.get("pos") for t in rows[0]["state"]["towns"]}
    owner_at = [(r["state"]["minute"], {t["name"]: t["owner"] for t in r["state"]["towns"]}) for r in rows]
    def lost_after(town, i):
        """Minutes from report i until the town is first not ours, None if it stays ours to the end."""
        for minute, owners in owner_at[i + 1:]:
            if owners.get(town) != "us": return minute - owner_at[i][0]
        return None
    # towns taken
    captures = []
    for i in range(1, len(rows)):
        for town, owner in owner_at[i][1].items():
            if owner == "us" and owner_at[i - 1][1].get(town) not in (None, "us"):
                captures.append({"i": i, "minute": owner_at[i][0], "town": town, "lost": lost_after(town, i), "held": False})
    # holds: a team named under "holding" in report after report
    holds, running = [], {}
    for i, r in enumerate(rows):
        holding = r.get("holding") or {}
        for team in list(running):
            # ended: the team is no longer named, or the relay says so (it may start a new hold in the same report)
            note = next((n for n in r.get("holds") or [] if n.startswith("%s stops holding %s" % (team, running[team]["town"]))), "")
            if holding.get(team) != running[team]["town"] or note:
                h = running.pop(team); h["end_i"] = i
                h["why"] = why(note.split(": ", 1)[1] if ": " in note else "")
                holds.append(h)
        for team, town in holding.items():
            if team not in running:
                running[team] = {"team": team, "town": town, "i": i, "end_i": None, "why": "game ended"}
    holds += list(running.values())
    for h in holds:
        span = rows[h["i"]: (h["end_i"] if h["end_i"] is not None else len(rows))]
        h["start"] = owner_at[h["i"]][0]
        h["end"] = owner_at[h["end_i"]][0] if h["end_i"] is not None else end_minute
        h["minutes"] = h["end"] - h["start"]
        metres = []
        for r in span:
            team = next((t for t in r["state"]["teams"] if t["name"] == h["team"]), None)
            metres.append(dist(team["pos"], tpos[h["town"]]) if team and team.get("pos") and tpos.get(h["town"]) and team["men"] > 0 else None)
        there = [k for k, m in enumerate(metres) if m is not None and m <= AT_FLAG]
        h["arrived"] = (span[there[0]]["state"]["minute"] - h["start"]) if there else None
        h["metres"] = med([m for m in metres[there[0]:] if m is not None]) if there else None
        h["kills"] = sum(1 for r in span for k in r["state"].get("kills", []) if k.get("near") == h["town"])
        h["own_lost"] = sum(sum(r["state"].get("deaths", {}).get(h["team"], {}).values()) for r in span)
        h["lost_during"] = any(r["state"]["minute"] > h["start"] and o.get(h["town"]) != "us" for r, (_, o) in zip(span, owner_at[h["i"]:]))
        ours_at_release = h["end_i"] is not None and owner_at[h["end_i"]][1].get(h["town"]) == "us"
        h["after"] = lost_after(h["town"], h["end_i"]) if ours_at_release else None
        h["ours_at_release"] = ours_at_release
        for c in captures:
            if c["town"] == h["town"] and c["i"] == h["i"]: c["held"] = True
    quick = [c for c in captures if c["lost"] is not None and c["lost"] <= SOON]
    ours = sum(1 for t in last["towns"] if t["owner"] == "us")
    print("\n==== %s%s | relay %s | %d towns at the end (minute %.0f)" % (name[8:23], ("  (%s)" % labels[name]) if name in labels else "", rows[0].get("relay"), ours, end_minute))
    print("   towns taken %d times (%d different towns); lost again %d, of them %d within 3 minutes of being taken" % (
        len(captures), len({c["town"] for c in captures}), sum(1 for c in captures if c["lost"] is not None), len(quick)))
    kind = kinds.get(name, "?")
    table[kind].append({"towns": ours, "captures": len(captures), "quick": len(quick), "holds": len(holds),
                        "released": 0, "after": 0, "hold_minutes": sum(h["minutes"] for h in holds), "kills": sum(h.get("kills", 0) for h in holds)})
    if not holds:
        print("   no holds in this game (a stock game, a relay before version 25, or --no-hold)")
        continue
    unheld = [c for c in captures if not c["held"]]
    released = [h for h in holds if h["ours_at_release"]]
    soon = [h for h in released if h["after"] is not None and h["after"] <= SOON]
    later = [h for h in released if h["after"] is not None and h["after"] > SOON]
    table[kind][-1].update({"released": len(released), "after": len(soon)})
    team_minutes = len(rows[0]["state"]["teams"][1:]) * (end_minute - rows[0]["state"]["minute"])
    ended = collections.Counter(h["why"] for h in holds)
    print("   holds %d; %d towns taken had no team on TAKE_TOWNS within reach, and %d of those were lost within 3 minutes" % (
        len(holds), len(unheld), sum(1 for c in unheld if c["lost"] is not None and c["lost"] <= SOON)))
    print("   a hold lasted %.1f minutes (median; longest %.1f). All holds: %d team-minutes, %.0f%% of the eight teams' time" % (
        med([h["minutes"] for h in holds]), max(h["minutes"] for h in holds), round(sum(h["minutes"] for h in holds)),
        100 * sum(h["minutes"] for h in holds) / max(team_minutes, 1)))
    print("   how they ended: %s" % ", ".join("%s %d" % (k, v) for k, v in ended.most_common()))
    reached = [h for h in holds if h["arrived"] is not None]
    print("   the holder reached the flag (within %d m) in %d of %d holds, after %.1f minutes (median), and then stood %d m from it (median)" % (
        AT_FLAG, len(reached), len(holds), med([h["arrived"] for h in reached]), round(med([h["metres"] for h in reached]))))
    print("   during the holds: %d kills at the held towns, %d men of the holders lost, the town was lost while held in %d holds" % (
        sum(h["kills"] for h in holds), sum(h["own_lost"] for h in holds), sum(1 for h in holds if h["lost_during"])))
    print("   AFTER THE RELEASE (%d holds that ended with the town ours): lost within 3 minutes %d, lost later %d, kept to the end %d" % (
        len(released), len(soon), len(later), len(released) - len(soon) - len(later)))
    for h in sorted(holds, key=lambda h: h["start"]):
        after = ("town not ours at the release" if not h["ours_at_release"] and h["end_i"] is not None else
                 "" if h["end_i"] is None else "kept to the end" if h["after"] is None else "LOST %.1f min after the release" % h["after"])
        print("      %5.1f %-8s %-13s %3.1f min, %-22s | %s | kills %d, own lost %d%s | %s" % (
            h["start"], h["team"], h["town"][:13], h["minutes"], h["why"],
            "never at the flag" if h["arrived"] is None else "at the flag after %.1f, %3d m from it" % (h["arrived"], round(h["metres"])),
            h["kills"], h["own_lost"], ", lost while held" if h["lost_during"] else "", after))
if len(table) > 1 or any(len(v) > 1 for v in table.values()):
    print("\n==== by kind of game")
    for kind in ("stock", "rules", "model") + tuple(k for k in table if k not in ("stock", "rules", "model")):
        games = table.get(kind)
        if not games: continue
        line = "   %-6s %d games | towns at the end %s (mean %.1f) | taken %s | lost within 3 minutes of being taken %s" % (
            kind, len(games), [g["towns"] for g in games], statistics.mean(g["towns"] for g in games), [g["captures"] for g in games], [g["quick"] for g in games])
        if any(g["holds"] for g in games):
            line += " | holds %s, lost within 3 minutes of the release %s of %s, kills at held towns %s" % (
                [g["holds"] for g in games], [g["after"] for g in games], [g["released"] for g in games], [g["kills"] for g in games])
        print(line)
