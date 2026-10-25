"""Unit tests for what was new in relay version 25: hold what you take. The team nearest a town its side has just
taken goes to the flag (order 1 with the town's number) and stays two minutes once it is there, longer while it is
still killing or losing men there, five minutes at most. Then it goes on taking towns (order 3).
Started by run_tests.py. Arguments: the folder that holds relay.py, a scratch folder."""
import json, sys, os, io, contextlib
sys.path.insert(0, sys.argv[1]); TMP = sys.argv[2]
import relay
T = [("Lany", 200, 10000, 4300), ("Varta", 100, 8900, 7000), ("Petrovice", 400, 3000, 5400), ("Mala Ves", 100, 8000, 4700)]
VARTA, PETROVICE, MALA_VES = 1, 2, 3
BASE = (10019, 4009)
def man(t, w=""): return [t, w, False]
SQUAD = [man("SoldierEB")] * 5 + [man("SoldierELAW", "RPGLauncher")] * 4
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
NO_BARRACKS = [1, 0, 0, 0, 0, 0, 0, 0]
def at(town, east=0, north=0): return (T[town][2] + east, T[town][3] + north)
def msg(minute, owners=None, where=None, kills=(), deaths=(), change=None, built=HEAVY):
    """One report. owners: town number -> 0 nobody, 1 us, 2 enemy. where: team -> (x, y), every other team drives
    along far from every town. change: team -> values for team(): men, kit, fleeing, human, speed."""
    owners, where, change = owners or {}, where or {}, change or {}
    towns = [[n, v, owners.get(i, 0), x, y] for i, (n, v, x, y) in enumerate(T)]
    teams = [team("Commander", LEADER, *BASE, seat=0, speed=0)]
    for i, n in enumerate(NAMES):
        extra = dict(change.get(n, {}))
        kit = extra.pop("kit", tanks(3) if i < 4 else SQUAD)
        x, y = where.get(n, (5000 + 60 * minute, 1000 + 250 * i))
        extra.setdefault("speed", 0 if n in where else 20)
        teams.append(team(n, kit, x, y, seat=1 if kit and kit[0][1] == "V" else 0, **extra))
    return ["MFCTI", "East", minute * 60, 1, towns, [900000, built, True, 0, False, -1, BASE[0], BASE[1]], teams, [],
            [list(k) for k in kills], [list(d) for d in deaths], [], 13, [0, 0, 0], True, 2]
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
def entry(reply, name): return json.loads(reply)[1][relay.TEAM_NAMES.index(name)]
def codes(reply): return {n: entry(reply, n)[1:3] for n in NAMES}
def hold_lines(out): return [l.strip() for l in out.splitlines() if l.startswith("   HOLD  ")]
def started(c, name, minute=1, where=None):
    """A rules-only commander whose teams are out taking towns, after one quiet report."""
    c = commander(name)
    reply, out = handle(c, msg(minute, where=where))
    return c
KILL_AT_VARTA = ("SoldierGB", VARTA, 1)        # a resistance rifleman killed near Varta by Alpha
relay.RULES_ONLY = True

check("relay is version 25 or later", relay.VERSION >= 25, relay.VERSION)
check("the hold settings: on, reach 600 m, at the flag within 60 m, 2 to 5 minutes, quiet after 1.5",
      (relay.HOLD_TAKEN_TOWNS, relay.HOLD_REACH_METRES, relay.HOLD_AT_FLAG_METRES, relay.HOLD_MIN_MINUTES, relay.HOLD_MAX_MINUTES, relay.HOLD_QUIET_MINUTES) == (True, 600, 60, 2, 5, 1.5))

