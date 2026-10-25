r"""For every team in every game: how long it stood still once formed, and where.
Usage:  python tools\standing_still.py logs\session_20261008_*.jsonl"""
import json, sys, glob, os
# For every team: stretches where it stood still (moved < 25 m between reports) with 6 or more men.
# Time a team stood at a flag on the relay's order to hold the town it took (relay 25) is counted apart.
def dist(a, b): return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** .5
for f in sorted(g for a in sys.argv[1:] for g in (glob.glob(a) or [a])):
    rows = [json.loads(l) for l in open(f, encoding="utf-8", errors="replace") if l.strip().startswith("{")]
    rows = [r for r in rows if isinstance(r.get("state"), dict)]
    s1 = rows[-1]["state"]
    print("\n==== %s relay %s mode %s | end towns %d" % (os.path.basename(f)[8:23], rows[0].get("relay"), rows[0]["state"]["mode"], sum(1 for t in s1["towns"] if t["owner"] == "us")))
    names = [t["name"] for t in rows[0]["state"]["teams"]][1:]
    total_idle = 0; total = 0; total_held = 0
    for n in names:
        stretches = []; start = None; anchor = None; idle = 0; prevm = None; full = 0; held = 0
        for r in rows:
            s = r["state"]; t = next(x for x in s["teams"] if x["name"] == n); m = s["minute"]
            dt = (m - prevm) if prevm is not None else 0; prevm = m
            p = t.get("pos")
            if t["men"] >= 6: full += dt
            if t["men"] >= 6 and p and anchor and dist(p, anchor) < 25 and n in (r.get("holding") or {}):
                held += dt           # it stands at a flag because the relay told it to hold the town (relay 25)
                if start is not None and end - start[0] >= 4: stretches.append((start, end))
                start = None
            elif t["men"] >= 6 and p and anchor and dist(p, anchor) < 25:
                idle += dt
                if start is None: start = (lastm, t.get("base_dist"), t["near"], t["metres_from_it"], t["men"], t["has"][:40], t["order"][:10], t["role"])
                end = m
            else:
                if start is not None and end - start[0] >= 4: stretches.append((start, end))
                start = None; anchor = p
            lastm = m
        if start is not None and end - start[0] >= 4: stretches.append((start, end))
        total_idle += idle; total += full; total_held += held
        print("  %-8s %-10s formed %3d' stood still %3d' (%2d%%)%s  %s" % (n, rows[len(rows)//2]["state"]["teams"][names.index(n)+1]["role"][:10], full, idle, 100*idle/max(full,1),
              (", holding a town %d'" % held) if held else "",
              "; ".join("%d-%d' base %sm %s %sm [%d: %s]" % (a[0], e, a[1], a[2], a[3], a[4], a[5]) for a, e in stretches)[:330]))
    print("  all teams: formed %d team-minutes, stood still %d (%d%%)%s" % (total, total_idle, 100*total_idle/max(total,1),
          (", and stood holding a town it had taken %d (%d%%), not counted as standing still" % (total_held, 100*total_held/max(total,1))) if total_held else ""))
