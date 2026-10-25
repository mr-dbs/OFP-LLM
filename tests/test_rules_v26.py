"""Unit tests for what was new in relay version 26: base defence. When the enemy side is seen near the base, or
kills our men from near it, the base is under fire: the nearest fit teams counterattack the attacker's position
(order 1, place 0 of the reply) and the mortars fire on it (the fire mission, the 5th part of the reply).
Started by run_tests.py. Arguments: the folder that holds relay.py, a scratch folder."""
import re, json, sys, os, io, contextlib
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
def msg(minute, seen=(), deaths=(), mortars=2, where=None, change=None, layout=14, owners=None):
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
    dead = [[i, cls, False, x, y] if layout >= 14 else [i, cls, False] for i, cls, x, y in deaths]
    info = [900000, HEAVY, True, 0, False, -1, BASE[0], BASE[1]] + ([mortars, mortars] if layout >= 14 else [])
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
def rows(c): return [json.loads(l) for l in open(c.log_path, encoding="utf-8")]
def parts(reply): return json.loads(reply)
def entry(reply, name): return parts(reply)[1][relay.TEAM_NAMES.index(name)]
def base_lines(out): return [l.strip() for l in out.splitlines() if l.startswith("   BASE  ")]
TANK = "M1A1"                                   # the player's tank
AT = (BASE[0] + 1000, BASE[1])                  # where it sits, 1000 m from the base
relay.RULES_ONLY = True
def started(name, minute=1, **kw):
    c = commander(name); handle(c, msg(minute, **kw)); return c

check("relay is version 26 or later", relay.VERSION >= 26, relay.VERSION)
check("the settings: on, 2 km, 4 minutes to clear, 3 teams within 4 km, re-aim beyond 150 m",
      (relay.BASE_DEFENCE, relay.BASE_THREAT_METRES, relay.BASE_THREAT_CLEAR_MINUTES, relay.COUNTER_TEAMS,
       relay.COUNTER_REACH_METRES, relay.FIRE_RETARGET_METRES, relay.REPORT_LAYOUT) == (True, 2000, 4, 3, 4000, 150, 14))

# 1. reading layout 14
s = state_of(msg(5, seen=[(TANK, *AT, 0), ("SoldierGB", 9000, 6900, 1)], deaths=[(4, TANK, *AT), (5, "unknown", -1, -1)], mortars=2))
tank = next(i for i in s["seen"] if i["whose"] == "enemy")
check("a sighting carries its map position", tank["positions"] == [AT] and tank["armoured"], tank)
check("a man lost carries where his killer stood; an unknown killer carries none",
      s["killers"] == [{"team": "Delta", "what": tank["what"], "class": "tank", "armoured": True, "pos": AT}] and sum(s["deaths"]["Echo"].values()) == 1, s["killers"])
check("the mortars are read", s.get("mortars") == 2 and s.get("mortars_with_shells") == 2)
s13 = state_of(msg(5, seen=[(TANK, *AT, 0)], deaths=[(4, TANK, *AT)], layout=13))
check("a layout 13 report is still read, without positions", s13["seen"][0]["positions"] == [] and s13["killers"] == [] and "mortars" not in s13)

# 2. quiet: the reply has its two new parts, empty
c = started("unit26a.jsonl")
reply, out = handle(c, msg(2))
check("no threat: the reply ends with an empty place list and no fire mission", parts(reply)[3:5] == [[], []] and not base_lines(out), reply[-40:])
check("...and the model would read base_under_fire = no", c.base_threat is None)

# 3. a tank 1000 m from the base: counterattack and fire
reply, out = handle(c, msg(3, seen=[(TANK, *AT, 0)]))
check("an enemy tank 1000 m from the base starts the threat", c.base_threat and c.base_threat["metres"] == 1000 and c.base_threat["how"] == "seen", c.base_threat)
check("...the console says BASE UNDER FIRE", any("BASE UNDER FIRE" in l and "1000 m" in l for l in base_lines(out)), base_lines(out))
check("...the three nearest tank teams counterattack", sorted(c.counter) == ["Alpha", "Bravo", "Charlie"], c.counter)
check("...each is sent to place 0", all(entry(reply, n)[1:3] == [1, 200] for n in ("Alpha", "Bravo", "Charlie")) and entry(reply, "Delta")[1:3] == [3, -1], parts(reply)[1])
check("...place 0 and the fire mission are the tank's position", parts(reply)[3] == [list(AT)] and parts(reply)[4] == list(AT), parts(reply)[3:])
row = rows(c)[-1]
check("...the log row carries the threat, the teams, the place and the fire point",
      row["base_threat"]["what"] and row["counter"] == ["Alpha", "Bravo", "Charlie"] and row["fire"] == list(AT) and any("BASE UNDER FIRE" in n for n in row["defence"]), {k: row.get(k) for k in ("counter", "fire")})