# 1. the team at the flag of a town just taken holds it for two minutes, then goes on
W = {"Alpha": at(VARTA, 20, 10), "Bravo": at(VARTA, 300, 250)}
c = started(None, "unit25a.jsonl", where=W)
reply, out = handle(c, msg(1.5, where=W))
check("before anything is taken every team is taking towns and nothing is said about holds", all(v == [3, -1] for v in codes(reply).values()) and not hold_lines(out) and "holding" not in rows(c)[-1], codes(reply))
reply, out = handle(c, msg(2, {VARTA: 1}, W))
check("a town is taken: the nearest team on TAKE_TOWNS is sent to its flag (order 1, the town's number)", entry(reply, "Alpha")[1:3] == [1, VARTA], reply)
check("...its role and its standing order are unchanged", entry(reply, "Alpha")[0] == relay.MFCTI_ROLE_NUMBER[c.standing["Alpha"]["role"]] and c.standing["Alpha"]["order"] == "TAKE_TOWNS", c.standing["Alpha"])
check("...and only that team: the second nearest and the rest keep taking towns", all(v == [3, -1] for n, v in codes(reply).items() if n != "Alpha"), codes(reply))
check("...the console says who holds what and for how long", any("Alpha holds Varta" in l and "at least 2 minutes" in l and "at most 5" in l for l in hold_lines(out)), hold_lines(out))
row = rows(c)[-1]
check("...the log row names the holder and carries the note", row.get("holding") == {"Alpha": "Varta"} and any("Alpha holds Varta" in n for n in row.get("holds", [])) and row["reply"] == reply, {k: row.get(k) for k in ("holding", "holds")})
reply, out = handle(c, msg(3, {VARTA: 1}, W))
check("one minute at the flag: it still holds", entry(reply, "Alpha")[1:3] == [1, VARTA] and rows(c)[-1].get("holding") == {"Alpha": "Varta"} and not hold_lines(out), (reply, hold_lines(out)))
reply, out = handle(c, msg(4, {VARTA: 1}, W))
check("two quiet minutes at the flag: it is released and takes towns again", entry(reply, "Alpha")[1:3] == [3, -1] and "Alpha" not in c.holds, reply)
check("...the console and the log say why", any("Alpha stops holding Varta after 2.0 minutes" in l and "quiet" in l for l in hold_lines(out)) and "holding" not in rows(c)[-1]
      and any("stops holding" in n for n in rows(c)[-1]["holds"]), hold_lines(out))
reply, out = handle(c, msg(5, {VARTA: 1}, W))
check("a town that stays ours starts no second hold", not c.holds and not hold_lines(out) and entry(reply, "Alpha")[1:3] == [3, -1])

# 2. a team that had already driven off is called back: the two minutes start when it reaches the flag
AWAY = {"Bravo": at(VARTA, 300, 250)}
c = started(None, "unit25b.jsonl", where=AWAY)
reply, out = handle(c, msg(2, {VARTA: 1}, AWAY))
check("the nearest team is 391 m away: it is called back to the flag", entry(reply, "Bravo")[1:3] == [1, VARTA] and c.holds["Bravo"]["at_flag"] is None and "391 m from the flag" in out, hold_lines(out))
reply, out = handle(c, msg(3, {VARTA: 1}, {"Bravo": at(VARTA, 30, 30)}))
check("it arrives at minute 3", c.holds.get("Bravo", {}).get("at_flag") == 3.0 and entry(reply, "Bravo")[1:3] == [1, VARTA])
reply, out = handle(c, msg(4, {VARTA: 1}, {"Bravo": at(VARTA, 30, 30)}))
check("at minute 4 it has been there one minute and holds on", entry(reply, "Bravo")[1:3] == [1, VARTA])
reply, out = handle(c, msg(5, {VARTA: 1}, {"Bravo": at(VARTA, 30, 30)}))
check("at minute 5 it has been there two and is released", entry(reply, "Bravo")[1:3] == [3, -1] and "Bravo stops holding Varta after 3.0 minutes" in out, hold_lines(out))

# 3. a team that never reaches the flag is released after five minutes
c = started(None, "unit25c.jsonl", where=AWAY)
handle(c, msg(2, {VARTA: 1}, AWAY))
for m in (3, 4, 5, 6):
    reply, out = handle(c, msg(m, {VARTA: 1}, AWAY))
