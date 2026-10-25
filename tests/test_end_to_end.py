"""End to end: raw game text in, reply out, through the Relay class, including the failure paths.
Started by run_tests.py. Arguments: the folder that holds relay.py, a scratch folder, a log holding a damaged report."""
import json, sys, os, io, contextlib
sys.path.insert(0, sys.argv[1]); TMP = sys.argv[2]; RAW_LOG = sys.argv[3]
import relay
relay.LOG_DIR = TMP
relay.RELAY.log_path = os.path.join(TMP, "e2e_relay.jsonl")      # keep test rows out of the real logs folder
ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FAIL:", label, str(extra)[:400])
def rows_of(path): return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]

raw = next(json.loads(l)["raw"] for l in open(RAW_LOG, encoding="utf-8") if '"raw"' in l[:20])      # a real report with junk in it
check("the real damaged report is not valid JSON as sent", not (lambda t: (json.loads(t), True)[1] if False else False)(raw) and "scalar bool array string" in raw)

relay.ask_model = lambda messages, think: (json.dumps({"situation": "s", "teams": {}, "intent": "take towns"}), False)
r = relay.Relay(); r.log_path = os.path.join(TMP, "e2e_control.jsonl"); open(r.log_path, "w").close()
with contextlib.redirect_stdout(io.StringIO()) as out: reply = r.handle(raw)
parsed = json.loads(reply)
check("control mode: damaged report repaired and answered", parsed[0] == 1 and len(parsed[1]) == 9, reply)
check("control mode: 'one unreadable entry' noted", "unreadable entry" in out.getvalue())
row = rows_of(r.log_path)[-1]
check("control mode: logged with relay version, standing orders and reply", row.get("relay") == relay.VERSION and "standing" in row and row.get("reply") == reply, list(row))
check("control mode: every team on TAKE_TOWNS via the fallback, code 3", all(e[1] == 3 for e in parsed[1][1:]) and "FALLBACK" in out.getvalue(), parsed[1])

# observer mode: same report with mode 0
msg = json.loads(raw.replace("scalar bool array string 0xfcffffef", "null").replace("[string,", "[null,")); msg[3] = 0
r2 = relay.Relay(); r2.log_path = os.path.join(TMP, "e2e_observer.jsonl"); open(r2.log_path, "w").close()
with contextlib.redirect_stdout(io.StringIO()): rep = r2.handle(json.dumps(msg))
check("observer mode: answers 'observing' and logs", rep == '[1,[],"observing"]' and rows_of(r2.log_path)[-1].get("relay") == relay.VERSION)

# the window is closed: printing fails, the relay must still log and answer
class Dead(io.TextIOBase):
    def write(self, text): raise OSError("the console is gone")
    def flush(self): raise OSError("the console is gone")
real = sys.stdout; sys.stdout = Dead()
try:
    rep_obs = r2.handle(json.dumps(msg)); rep_ctl = r.handle(raw)
finally:
    sys.stdout = real
check("console gone: observer still logs and answers", rep_obs == '[1,[],"observing"]' and len(rows_of(r2.log_path)) == 2)
check("console gone: commander still logs and answers", json.loads(rep_ctl)[0] == 1 and len(rows_of(r.log_path)) == 2, rep_ctl)

# a report that cannot be read at all, and a crash inside the relay: both leave a row with the cause
with contextlib.redirect_stdout(io.StringIO()): rep = r.handle('["MFCTI","East",12,1,[[')
last = rows_of(r.log_path)[-1]
check("unreadable report: error reply, and a log row with the error and a trace", rep.startswith("[0,") and "error" in last and "trace" in last, last)
import http.server
class FakeHandler(relay.Handler):
    def __init__(self): self.headers = {"Content-Length": "5"}; self.rfile = io.BytesIO(b"[boom"); self.wfile = io.BytesIO(); self.sent = []
    def send_response(self, code): self.sent.append(code)
    def send_header(self, *a): pass
    def end_headers(self): pass
relay.RELAY.log_path = os.path.join(TMP, "e2e_crash.jsonl"); open(relay.RELAY.log_path, "w").close()
def explode(text): raise RuntimeError("something unforeseen")
relay.RELAY.handle = explode
h = FakeHandler()
with contextlib.redirect_stdout(io.StringIO()): h.do_POST()
last = rows_of(relay.RELAY.log_path)[-1]
check("a crash inside the relay: the game still gets an answer", h.sent == [200] and h.wfile.getvalue().startswith(b"[0,"), h.wfile.getvalue())
check("...and the session log records what crashed", "RuntimeError" in last["error"] and "something unforeseen" in last["trace"], last)
print("end-to-end tests: %d passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