check("...and the change goes to the commander (it was a plan report, not 'no change')", row.get("result") != "no change" and any("BASE UNDER FIRE" in ch for ch in row.get("changes", [])), row.get("changes"))

# 4. the attacker shifts a little, then a lot
reply, out = handle(c, msg(4, seen=[(TANK, AT[0] + 100, AT[1], 0)]))
check("it moves 100 m: same place, same aim, nothing sent again", parts(reply)[3] == [list(AT)] and parts(reply)[4] == list(AT)
      and all(entry(reply, n)[3] == 0 for n in ("Alpha", "Bravo", "Charlie")), reply[-60:])
NEW = (AT[0] + 400, AT[1] + 200)
reply, out = handle(c, msg(5, seen=[(TANK, *NEW, 0)]))
check("it moves 450 m: the counterattack follows (order sent again) and the mortars re-aim", parts(reply)[3] == [list(NEW)] and parts(reply)[4] == list(NEW)
      and all(entry(reply, n)[1:] == [1, 200, 1] for n in ("Alpha", "Bravo", "Charlie")), parts(reply)[1:])

# 5. no longer seen but still killing our men from there: the threat goes on
reply, out = handle(c, msg(6, deaths=[(7, TANK, *NEW)]))
check("unseen but killing from 1 km: the threat goes on, now known by the kills", c.base_threat and c.base_threat["how"] == "killing our men" and c.base_threat["last"] == 6.0, c.base_threat)
check("...three minutes after it began the model is reminded", any("STILL UNDER FIRE after 3 minutes" in l for l in base_lines(out)), base_lines(out))
reply, out = handle(c, msg(7))
check("one quiet report: still on, and no reminder without new evidence", c.base_threat is not None and sorted(c.counter) == ["Alpha", "Bravo", "Charlie"] and not base_lines(out), base_lines(out))
reply, out = handle(c, msg(9))
check("three quiet minutes: still on", c.base_threat is not None)
reply, out = handle(c, msg(10))
check("four quiet minutes: over; teams back to their orders, no place, no fire", c.base_threat is None and not c.counter
      and all(entry(reply, n)[1:3] == [3, -1] for n in NAMES if n != c.crew) and parts(reply)[3:5] == [[], []] and any("no longer under fire" in l for l in base_lines(out)), reply)

# 6. what does not start a threat
c = started("unit26b.jsonl")
reply, out = handle(c, msg(2, seen=[("SoldierGB", *AT, 1), ("SoldierGB", AT[0], AT[1] + 10, 1)]))
check("resistance at the same spot: no threat", c.base_threat is None and not c.counter)
reply, out = handle(c, msg(3, seen=[("AH64", *AT, 0)]))
check("an enemy helicopter alone: no counterattack by ground teams", c.base_threat is None and not c.counter)
reply, out = handle(c, msg(4, seen=[(TANK, BASE[0] + 2500, BASE[1], 0)], deaths=[(4, TANK, BASE[0] + 2600, BASE[1])]))
check("an enemy tank 2.5 km out, even killing from there: no threat", c.base_threat is None)
reply, out = handle(c, msg(5, seen=[("SoldierWB", BASE[0] + 1500, BASE[1], 0)]))
check("an enemy rifleman 1.5 km out: a threat (not armoured)", c.base_threat and not c.base_threat["armoured"])
check("...against infantry any fit team may go, nearest with vehicles first", sorted(c.counter) == ["Alpha", "Bravo", "Charlie"], c.counter)

