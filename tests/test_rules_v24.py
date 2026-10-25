"""Unit tests for what was new in relay version 24: a model that is slow or down may not cost the commander his
tempo. One plan has a deadline in real seconds for all attempts together; past it the rule-based plan is used;
after two failures in a row the model is left alone for a while.
Started by run_tests.py. Arguments: the folder that holds relay.py, a scratch folder."""
import json, sys, os, io, contextlib, threading, time, urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, sys.argv[1]); TMP = sys.argv[2]
import relay
T = [("Lany", 200, 10000, 4300), ("Varta", 100, 8900, 7000), ("Petrovice", 400, 3000, 5400), ("Mala Ves", 100, 8000, 4700)]
BASE = (10019, 4009)
def man(t, w=""): return [t, w, False]
SQUAD = [man("SoldierEB")] * 5 + [man("SoldierELAW", "RPGLauncher")] * 4
def tanks(n): return [["MFCTI116T80", "V", True, True, True, 0.8, True, True] for _ in range(n)]
LEADER = [man("SoldierEAT", "AT4Launcher")]
def team(name, kit, x, y, seat=1, speed=20):
    men = len(kit) if kit and kit[0][1] != "V" else 3 * len(kit)
    near_m = ((x - T[0][2]) ** 2 + (y - T[0][3]) ** 2) ** .5
    return [name, False, 0, 12, True, 100000, men, 0, near_m, False, True, kit, x, y, ((x - BASE[0]) ** 2 + (y - BASE[1]) ** 2) ** .5,
            seat, speed, True, 0, 0.0, 0.0, False, True, 0.9, False, True, 0, "", "", ""]
NAMES = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]
HEAVY = [1, 1, 1, 1, 0, 0, 1, 0]
def msg(minute, owner=0):
    """A report in which every team moves, and one town changes owner when asked, so the plan is asked for again."""
    towns = [[n, v, (owner if i == 1 else 0), x, y] for i, (n, v, x, y) in enumerate(T)]
    teams = [team("Commander", LEADER, *BASE, seat=0, speed=0)]
    for i, n in enumerate(NAMES):
        teams.append(team(n, tanks(3) if i < 4 else SQUAD, BASE[0] + 3000 + 40 * minute, BASE[1] + 2000 + 30 * i, seat=1 if i < 4 else 0))
    return ["MFCTI", "East", minute * 60, 1, towns, [900000, HEAVY, True, 0, False, -1, BASE[0], BASE[1]], teams, [], [], [], [], 13, [0, 0, 0], True, 2]
def state_of(m): return relay.parse_mfcti(json.loads(json.dumps(m)))
def commander(name): return relay.MfctiCommander("East", os.path.join(TMP, name))
def plan(order="TAKE_TOWNS"):
    return {"situation": "s", "intent": "from the model", "teams": {n: {"role": "ARMOUR" if n in NAMES[:4] else "INFANTRY", "order": order,
                                                                         "target": None, "why": "test"} for n in NAMES}}
ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FAIL:", label, str(extra)[:900])
def handle(c, m):
    s = state_of(m)
    with contextlib.redirect_stdout(io.StringIO()) as out: reply = c.handle(s)
    return reply, out.getvalue()
def rows(c): return [json.loads(l) for l in open(c.log_path, encoding="utf-8")]
def legal(reply):
    r = json.loads(reply)
    return r[0] == 1 and len(r[1]) == 9 and all(len(e) == 4 for e in r[1]) and any(e[1] == 3 for e in r[1][1:])
real_ask_model = relay.ask_model
now = [1000.0]
relay.clock = lambda: now[0]
calls = []
def good(messages, think):
    calls.append("good"); return json.dumps(plan()), False
def dead(messages, think):
    calls.append("dead"); raise urllib.error.URLError("timed out")
def broken(messages, think):
    calls.append("broken"); raise urllib.error.HTTPError("http://localhost:11434/api/chat", 500, "Internal Server Error", None, None)

check("relay is version 24 or later", relay.VERSION >= 24, relay.VERSION)
check("one plan may take 30 seconds, two failures rest the model for 180", (relay.MODEL_DEADLINE, relay.MODEL_FAILS_TO_REST, relay.MODEL_REST_SECONDS) == (30, 2, 180))

# 1. a model that is down from the first report: the teams still get orders, from the rules
relay.ask_model = dead; calls.clear()
c = commander("unit24a.jsonl")
reply, out = handle(c, msg(1))
check("first report, model down: the reply is a full set of orders, not an error", legal(reply), reply)
check("...and the console says the model gave no answer and that the rules decided", "MODEL  no answer" in out and "FALLBACK: no plan from the model" in out, out[-500:])
row = rows(c)[-1]
check("...and the log row is marked", row.get("model_failed") and row.get("fallback") is True and row.get("reply") == reply, {k: row.get(k) for k in ("model_failed", "fallback")})
check("...and every team has a standing order", len(c.standing) == 8 and all(o["order"] == "TAKE_TOWNS" for o in c.standing.values()), c.standing)
check("the model was tried once, not three times", calls == ["dead"], calls)

