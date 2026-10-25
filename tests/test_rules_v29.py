"""Unit tests for what was new in relay version 29 (crew size, lift fire, rounds fired). Built on the helpers of version 26: base defence. When the enemy side is seen near the base, or
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
check("relay is version 29 or later", relay.VERSION >= 29, relay.VERSION)

# 1. the crew team number is the 6th part of the reply
c = commander("u29a.jsonl")
reply, out = handle(c, msg(1, mortars=0))
check("no crew: the 6th part is -1", len(parts(reply)) >= 6 and parts(reply)[5] == -1, reply[-40:])
W = {"Echo": (BASE[0] + 20, BASE[1])}
reply, out = handle(c, msg(2, mortars=2, where=W))
check("crew named: the 6th part is its team number", c.crew == "Echo" and parts(reply)[5] == relay.TEAM_NAMES.index("Echo"), (c.crew, reply[-40:]))

# 2. a small team near the base is preferred as crew
c = commander("u29b.jsonl"); handle(c, msg(1, mortars=0))
W = {"Echo": (BASE[0] + 900, BASE[1]), "Golf": (BASE[0] + 1200, BASE[1])}
reply, out = handle(c, msg(2, mortars=2, where=W, change={"Golf": {"men": 5}}))
check("a 5-man team 1200 m out is picked over a 9-man team 900 m out", c.crew == "Golf", (c.crew, out[-200:]))
c = commander("u29c.jsonl"); handle(c, msg(1, mortars=0))
W = {"Echo": (BASE[0] + 900, BASE[1]), "Golf": (BASE[0] + 2500, BASE[1])}
reply, out = handle(c, msg(2, mortars=2, where=W, change={"Golf": {"men": 5}}))
check("...but not when the small team is beyond 1500 m: the nearest goes", c.crew == "Echo", c.crew)

# 3. lift fire while one of ours is close to the target
c = commander("u29d.jsonl"); handle(c, msg(1))
reply, out = handle(c, msg(2, seen=[("M1A1", *AT, 0)]))
check("attack: the mortars fire on the attacker", parts(reply)[4] == list(AT) and not c.fire_lifted, parts(reply)[3:])
close = {n: (AT[0] - 150, AT[1]) for n in sorted(c.counter)[:1]}
reply, out = handle(c, msg(3, seen=[("M1A1", *AT, 0)], where=close))
check("a counterattacker 150 m from the target: fire lifted, the counterattack still goes there",
      parts(reply)[4] == [] and c.fire_lifted and parts(reply)[3] == [list(AT)] and "mortars lift fire" in out, (parts(reply)[3:], out[-300:]))
check("...the log says so", json.loads(open(c.log_path).read().splitlines()[-1]).get("fire_lifted") is True)
reply, out = handle(c, msg(4, seen=[("M1A1", *AT, 0)], where={n: (AT[0] - 600, AT[1]) for n in close}))
check("it pulls back to 600 m: the mortars fire again", parts(reply)[4] == list(AT) and not c.fire_lifted and "mortars fire again" in out, (parts(reply)[3:], out[-300:]))

# 4. an attacker at the base itself: no mortar fire
c = commander("u29e.jsonl"); handle(c, msg(1))
NEAR = (BASE[0] + 150, BASE[1])
reply, out = handle(c, msg(2, seen=[("M1A1", *NEAR, 0)]))
check("attacker 150 m from the base: no fire on it", parts(reply)[4] == [] and c.fire_lifted and "the base" in out, (parts(reply)[3:], out[-300:]))

# 5. the threat ends: nothing left lifted
c = commander("u29f.jsonl"); handle(c, msg(1))
handle(c, msg(2, seen=[("M1A1", *NEAR, 0)]))
for m in range(3, 8):
    reply, out = handle(c, msg(m))
check("threat over: no fire point, nothing lifted", c.base_threat is None and c.fire_point is None and not c.fire_lifted)

# 6. rounds fired: the 13th side number of Report.sqs 17
m = msg(1); m[5] = m[5] + [17]
check("Report.sqs 17: the rounds fired are read", state_of(m).get("mortar_shots") == 17, state_of(m).get("mortar_shots"))
check("...and an older report has none", "mortar_shots" not in state_of(msg(1)))

print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
