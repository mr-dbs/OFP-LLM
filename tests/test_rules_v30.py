"""Unit tests for what was new in relay version 30 (commander's guard, resistance at the base, crew kept at 2 men). Built on the helpers of version 26: base defence. When the enemy side is seen near the base, or
kills our men from near it, the base is under fire: the nearest fit teams counterattack the attacker's position
(order 1, place 0 of the reply) and the mortars fire on it (the fire mission, the 5th part of the reply).
Started by run_tests.py. Arguments: the folder that holds relay.py, a scratch folder."""
import json, sys, os, io, contextlib
sys.path.insert(0, sys.argv[1]); TMP = sys.argv[2]
import relay
T = [("Lany", 200, 10000, 4300), ("Varta", 100, 8900, 7000), ("Petrovice", 400, 3000, 5400), ("Mala Ves", 100, 8000, 4700)]
BASE = (10019, 4009)
def man(t, w=""): return [t, w, False]
SQUAD = [man("SoldierEB")] * 5 + [man("SoldierELAW", "RPGLauncher")] * 4
RIFLES = [man("SoldierEB")] * 9
def tanks(n): return [["MFCTI116T80", "V", True, True, True, 0.8, True, True] for _ in range(n)]
LEADER = [man("SoldierEAT", "AT4Launcher")]
def team(name, kit, x, y, seat=1, speed=20, men=None, fleeing=False, human=False):
    if men is None: men = len(kit) if kit and kit[0][1] != "V" else 3 * len(kit)
    d = [((x - tx) ** 2 + (y - ty) ** 2) ** .5 for _, _, tx, ty in T]
    near = d.index(min(d))
    return [name, human, 0, 12, True, 100000, men, near, d[near], fleeing, True, kit, x, y, ((x - BASE[0]) ** 2 + (y - BASE[1]) ** 2) ** .5,
            seat, speed, True, 0, 0.0, 0.0, False, True, 0.9, False, True, 0, "", "", ""]
NAMES = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]
HEAVY = [1, 1, 1, 1, 0, 0, 1, 0]
# Default places: tank teams 2 to 3.5 km from base, foot teams 1.5 to 3 km, all moving along.
def home(i, minute): return (BASE[0] - 1500 - 500 * i + 30 * minute, BASE[1] + 300 * (i % 3))
def msg(minute, seen=(), deaths=(), mortars=2, where=None, change=None, layout=14, owners=None, v15=True, off=False):
    """seen: (class, x, y, whose) with whose 0 enemy, 1 resistance. deaths: (team number, killer class, x, y)."""
    where, change, owners = where or {}, change or {}, owners or {}
    towns = [[n, v, owners.get(i, 0), x, y] for i, (n, v, x, y) in enumerate(T)]
    teams = [team("Commander", LEADER, *BASE, seat=0, speed=0)]
    for i, n in enumerate(NAMES):
        extra = dict(change.get(n, {}))
        kit = extra.pop("kit", tanks(3) if i < 4 else SQUAD)
        x, y = where.get(n, home(i, minute))
        extra.setdefault("speed", 0 if n in where else 20)
        teams.append(team(n, kit, x, y, seat=1 if kit and kit[0][1] == "V" else 0, **extra))
    enemy = []
    for cls, x, y, whose in seen:
        d = [((x - tx) ** 2 + (y - ty) ** 2) ** .5 for _, _, tx, ty in T]
        entry = [cls, d.index(min(d)), cls.startswith("Soldier"), False, whose]
        enemy.append(entry + [x, y] if layout >= 14 else entry)
    dead = [([i, cls, False, x, y] + ([ks] if v15 else [])) if layout >= 14 else [i, cls, False] for i, cls, x, y, ks in [(d + (0,))[:5] for d in deaths]]
    info = [900000, HEAVY, True, 0, False, -1, BASE[0], BASE[1]] + ([mortars, mortars] if layout >= 14 else []) + ([off, False] if v15 else [])
    return ["MFCTI", "East", minute * 60, 1, towns, info, teams, enemy, [], dead, [], layout, [0, 0, 0], True, 2]