# 2. two failures in a row: the model is left alone, then tried again
reply, out = handle(c, msg(2, owner=1))
check("second failure in a row: the model is declared down", "MODEL  DOWN: 2 failures in a row" in out and legal(reply), out[-400:])
calls.clear()
now[0] += 60
reply, out = handle(c, msg(3, owner=2))
check("while it rests it is not asked, and the rules still answer", calls == [] and "MODEL  resting" in out and legal(reply), (calls, out[-300:]))
check("...the resting report is marked in the log too", "resting" in str(rows(c)[-1].get("model_failed")), rows(c)[-1].get("model_failed"))
now[0] += relay.MODEL_REST_SECONDS
relay.ask_model = good
reply, out = handle(c, msg(4, owner=1))
check("after the rest it is asked again, and a good answer is used", calls == ["good"] and "MODEL  answering again after 2 failures" in out and "from the model" in reply, (calls, out[-300:]))
check("...and that report is not marked as failed", "model_failed" not in rows(c)[-1] and c.model_fail_run == 0)
relay.ask_model = dead; calls.clear()
reply, out = handle(c, msg(5, owner=2))
check("one failure after a recovery does not rest the model", "MODEL  no answer" in out and "DOWN" not in out and c.model_rest_until <= now[0], out[-300:])
relay.ask_model = good
reply, out = handle(c, msg(6, owner=1))
check("...and a good answer in between resets the count", c.model_fail_run == 0 and "answering again after 1 failures" in out)
check("the total of failures is kept", c.model_failed_total == 3, c.model_failed_total)

# 3. a server error counts the same as silence
relay.ask_model = broken
c = commander("unit24b.jsonl")
reply, out = handle(c, msg(1))
check("HTTP 500 from the model: orders from the rules, and the reason is in the log", legal(reply) and "500" in rows(c)[-1]["model_failed"], rows(c)[-1].get("model_failed"))

# 4. a healthy model: nothing new is said, nothing is marked
relay.ask_model = good
c = commander("unit24c.jsonl"); said = ""
for m in range(1, 7):
    reply, out = handle(c, msg(m, owner=m % 3)); said += out
check("a healthy model: no MODEL lines, no marks, its plans are used", "MODEL  " not in said and not any("model_failed" in r for r in rows(c)) and "from the model" in reply, said[-300:])

# 5. rules-only games are untouched
relay.RULES_ONLY = True; relay.ask_model = dead; calls.clear()
c = commander("unit24d.jsonl"); said = ""
for m in range(1, 5):
    reply, out = handle(c, msg(m, owner=m % 3)); said += out
check("--rules: the model is never called and nothing is marked as failed", calls == [] and legal(reply) and not any("model_failed" in r for r in rows(c)) and "MODEL  " not in said, calls)
relay.RULES_ONLY = False

# 6. the deadline is shared by all attempts
def slow_wrong(messages, think):
    calls.append("wrong"); now[0] += 12; return "this is not JSON", False
relay.ask_model = slow_wrong; calls.clear()
c = commander("unit24e.jsonl")
reply, out = handle(c, msg(1))
check("answers that are wrong still get their retries, and the rules step in after them", calls == ["wrong"] * relay.MAX_ATTEMPTS and legal(reply) and "FALLBACK: the model gave no legal plan" in out, (calls, out[-300:]))
check("...and a wrong answer is not counted as the model being down", "model_failed" not in rows(c)[-1] and c.model_fail_run == 0)
relay.MODEL_DEADLINE_AT = now[0] + 1.0
try:
    real_ask_model([{"role": "user", "content": "x"}], "low"); refused = False
except TimeoutError as error:
    refused = "used up" in str(error)
except Exception as error:
    refused = False
relay.MODEL_DEADLINE_AT = None
check("with less than 1.5 seconds left the model is not called at all", refused)
check("the deadline is cleared after a plan", relay.MODEL_DEADLINE_AT is None)

# 7. the real call against a real (stand-in) server: one that answers, one that is too slow
class Stub(BaseHTTPRequestHandler):
    delay = 0.0
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        time.sleep(Stub.delay)
        body = json.dumps({"message": {"content": json.dumps(plan())}, "done_reason": "stop", "eval_count": 400, "eval_duration": 3000000000}).encode()
        try:
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        except OSError:
            pass
    def log_message(self, *a): pass
server = HTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=server.serve_forever, daemon=True).start()
relay.OLLAMA_URL = "http://127.0.0.1:%d/api/chat" % server.server_address[1]
relay.ask_model = real_ask_model
relay.clock = time.time
relay.MODEL_DEADLINE = 3
c = commander("unit24f.jsonl")
began = time.time(); reply, out = handle(c, msg(1)); took = time.time() - began
check("a model that answers in time is used, over real HTTP", "from the model" in reply and "model_failed" not in rows(c)[-1] and took < 2.5, (took, out[-200:]))
check("...and its speed is in the log", rows(c)[-1]["decision"]["attempts"][0]["model"].get("eval_count") == 400)
Stub.delay = 5.0
began = time.time(); reply, out = handle(c, msg(2, owner=1)); took = time.time() - began
check("a model that takes 5 seconds against a 3-second deadline: the rules answer after about 3", legal(reply) and 2.5 < took < 4.5 and rows(c)[-1].get("model_failed"), (round(took, 1), out[-300:]))
relay.MODEL_DEADLINE = 30
server.shutdown()

# 8. the start-up option
check("--deadline=45 is read", relay.deadline_option(["logfile", "--deadline=45"], 30) == 45)
check("no option, a bad value or one below 5 leaves the default", relay.deadline_option(["--rules"], 30) == 30 and relay.deadline_option(["--deadline=soon"], 30) == 30 and relay.deadline_option(["--deadline=2"], 30) == 30)

print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
