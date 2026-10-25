"""Unit tests for what was new in relay version 31 (one side on rules, the other on the model). Built on the helpers of version 26: base defence. When the enemy side is seen near the base, or
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
import time
def parts(reply): return json.loads(reply)
check("relay is version 31 or later", relay.VERSION >= 31, relay.VERSION)
relay.RULES_ONLY = False
relay.RULES_SIDES = {"West"}
east = relay.MfctiCommander("East", os.path.join(TMP, "u31e.jsonl"))
west = relay.MfctiCommander("West", os.path.join(TMP, "u31w.jsonl"))
check("--rules-side=West: West is rules only, East is not", west.rules_only() and not east.rules_only())
m = msg(1); m[1] = "West"
started = time.time()
reply, out = handle(west, m)
reply, out = handle(west, (lambda m: (m.__setitem__(1, "West"), m)[1])(msg(2)))
check("a West report is answered by the rules, without asking the model", time.time() - started < 5, round(time.time() - started, 1))
check("...and the log marks it", json.loads(open(west.log_path).read().splitlines()[-1]).get("rules_only") is True)
check("...with a full set of orders", len(parts(reply)[1]) == 9)
relay.RULES_SIDES = set()
check("no option: neither side is rules only", not west.rules_only() and not east.rules_only())
relay.RULES_ONLY = True
check("--rules: both sides are", west.rules_only() and east.rules_only())
print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
