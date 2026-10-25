r"""Every vehicle team from its first vehicle to its last: what it had, how much of that time it stood still,
whether it ever left base, and the share of tanks, Shilkas and carriers.
Usage:  python tools\vehicle_teams.py logs\session_20261008_*.jsonl"""
import json, sys, os, re, collections, glob
# One "life" of a vehicle team = from the report it first has a vehicle until it has none again.
# For each life: what was the first vehicle (the leader drives it), and how much of the life the team stood still.
def dist(a, b): return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** .5
def vehicles(has):
    out = collections.Counter()
    for part in has.split(", "):
        m = re.match(r"(\d+) x (.+)", part)
        if not m: continue
        n, what = int(m.group(1)), m.group(2)
        if "Shilka" in what: out["shilka"] += n
        elif "tank" in what and "anti-tank" not in what: out["tank"] += n
        elif "BMP" in what or "carrier" in what: out["apc"] += n
    return out
allv = collections.defaultdict(lambda: [0, 0.0, 0.0, 0]); tot = collections.defaultdict(collections.Counter)
for f in sorted(g for a in sys.argv[1:] for g in (glob.glob(a) or [a])):
    rows = [json.loads(l) for l in open(f, encoding="utf-8", errors="replace") if l.strip().startswith("{")]
    rows = [r for r in rows if isinstance(r.get("state"), dict)]
    kind = "stock" if rows[0]["state"]["mode"] == 0 else "relay %s" % rows[0].get("relay")
    names = [t["name"] for t in rows[0]["state"]["teams"]][1:]
    print("\n== %s %s" % (os.path.basename(f)[8:23], kind))
    for n in names:
        life = None; prevm = None; prevp = None
        def close(life):
            if life and life["mins"] >= 5:
                print("   %-8s %2d-%2d'  first %-6s  later %-22s  stood still %3d%% of %2d'  left base: %s" % (n, life["start"], life["end"], life["first"], dict(life["max"]), 100*life["still"]/life["mins"], life["mins"], "yes" if life["far"] else "NO"))
                a = allv[(kind.split()[0] if kind == "stock" else "model", life["first"])]; a[0] += 1; a[1] += life["mins"]; a[2] += life["still"]; a[3] += 0 if life["far"] else 1
        for r in rows:
            s = r["state"]; t = next(x for x in s["teams"] if x["name"] == n); m = s["minute"]
            v = vehicles(t["has"]) if t["men"] > 0 else collections.Counter()
            dt = (m - prevm) if prevm is not None else 0
            if sum(v.values()) == 0:
                close(life); life = None
            else:
                if life is None:
                    first = "shilka" if v["shilka"] and not v["tank"] and not v["apc"] else ("tank" if v["tank"] and not v["shilka"] else ("apc" if v["apc"] and not v["shilka"] and not v["tank"] else "mixed"))
                    life = {"start": m, "first": first, "mins": 0.0, "still": 0.0, "max": collections.Counter(), "far": False, "end": m}
                else:
                    life["mins"] += dt
                    if prevp and t.get("pos") and dist(prevp, t["pos"]) < 25: life["still"] += dt
                for k in v: life["max"][k] = max(life["max"][k], v[k])
                if (t.get("base_dist") or 0) > 400: life["far"] = True
                life["end"] = m
                tot[kind.split()[0] if kind == "stock" else kind][""] += 0
                for k in v: tot["stock" if kind == "stock" else kind][k] += v[k] * dt
            prevm = m; prevp = t.get("pos")
        close(life)
print("\nSUMMARY by what the leader's first vehicle was (lives of 5 minutes or more):")
for k, a in sorted(allv.items()):
    print("   %-6s first vehicle %-6s: %2d lives, %4d team-minutes, stood still %2d%%, never left base %d" % (k[0], k[1], a[0], a[1], 100*a[2]/max(a[1],1), a[3]))
print("\nvehicle-minutes by type:")
for k, c in tot.items():
    s = sum(c.values()) or 1
    print("   %-9s %s" % (k, {x: "%d%%" % (100*c[x]/s) for x in ("tank", "shilka", "apc")}))