# 7. who is sent
W = {"Alpha": (AT[0] + 4500, AT[1]), "Echo": (AT[0] - 300, AT[1])}
c = started("unit26c.jsonl", where=W, change={"Foxtrot": {"kit": RIFLES}})
reply, out = handle(c, msg(2, seen=[(TANK, *AT, 0)], where=W, change={"Foxtrot": {"kit": RIFLES}}))
check("a tank team 4.5 km from the attacker is not sent", "Alpha" not in c.counter, c.counter)
check("tank teams come before a nearer foot team", sorted(c.counter) == ["Bravo", "Charlie", "Delta"], c.counter)
c = started("unit26d.jsonl")
c.standing["Bravo"]["order"] = "RETURN_TO_BASE"
c.crew = None                                         # (version 28: no mortar crew in this check)
NEAR = {"Echo": BASE, "Foxtrot": BASE}
s = state_of(msg(2, seen=[(TANK, *AT, 0)], where=NEAR, mortars=0, change={"Alpha": {"human": True}, "Charlie": {"kit": tanks(1) + [["MFCTI116T80", "V", False, False, True, 0.2, True, True]] * 2},
                                                              "Foxtrot": {"kit": RIFLES}}))
c.update_counter(s, c.commanded(s))
check("not a team led by a player, not a team going home for repair, not an unfit one, not riflemen against a tank; "
      "a foot team with launchers at the base does go", set(c.counter) == {"Delta", "Echo"}, c.counter)
c = started("unit26e.jsonl")
handle(c, msg(2, seen=[(TANK, *AT, 0)]))
reply, out = handle(c, msg(3, seen=[(TANK, *AT, 0)], change={"Alpha": {"kit": [], "men": 0}}))
check("a counterattacking team wiped out is replaced by the next nearest", "Alpha" not in c.counter and len(c.counter) == 3 and "Delta" in c.counter
      and any("Alpha leaves the counterattack" in l for l in base_lines(out)), (c.counter, base_lines(out)))

reply, out = handle(c, msg(4, seen=[(TANK, *AT, 0)], change={"Alpha": {"kit": [], "men": 0}, "Bravo": {"fleeing": True}}))
check("a counterattacking team that flees leaves it too", "Bravo" not in c.counter and any("Bravo leaves the counterattack: no longer fit" in l for l in base_lines(out)), (c.counter, base_lines(out)))

# 8. no mortars: no fire mission, the counterattack still goes
c = started("unit26f.jsonl", mortars=0)
reply, out = handle(c, msg(2, seen=[(TANK, *AT, 0)], mortars=0))
check("no mortars: no fire mission, but teams are sent", parts(reply)[4] == [] and parts(reply)[3] == [list(AT)] and len(c.counter) == 3, parts(reply)[3:])

# 9. holds and kicks
VARTA = 1
WH = {"Alpha": (T[VARTA][2] + 10, T[VARTA][3] + 10)}
c = started("unit26g.jsonl", where=WH)
handle(c, msg(2, owners={VARTA: 1}, where=WH))
check("(set-up) Alpha holds Varta", c.holds.get("Alpha", {}).get("town") == "Varta", c.holds)
AT2 = (T[VARTA][2] + 900, T[VARTA][3])
BASE_NEAR_VARTA = {"Alpha": WH["Alpha"]}
c.counter = {}
m = msg(3, owners={VARTA: 1}, where=WH, seen=[(TANK, BASE[0] + 900, BASE[1], 0)])
reply, out = handle(c, m)
holder_sent = "Alpha" in c.counter
check("a team holding a town that is sent against the attacker stops holding", (not holder_sent) or ("Alpha" not in c.holds), (c.counter, c.holds))
c = started("unit26h.jsonl", where={"Bravo": (BASE[0] + 1500, BASE[1])})
kicked = []
for m_ in (2, 3, 4, 5, 6, 7, 8):
    reply, out = handle(c, msg(m_, seen=[(TANK, *AT, 0)], where={"Bravo": (BASE[0] + 1500, BASE[1])}))
    kicked.append(entry(reply, "Bravo")[3] in (2, 3) or "KICK  Bravo: kick" in out)
check("a counterattacking team that stands fighting is not kicked", "Bravo" in c.counter and not any(kicked), (c.counter, kicked))

