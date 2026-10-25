r"""One block per game: towns at 20/40/60 minutes and at the end, model calls, what each team did.
Usage:  python tools\trial_summary.py FOLDER        (a folder of session_*.jsonl logs; default: the logs folder)"""
import json, sys, glob, os, collections, statistics
d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
NAMES = ["Alpha","Bravo","Charlie","Delta","Echo","Foxtrot","Golf","Hotel"]
def dist(a, b): return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** .5
def read_rows(path):
    """Every readable line of a session log. A relay stopped in the middle of a line leaves a broken last line: skipped."""
    out = []
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.strip().startswith("{"): continue
        try: out.append(json.loads(line))
        except ValueError: pass
    return out
ends = []
for f in sorted(glob.glob(os.path.join(d, "session_*.jsonl"))):
    allrows = read_rows(f)
    rows = [r for r in allrows if isinstance(r.get("state"), dict)]
    if not rows: continue
    other = [r for r in allrows if not isinstance(r.get("state"), dict)]
    s0, s1 = rows[0]["state"], rows[-1]["state"]
    def at(m):
        prior = [r for r in rows if r["state"]["minute"] <= m]
        return sum(1 for t in prior[-1]["state"]["towns"] if t["owner"] == "us") if prior else None
    ours = sum(1 for t in s1["towns"] if t["owner"] == "us"); en = sum(1 for t in s1["towns"] if t["owner"] == "enemy"); ends.append(ours)
    built = {}
    for r in rows:
        for b in r["state"]["buildings"]: built.setdefault(b, r["state"]["minute"])
    calls = [r for r in rows if r.get("plan")]; secs = sorted(r.get("seconds", 0) for r in calls)
    gaps = sorted(b["state"]["minute"] - a["state"]["minute"] for a, b in zip(rows, rows[1:]))
    lost = sum(n for r in rows for dd in r["state"]["deaths"].values() for n in dd.values())
    print("\n==== %s | relay %s mode %s | reports %d (+%d rows without a state) | minutes %.1f-%.1f | base near %s ====" % (
        os.path.basename(f)[8:23], rows[0].get("relay"), s0["mode"], len(rows), len(other), s0["minute"], s1["minute"], s0["teams"][1]["near"]))
    print("   towns at 20/40/60: %s/%s/%s | end: %d ours (value %d), %d West | first town %s" % (at(20), at(40), at(60), ours, sum(t["value"] for t in s1["towns"] if t["owner"] == "us"), en,
          next((r["state"]["minute"] for r in rows if any(t["owner"] == "us" for t in r["state"]["towns"])), None)))
    print("   heavy factory at %s | model calls %d, fallbacks %d, errors %d | call seconds median %.1f max %.1f | report gap median %.1f max %.1f | men lost %d" % (
        built.get("heavy factory"), len(calls), sum(1 for r in rows if r.get("fallback")), sum(1 for r in allrows if r.get("error")),
        secs[len(secs)//2] if secs else 0, secs[-1] if secs else 0, gaps[len(gaps)//2], gaps[-1], lost))
    # The model itself: how fast it wrote, and how many plans it did not give in time (relay 24 marks those
    # "model_failed"; before that they were rows with an "error").
    attempts = [a for r in rows for a in ((r.get("decision") or {}).get("attempts") or [])]
    speeds = sorted(a["model"]["eval_count"] / (a["model"]["eval_duration"] / 1e9) for a in attempts
                    if isinstance(a.get("model"), dict) and a["model"].get("eval_duration") and a["model"].get("eval_count"))
    failed = sum(1 for r in rows if r.get("model_failed") or r.get("error"))
    if speeds or failed:
        asked = len(calls) + sum(1 for r in rows if r.get("error"))
        print("   the model: wrote at %s tokens a second (median; slowest %s) | no plan in time for %d of %d reports that needed one%s" % (
            ("%.0f" % speeds[len(speeds)//2]) if speeds else "?", ("%.0f" % speeds[0]) if speeds else "?", failed, max(asked, failed),
            "   <-- NOT a valid model game" if failed * 4 >= max(asked, 1) or (speeds and speeds[len(speeds)//2] < 40) else ""))
    if s1.get("recounts"):
        print("   capture-circle recount handed over: %d towns to East, %d to West, %d to the resistance" % (
            s1["recounts"]["east"], s1["recounts"]["west"], s1["recounts"]["resistance"]))
    for r in other[:3]: print("   ROW WITHOUT STATE:", {k: str(v)[:200] for k, v in r.items() if k != "raw"})
    for r in rows:
        if r.get("error"): print("   error at minute %.1f: %s" % (r["state"]["minute"], str(r["error"])[:160]))
    # orders and roles over time
    standing = {}; prevm = 0; orders = collections.Counter(); roles = collections.defaultdict(collections.Counter)
    for r in rows:
        dt = r["state"]["minute"] - prevm; prevm = r["state"]["minute"]
        if r.get("standing"): standing = r["standing"]
        for n, v in standing.items(): orders[v["order"]] += dt; roles[n][v["role"]] += dt
    tot = sum(orders.values()) or 1
    print("   team-time by order:", {k: "%d%%" % round(100 * v / tot) for k, v in orders.most_common()})
    print("   roles (most of the game):", {n[:3]: roles[n].most_common(1)[0][0] for n in NAMES if roles[n]})
    rule = collections.Counter(); corr = collections.Counter()
    for r in rows:
        for x in r.get("rule_changes") or []: rule[x.split(": ", 1)[1].split(" (")[0]] += 1
        for x in r.get("plan_corrections") or []: corr[x.split(": ", 1)[1].split(" (")[0]] += 1
    print("   rule changes to standing orders:", dict(rule.most_common(8)))
    print("   plan corrections:", dict(corr.most_common(8)))
    # captures
    tpos = {t["name"]: t["pos"] for t in s0["towns"]}; prev = {}; caps = []; lostt = []
    for r in rows:
        s = r["state"]
        for t in s["towns"]:
            b = prev.get(t["name"])
            if b is not None and b != t["owner"]:
                if t["owner"] == "us":
                    who = sorted((dist(tm["pos"], tpos[t["name"]]), tm["name"]) for tm in s["teams"][1:] if tm["men"] > 0 and "pos" in tm)
                    caps.append((s["minute"], t["name"], who[0][1] if who and who[0][0] < 600 else "?"))
                elif b == "us": lostt.append((s["minute"], t["name"], t["owner"]))
            prev[t["name"]] = t["owner"]
    print("   captures (%d): %s" % (len(caps), "; ".join("%.0f' %s %s" % c for c in caps)))
    print("   lost (%d): %s" % (len(lostt), "; ".join("%.0f' %s->%s" % l for l in lostt)))
    hold_notes = [x for r in rows for x in r.get("holds") or []]
    if hold_notes:                     # relay 25: the team that takes a town holds it for a while
        held_minutes = sum((b["state"]["minute"] - a["state"]["minute"]) * len(a.get("holding") or {}) for a, b in zip(rows, rows[1:]))
        print("   holds: %d started, %d team-minutes (%d%% of the eight teams' time). Details: python tools\\holds.py" % (
            sum(1 for x in hold_notes if " holds " in x and "stops holding" not in x), round(held_minutes),
            round(100 * held_minutes / max(1, len(NAMES) * (s1["minute"] - s0["minute"])))))
    bycap = collections.Counter(c[2] for c in caps)
    away = collections.Counter(); dtt = collections.Counter(); first = {}; lostm = collections.Counter(); prevm = 0
    for r in rows:
        s = r["state"]; dt = s["minute"] - prevm; prevm = s["minute"]
        for tm in s["teams"][1:]:
            n = tm["name"]; dtt[n] += dt
            if tm["men"] > 0 and (tm.get("base_dist") or 0) > 400:
                away[n] += dt
                if n not in first and tm["men"] >= 3: first[n] = (s["minute"], tm["men"])
            lostm[n] += sum(s["deaths"].get(n, {}).values())
    def kit(n, m):
        r = min(rows, key=lambda r: abs(r["state"]["minute"] - m)); tm = next(x for x in r["state"]["teams"] if x["name"] == n); return "%d: %s" % (tm["men"], tm["has"][:52])
    for n in NAMES:
        print("   %-8s %-12s left %-5s away %3d%% caps %d lost %2d | 30': %s | 60': %s" % (n, roles[n].most_common(1)[0][0] if roles[n] else "-", ("%.0f'" % first[n][0]) if n in first else "never",
              round(100 * away[n] / max(1, dtt[n])), bycap[n], lostm[n], kit(n, 30), kit(n, 60)))
print("\ntowns held at the end:", ends, "mean %.1f" % statistics.mean(ends))