def state_of(m): return relay.parse_mfcti(json.loads(json.dumps(m)))
def commander(name): return relay.MfctiCommander("East", os.path.join(TMP, name))
ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FAIL:", label, str(extra)[:900])
def handle(c, m):
    with contextlib.redirect_stdout(io.StringIO()) as out: reply = c.handle(state_of(m))
    return reply, out.getvalue()
def entry(reply, name): return json.loads(reply)[1][relay.TEAM_NAMES.index(name)]
AT = (BASE[0] + 1000, BASE[1])
relay.RULES_ONLY = True
def parts(reply): return json.loads(reply)
def guard(m, he=4, manned=3, guards=6):
    m[5] = m[5] + [0, he, manned, guards]; return m
check("relay is version 30 or later", relay.VERSION >= 30, relay.VERSION)

# 1. Report.sqs 18 numbers
s = state_of(guard(msg(1)))
check("Report.sqs 18: HE stations, manned, guard are read", (s.get("he_stations"), s.get("he_manned"), s.get("guards")) == (4, 3, 6), s.get("guards"))
check("...an older report has none of them", "guards" not in state_of(msg(1)))

# 2. with the commander's guard no field team is crew, and a crew already named is let go
c = commander("u30a.jsonl"); handle(c, guard(msg(1, mortars=0)))
W = {"Echo": (BASE[0] + 20, BASE[1])}
reply, out = handle(c, guard(msg(2, mortars=2, where=W)))
check("guard: no field team becomes the crew", c.crew is None and parts(reply)[5] == -1 and entry(reply, "Echo")[1:3] == [3, -1], (c.crew, entry(reply, "Echo")))
c = commander("u30b.jsonl"); handle(c, msg(1, mortars=0))
handle(c, msg(2, mortars=2, where=W))
had = c.crew
reply, out = handle(c, guard(msg(3, mortars=2, where=W)))
check("a crew from an older report is released once the guard is reported", had == "Echo" and c.crew is None and "guard mans the guns" in out, (had, c.crew, out[-200:]))

# 3. resistance killing our men at the base is an attack; further out it is not
c = commander("u30c.jsonl"); handle(c, msg(1))
reply, out = handle(c, msg(2, deaths=[(5, "BMP", BASE[0] + 300, BASE[1], 1)]))
check("resistance killer 300 m from the base: base under fire", c.base_threat is not None and "resistance" in c.base_threat["what"] and "BASE UNDER FIRE" in out, (c.base_threat, out[-300:]))
check("...and the mortars fire on it", parts(reply)[4] == [BASE[0] + 300, BASE[1]], parts(reply)[3:])
c = commander("u30d.jsonl"); handle(c, msg(1))
reply, out = handle(c, msg(2, deaths=[(5, "BMP", BASE[0] + 1000, BASE[1], 1)]))
check("resistance killer 1000 m out: no alarm (the pack 27 fix stays)", c.base_threat is None, c.base_threat)
c = commander("u30e.jsonl"); handle(c, msg(1))
reply, out = handle(c, msg(2, deaths=[(5, "M1A1", BASE[0] + 1000, BASE[1], 0)]))
check("enemy killer 1000 m out: still an alarm", c.base_threat is not None, c.base_threat)
s = state_of(msg(2, deaths=[(5, "BMP", BASE[0] + 300, BASE[1], 1)]))
check("resistance killers are kept apart from the enemy's", not s["killers"] and len(s["resistance_killers"]) == 1, (s["killers"], s["resistance_killers"]))

# 4. an older-report crew is kept down to 2 men
c = commander("u30f.jsonl"); handle(c, msg(1, mortars=0))
handle(c, msg(2, mortars=2, where=W))
reply, out = handle(c, msg(3, mortars=2, where=W, change={"Echo": {"men": 3}}))
check("crew down to 3 men: kept, and still told to defend the base", c.crew == "Echo" and entry(reply, "Echo")[1:3] == [4, -1], (c.crew, entry(reply, "Echo")))
reply, out = handle(c, msg(4, mortars=2, where=W, change={"Echo": {"men": 1}}))
check("crew down to 1 man: replaced", c.crew != "Echo" and "Echo is no longer the mortar crew" in out, (c.crew, out[-200:]))

print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