check("four minutes on, still 391 m away: still told to go to the flag", entry(reply, "Bravo")[1:3] == [1, VARTA])
reply, out = handle(c, msg(7, {VARTA: 1}, AWAY))
check("five minutes on: released whatever happened", entry(reply, "Bravo")[1:3] == [3, -1] and "5 minutes are up" in out, hold_lines(out))

# 4. fighting keeps the holder: a kill at the town or a man of the team lost restarts the quiet time
c = started(None, "unit25d.jsonl", where=W)
handle(c, msg(2, {VARTA: 1}, W))
handle(c, msg(3, {VARTA: 1}, W))
reply, out = handle(c, msg(4, {VARTA: 1}, W, kills=[KILL_AT_VARTA]))
check("two minutes at the flag but a kill at the town in this report: it holds on", entry(reply, "Alpha")[1:3] == [1, VARTA] and c.holds["Alpha"]["fight"] == 4.0, reply)
reply, out = handle(c, msg(5, {VARTA: 1}, W))
check("one quiet minute after the kill is not enough", entry(reply, "Alpha")[1:3] == [1, VARTA])
reply, out = handle(c, msg(5.5, {VARTA: 1}, W))
check("a minute and a half is: released", entry(reply, "Alpha")[1:3] == [3, -1] and "quiet for 1.5 minutes" in out, hold_lines(out))
c = started(None, "unit25e.jsonl", where=W)
handle(c, msg(2, {VARTA: 1}, W))
handle(c, msg(3, {VARTA: 1}, W))
reply, out = handle(c, msg(4, {VARTA: 1}, W, deaths=[(1, "SoldierGB", False)]))
check("a man of the holding team killed counts as fighting too", entry(reply, "Alpha")[1:3] == [1, VARTA])
reply, out = handle(c, msg(4.5, {VARTA: 1}, W, kills=[("SoldierGB", MALA_VES, 2)]))
check("a kill at another town does not", c.holds["Alpha"]["fight"] == 4.0)
c = started(None, "unit25f.jsonl", where=W)
handle(c, msg(2, {VARTA: 1}, W))
for m in (3, 4, 5, 6):
    reply, out = handle(c, msg(m, {VARTA: 1}, W, kills=[KILL_AT_VARTA]))
check("a fight that goes on keeps it four minutes", entry(reply, "Alpha")[1:3] == [1, VARTA])
reply, out = handle(c, msg(7, {VARTA: 1}, W, kills=[KILL_AT_VARTA]))
check("...and at five minutes it is released even while it fights", entry(reply, "Alpha")[1:3] == [3, -1] and "5 minutes are up" in out, hold_lines(out))

# 5. a holding team is not kicked for standing still, and the clock for kicks starts new when it is released
c = started(None, "unit25g.jsonl", where=W)
kicked = []
handle(c, msg(2, {VARTA: 1}, W))
for m in (3, 4, 5, 6):
    reply, out = handle(c, msg(m, {VARTA: 1}, W, kills=[KILL_AT_VARTA]))
    kicked.append((entry(reply, "Alpha")[3], "KICK  Alpha" in out, "Alpha" in c.freeze))
check("four minutes standing at the flag on a hold: no kick, and it is not watched as frozen", kicked == [(0, False, False)] * 4, kicked)
reply, out = handle(c, msg(7, {VARTA: 1}, W))
check("the report that releases it does not kick it either", entry(reply, "Alpha")[1:] == [3, -1, 0] and c.freeze.get("Alpha", {}).get("since") == 7.0, (reply, c.freeze.get("Alpha")))
relay.HOLD_TAKEN_TOWNS = False
c = started(None, "unit25h.jsonl", where=W)
said = ""
for m in (2, 3, 4, 5, 6, 7):
    reply, out = handle(c, msg(m, {VARTA: 1}, W)); said += out