# 10. older report scripts, switched off, and the test threat
c = started("unit26i.jsonl", layout=13)
reply, out = handle(c, msg(2, seen=[(TANK, *AT, 0)], layout=13))
check("layout 13: nothing of this is used and the reply keeps its old three parts", len(parts(reply)) == 3 and not c.counter and c.base_threat is None, reply[-40:])
relay.BASE_DEFENCE = False
c = started("unit26j.jsonl")
reply, out = handle(c, msg(2, seen=[(TANK, *AT, 0)]))
check("--no-defence: no threat, no teams, empty places and fire", c.base_threat is None and parts(reply)[3:5] == [[], []])
relay.BASE_DEFENCE = True
relay.TEST_THREAT_MINUTE = 5
c = started("unit26k.jsonl")
reply, out = handle(c, msg(4))
check("test threat: nothing before its minute", c.base_threat is None)
reply, out = handle(c, msg(5))
lany = (T[0][2], T[0][3])
d = ((lany[0] - BASE[0]) ** 2 + (lany[1] - BASE[1]) ** 2) ** .5
check("test threat at minute 5: a made-up tank towards the nearest town, and the whole chain runs", c.base_threat and c.base_threat["how"] == "test"
      and parts(reply)[4] and len(c.counter) == 3 and abs(relay.distance(tuple(parts(reply)[4]), BASE) - min(800, d)) < 2, (c.base_threat, parts(reply)[3:]))
for m_ in range(6, 13):
    reply, out = handle(c, msg(m_))
check("...it lasts 8 minutes and clears 4 minutes later", c.base_threat is not None)
reply, out = handle(c, msg(17))
check("...and is over after that", c.base_threat is None and not c.counter)
relay.TEST_THREAT_MINUTE = None

# 11. the model is told, and cannot undo it
relay.RULES_ONLY = False
prompts = []
def model(messages, think):
    prompts.append(messages)
    return json.dumps({"situation": "s", "intent": "model", "teams": {n: {"role": "ARMOUR" if n in NAMES[:4] else "INFANTRY",
                                                                         "order": "TAKE_TOWNS", "target": None, "why": "t"} for n in NAMES}}), False
relay.ask_model = model
c = commander("unit26l.jsonl")
handle(c, msg(1))
handle(c, msg(2, owners={3: 1}))
before = json.loads(prompts[-1][1]["content"].split("CURRENT SITUATION:")[1].split("Give your orders now.")[0])
reply, out = handle(c, msg(3, seen=[(TANK, *AT, 0)]))
after = json.loads(prompts[-1][1]["content"].split("CURRENT SITUATION:")[1].split("Give your orders now.")[0])
check("the model reads base_under_fire = no while quiet", before.get("base_under_fire") == "no", before.get("base_under_fire"))
check("...and the attacker, distance, teams and mortars when it starts", isinstance(after.get("base_under_fire"), dict) and after["base_under_fire"]["metres_from_base"] == 1000
      and after["base_under_fire"]["counterattacking"] == ["Alpha", "Bravo", "Charlie"] and after["base_under_fire"]["mortars_firing"], after.get("base_under_fire"))
check("...the change is in WHAT CHANGED and the rule in its instructions", "BASE UNDER FIRE" in prompts[-1][1]["content"].split("CURRENT SITUATION:")[0]
      and "base_under_fire" in prompts[-1][0]["content"], prompts[-1][1]["content"][:400])
check("...its TAKE_TOWNS for the counterattacking teams does not undo the counterattack", all(entry(reply, n)[1:3] == [1, 200] for n in ("Alpha", "Bravo", "Charlie")), parts(reply)[1])
relay.RULES_ONLY = True

# 12. the whole path: report text in, reply text out
relay.LOG_DIR = TMP
r = relay.Relay(); r.log_path = os.path.join(TMP, "unit26_raw.jsonl"); open(r.log_path, "w").close()
with contextlib.redirect_stdout(io.StringIO()):
    r.handle(json.dumps(msg(1)))
    raw_reply = r.handle(json.dumps(msg(2, seen=[(TANK, *AT, 0)], deaths=[(4, TANK, *AT)])))
check("report text in, reply text out: places and fire as plain number lists the mission can read",
      raw_reply.startswith("[1,[[") and re.search(r",\[\[%d,%d\]\],\[%d,%d\](,.*)?\]$" % (AT + AT), raw_reply) and "." not in raw_reply.split('"')[-1], raw_reply[-60:])

# 13. options at start-up
source = open(os.path.join(sys.argv[1], "relay.py"), encoding="utf-8").read()
check("--no-defence and --test-threat=N are read at start-up and the banner says so",
      '"--no-defence" in sys.argv[1:]' in source and 'startswith("--test-threat=")' in source and "base defence (counterattack and mortar fire" in source)

print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
