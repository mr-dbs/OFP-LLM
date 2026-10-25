"""Unit tests for what was new in relay version 32 (the air response). Built on the helpers of version 26: base defence. When the enemy side is seen near the base, or
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
def guard(m): m[5] = m[5] + [0, 4, 4, 6]; return m
def airfactory(m): m[5][1] = [1, 1, 1, 1, 1, 0, 1, 0]; return m
HELO = ("MFCTI116AH64", BASE[0] - 1500, BASE[1] + 300, 0)
check("relay is version 32 or later", relay.VERSION >= 32, relay.VERSION)
c = commander("u32a.jsonl"); handle(c, guard(msg(1)))
reply, out = handle(c, guard(msg(2)))
check("no aircraft: nothing bought, 7th part empty", len(parts(reply)) == 7 and parts(reply)[6] == [], reply[-30:])
reply, out = handle(c, guard(msg(3, seen=[HELO])))
buy = parts(reply)[6]
check("attack helicopter seen: 3 teams and the base get anti-air soldiers", len(buy) == 4 and [0, 2] in buy and all(n == 2 for _, n in buy), buy)
names = [relay.TEAM_NAMES[t] for t, _ in buy if t]
dists = {n: relay.distance(next(t for t in c.last_teams if t["name"] == n)["pos"], (HELO[1], HELO[2])) for n in relay.TEAM_NAMES[1:]} if hasattr(c, "last_teams") else None
check("...and the model is told", "AIR THREAT" in out, out[-300:])
reply, out = handle(c, guard(msg(4, seen=[HELO])))
check("seen again 1 minute later: no second wave", parts(reply)[6] == [], parts(reply)[6])
reply, out = handle(c, guard(msg(9, seen=[HELO])))
check("seen again 6 minutes later: a second wave", len(parts(reply)[6]) == 4, parts(reply)[6])
c = commander("u32b.jsonl"); handle(c, msg(1))
reply, out = handle(c, msg(2, seen=[HELO]))
check("older report (no guard): field teams only", len(parts(reply)[6]) == 3 and all(t != 0 for t, _ in parts(reply)[6]), parts(reply)[6])
c = commander("u32c.jsonl"); handle(c, airfactory(guard(msg(1))))
reply, out = handle(c, airfactory(guard(msg(2, seen=[HELO]))))
hunter = c.air_hunter
check("with an air factory one team becomes the attack helicopter team", hunter is not None and entry(reply, hunter)[0] == relay.MFCTI_ROLE_NUMBER["AIR"], (hunter, entry(reply, hunter) if hunter else None))
reply, out = handle(c, airfactory(guard(msg(3))))
check("...and stays so after the aircraft is gone", c.air_hunter == hunter and entry(reply, hunter)[0] == relay.MFCTI_ROLE_NUMBER["AIR"])
c = commander("u32f.jsonl"); handle(c, guard(msg(1)))
reply, out = handle(c, guard(msg(2, seen=[("MFCTI116UH60", BASE[0] - 1500, BASE[1] + 300, 0)])))
check("an enemy UH-60 (a transport helicopter, but armed) starts the air response too (version 33)", len(parts(reply)[6]) == 4, parts(reply)[6])
c = commander("u32d.jsonl"); handle(c, guard(msg(1)))
reply, out = handle(c, guard(msg(2, seen=[("MFCTI116T80", BASE[0] - 1500, BASE[1], 0)])))
check("a tank seen: no anti-air bought", parts(reply)[6] == [], parts(reply)[6])
c = commander("u32e.jsonl"); handle(c, guard(msg(1)))
reply, out = handle(c, guard(msg(2, seen=[("MFCTI116AH64", BASE[0] - 1500, BASE[1], 1)])))
check("a resistance helicopter: no anti-air bought", parts(reply)[6] == [], parts(reply)[6])
print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