check("with the hold switched off the same team standing there is kicked as before", "KICK  Alpha: kick 1" in said, said[-400:])
check("...it is never sent to the flag and nothing is logged about holds", not c.holds and all("holding" not in r and not r.get("holds") for r in rows(c)) and "HOLD  " not in said)
relay.HOLD_TAKEN_TOWNS = True

# 6. the hold ends when the team's order changes, or the team is no longer fit to hold
def held(name):
    c = started(None, name, where=W)
    handle(c, msg(2, {VARTA: 1}, W))
    return c
c = held("unit25i.jsonl")
c.standing["Alpha"]["order"] = "RETURN_TO_BASE"
reply = c.reply(state_of(msg(2, {VARTA: 1}, W)))
check("a holder whose order is no longer TAKE_TOWNS follows that order at once", entry(reply, "Alpha")[1:3] == [1, -2], reply)
c.standing["Alpha"]["since"] = 2.0
reply, out = handle(c, msg(3, {VARTA: 1}, W, change={"Alpha": {"kit": tanks(1) + [["MFCTI116T80", "V", False, False, True, 0.2, True, True]] * 2}}))
check("...and the hold is ended on the next report", "Alpha" not in c.holds and "its order is now" in out, hold_lines(out))
c = held("unit25j.jsonl")
reply, out = handle(c, msg(3, {VARTA: 1}, W, change={"Alpha": {"kit": [man("SoldierEB")] * 2, "men": 2}}))
check("a holder down to two men on foot: the hold ends", "Alpha" not in c.holds and "no longer fit to hold" in out, hold_lines(out))
c = held("unit25k.jsonl")
reply, out = handle(c, msg(3, {VARTA: 1}, W, change={"Alpha": {"fleeing": True}}))
check("a holder that flees: the hold ends", "Alpha" not in c.holds and "no longer fit to hold" in out, hold_lines(out))
c = held("unit25l.jsonl")
reply, out = handle(c, msg(3, {VARTA: 1}, W, change={"Alpha": {"kit": [], "men": 0}}))
check("a holder wiped out: the hold ends, and the reply is still a full set of orders", "Alpha" not in c.holds and "the team is gone" in out and len(json.loads(reply)[1]) == 9, hold_lines(out))

# 7. who is picked
FAR = {"Alpha": at(VARTA, 500, 400)}                                   # 640 m
c = started(None, "unit25m.jsonl", where=FAR)
reply, out = handle(c, msg(2, {VARTA: 1}, FAR))
check("no team within 600 m of the town: nobody is called back", not c.holds and all(v == [3, -1] for v in codes(reply).values()) and not hold_lines(out), codes(reply))
TWO = {"Alpha": at(VARTA, 20, 10), "Bravo": at(VARTA, 100, 0), "Echo": at(MALA_VES, 10, 10)}
c = started(None, "unit25n.jsonl", where=TWO)
reply, out = handle(c, msg(2, {VARTA: 1, MALA_VES: 1}, TWO))
check("two towns taken in one report: each gets its own nearest team, a tank team and a foot team", c.holds.keys() == {"Alpha", "Echo"} and entry(reply, "Alpha")[1:3] == [1, VARTA]
      and entry(reply, "Echo")[1:3] == [1, MALA_VES] and entry(reply, "Bravo")[1:3] == [3, -1], codes(reply))
