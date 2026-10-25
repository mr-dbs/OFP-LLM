"""Unit tests for what was new in relay version 27 (killer side, mortars switched off). Built on the helpers of version 26: base defence. When the enemy side is seen near the base, or
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
AT = (BASE[0] + 1000, BASE[1])
relay.RULES_ONLY = True
check("relay is version 27 or later", relay.VERSION >= 27, relay.VERSION)
s = state_of(msg(5, deaths=[(4, "M1A1", *AT, 0), (5, "SoldierGB", *AT, 1)]))
check("Report 15: an enemy killer counts, a resistance killer does not", [k["team"] for k in s["killers"]] == ["Delta"] and sum(s["deaths"]["Echo"].values()) == 1, s["killers"])
s = state_of(msg(5, deaths=[(5, "SoldierGB", *AT)], v15=False))
check("Report 14: every killer counts, as before", [k["team"] for k in s["killers"]] == ["Echo"], s["killers"])
c = relay.MfctiCommander("East", os.path.join(TMP, "u27a.jsonl")); handle(c, msg(1))
reply, out = handle(c, msg(2, deaths=[(5, "SoldierGB", *AT, 1), (6, "SoldierGB", *AT, 1)]))
check("resistance killing our men 1 km from the base starts no counterattack", c.base_threat is None and not c.counter)
reply, out = handle(c, msg(3, deaths=[(5, "M1A1", *AT, 0)]))
check("the enemy doing the same does", c.base_threat is not None and len(c.counter) == 3)
s = state_of(msg(5, off=True))
check("the mortars-off flag is read", s.get("mortars_off") is True and state_of(msg(5)).get("mortars_off") is False)
c = relay.MfctiCommander("East", os.path.join(TMP, "u27b.jsonl"))
reply, out = handle(c, msg(1, off=True)); reply2, out2 = handle(c, msg(2, off=True))
check("...and the relay says so once", out.count("mortars are switched off") == 1 and "mortars are switched off" not in out2, out[-300:])
print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