BOTH = {"Alpha": at(VARTA, 20, 10)}
c = started(None, "unit25o.jsonl", where=BOTH)
handle(c, msg(2, {VARTA: 1}, BOTH))
T_SAVED = T[MALA_VES]; T[MALA_VES] = ("Mala Ves", 100, 8900 + 200, 7000)   # a second flag 200 m from the first
c2 = started(None, "unit25p.jsonl", where=BOTH)
handle(c2, msg(2, {VARTA: 1}, BOTH))
reply, out = handle(c2, msg(3, {VARTA: 1, MALA_VES: 1}, BOTH))
check("a team that already holds one town is not given a second", c2.holds.keys() == {"Alpha"} and c2.holds["Alpha"]["town"] == "Varta" and entry(reply, "Alpha")[1:3] == [1, VARTA], c2.holds)
T[MALA_VES] = T_SAVED
c = started(None, "unit25q.jsonl", where=TWO)
c.standing["Alpha"]["order"] = "DEFEND_BASE"
s = state_of(msg(1.5, {VARTA: 1}, TWO)); c.update_holds(s, c.commanded(s))
check("a team on another order is passed over for the next nearest on TAKE_TOWNS", "Alpha" not in c.holds and c.holds.get("Bravo", {}).get("town") == "Varta", c.holds)
c = started(None, "unit25r.jsonl", where=TWO)
reply, out = handle(c, msg(2, {VARTA: 1}, TWO, change={"Alpha": {"human": True}}))
check("a team led by a player is never picked", "Alpha" not in c.holds and "Bravo" in c.holds and entry(reply, "Alpha") == [-1, -1, -1, 0], reply)
c = started(None, "unit25s.jsonl", where=TWO)
reply, out = handle(c, msg(2, {VARTA: 1}, TWO, change={"Alpha": {"kit": [man("SoldierEB")] * 2, "men": 2}}))
check("a team of two men on foot is not picked", "Alpha" not in c.holds and "Bravo" in c.holds, c.holds)
c = started(None, "unit25t.jsonl", where=TWO)
reply, out = handle(c, msg(2, {VARTA: 1}, TWO, change={"Alpha": {"fleeing": True}}))
check("a fleeing team is not picked", "Alpha" not in c.holds and "Bravo" in c.holds, c.holds)
LANY = 0                                                               # its flag is 291 m from the base
HOME = {"Echo": (BASE[0] + 10, BASE[1] + 10), "Bravo": at(LANY, -350, 200)}
c = started(None, "unit25ad.jsonl", where=HOME)
reply, out = handle(c, msg(2, {LANY: 1}, HOME, change={"Echo": {"kit": [man("SoldierEB")] * 5}}))
check("a team still filling up at base (5 of 9 men) is passed over although it is nearer", c.holds.keys() == {"Bravo"} and entry(reply, "Echo")[1:3] == [3, -1], (c.holds, reply))
c = started(None, "unit25ae.jsonl", where=HOME)
reply, out = handle(c, msg(2, {LANY: 1}, HOME))
check("a full team at base is picked like any other", c.holds.keys() == {"Echo"}, c.holds)
c = commander("unit25u.jsonl")
handle(c, msg(1, {VARTA: 2}, W))
reply, out = handle(c, msg(2, {VARTA: 1}, W))
check("a town taken from the enemy side is held the same way", c.holds.get("Alpha", {}).get("town") == "Varta" and entry(reply, "Alpha")[1:3] == [1, VARTA], reply)
c = commander("unit25v.jsonl")
reply, out = handle(c, msg(1, {VARTA: 1}, W))
check("towns that are ours on the first report of a game start no hold", not c.holds and not hold_lines(out))
c = commander("unit25w.jsonl")
handle(c, msg(1, {}, W, built=NO_BARRACKS))
reply, out = handle(c, msg(2, {VARTA: 1}, W, built=NO_BARRACKS))
check("without a barracks no hold starts: the teams wait at base as before", not c.holds and entry(reply, "Alpha")[1:3] == [1, -2], reply)

# 8. the town is lost while it is held: the team stays at the flag until its five minutes are up
c = held("unit25x.jsonl")
handle(c, msg(3, {VARTA: 1}, W))
reply, out = handle(c, msg(4, {VARTA: 0}, W))
check("two minutes at the flag but the town is no longer ours: it stays", entry(reply, "Alpha")[1:3] == [1, VARTA], reply)
check("...and the loss counts as fighting", c.holds["Alpha"]["fight"] == 4.0, c.holds)
reply, out = handle(c, msg(5, {VARTA: 1}, W))
check("the town comes back while it is there: the same hold goes on, no second one", list(c.holds) == ["Alpha"] and c.holds["Alpha"]["since"] == 2.0 and not hold_lines(out)
      and entry(reply, "Alpha")[1:3] == [1, VARTA], (c.holds, hold_lines(out)))
reply, out = handle(c, msg(5.5, {VARTA: 1}, W))
check("...and it is released a minute and a half after the town was last not ours", entry(reply, "Alpha")[1:3] == [3, -1] and "quiet for 1.5 minutes" in out, hold_lines(out))
c = held("unit25y.jsonl")
for m in (3, 4, 5, 6):
    handle(c, msg(m, {VARTA: 0}, W))
reply, out = handle(c, msg(7, {VARTA: 0}, W))
check("still lost after five minutes: released, and the note says the town is not ours", entry(reply, "Alpha")[1:3] == [3, -1] and "5 minutes are up, and the town is not ours" in out, hold_lines(out))

# 9. switched off in the middle of a game, and a new game
c = held("unit25z.jsonl")
relay.HOLD_TAKEN_TOWNS = False
reply, out = handle(c, msg(3, {VARTA: 1}, W))
check("switched off while a team holds: the hold ends on the next report", not c.holds and entry(reply, "Alpha")[1:3] == [3, -1] and "switched off" in out, hold_lines(out))
relay.HOLD_TAKEN_TOWNS = True
c = held("unit25aa.jsonl")
reply, out = handle(c, msg(1, {}, W))
check("the game clock goes back (a new game): no hold is carried over", not c.holds and "new game" in out and all(v == [3, -1] for v in codes(reply).values()), codes(reply))

# 10. with the model in command the hold sits on top of its plan, and the model is told nothing about it
relay.RULES_ONLY = False
prompts = []
def good(messages, think):
    prompts.append(messages[1]["content"])
    return json.dumps({"situation": "s", "intent": "from the model", "teams": {n: {"role": "ARMOUR" if n in NAMES[:4] else "INFANTRY", "order": "TAKE_TOWNS",
                                                                               "target": None, "why": "test"} for n in NAMES}}), False
relay.ask_model = good
c = commander("unit25ab.jsonl")
handle(c, msg(1, {}, W))
reply, out = handle(c, msg(2, {VARTA: 1}, W))
check("model game: the town taken wakes the model, its plan is used, and the holder is still sent to the flag",
      len(prompts) == 2 and "from the model" in reply and entry(reply, "Alpha")[1:3] == [1, VARTA] and rows(c)[-1].get("holding") == {"Alpha": "Varta"}, (len(prompts), reply))
check("...the model's situation says nothing of holds", "hold" not in prompts[-1][prompts[-1].index("CURRENT SITUATION:"):].lower().replace("household", ""), prompts[-1][-600:])
def other(messages, think):
    plan = json.loads(good(messages, think)[0]); plan["teams"]["Alpha"].update({"order": "RETURN_TO_BASE"}); return json.dumps(plan), False
c = commander("unit25ac.jsonl")
handle(c, msg(1, {}, W))
handle(c, msg(2, {VARTA: 1}, W))
c.standing["Alpha"].update({"order": "ATTACK_BASE", "since": 2.0})
reply = c.reply(state_of(msg(2, {VARTA: 1}, W)))
check("an order the commander gives the holder comes before the hold", entry(reply, "Alpha")[1:3] == [2, -1], reply)
relay.RULES_ONLY = True

# 11. the start-up option exists and the banner states the rule
source = open(os.path.join(sys.argv[1], "relay.py"), encoding="utf-8").read()
check("--no-hold is read at start-up and the banner says whether teams hold", '"--no-hold" in sys.argv[1:]' in source and "teams hold a town they have just taken" in source)

print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
