import re, sys, collections
# Static checks on SQS files: CRLF line ends, no duplicate labels, every goto "X" has a label, brackets balance per line,
# no comment after code on a line, and no variable first assigned inside a Call Format string.
bad = 0
for path in sys.argv[1:]:
    raw = open(path, "rb").read().decode("latin-1")
    problems = []
    if "\n" in raw.replace("\r\n", ""): problems.append("bare line feed")
    lines = raw.split("\r\n")
    labels = collections.Counter(l.strip()[1:].strip().lower() for l in lines if l.strip().startswith("#"))
    for name, n in labels.items():
        if n > 1: problems.append("label #%s defined %d times" % (name, n))
    assigned = set()
    for i, l in enumerate(lines, 1):
        s = l.strip()
        if not s or s.startswith(";") or s.startswith("#"): continue
        code = re.sub(r'"(?:[^"]|"")*"', '""', s)           # drop string contents
        for a, b in ("()", "[]", "{}"):
            if code.count(a) != code.count(b): problems.append("line %d: unbalanced %s%s" % (i, a, b))
        if s.count('"') % 2: problems.append("line %d: odd number of quotes" % i)
        for m in re.finditer(r'goto\s+"([^"]+)"', s, re.I):
            if m.group(1).lower() not in labels: problems.append("line %d: goto \"%s\" has no label" % (i, m.group(1)))
        if "LLM" in path.replace("\\", "/").split("/")[-2:][0] or "llm" in s.lower():
            if re.search(r";\s*[A-Za-z ]{12,}$", code) and not re.search(r";\s*(_|\?|goto|Call|PublicVariable|\[|[A-Za-z0-9_%]+\s*(=|Set|Exec|select|In|doMove|addEventHandler))", code.split(";")[-1] and ";" + code.split(";")[-1], re.I):
                problems.append("line %d: looks like a comment after code" % i)
        # variables assigned outside Call strings, in order
        for m in re.finditer(r'(?<![A-Za-z0-9_"%])(_[A-Za-z0-9]+)\s*=(?!=)', code): assigned.add(m.group(1).lower())
        for call in re.finditer(r'Call\s+Format\s*\[\s*"((?:[^"]|"")*)"', s, re.I):
            for m in re.finditer(r'(?<![A-Za-z0-9_%])(_[A-Za-z0-9]+)\s*=(?!=)', call.group(1)):
                if m.group(1).lower() not in assigned: problems.append("line %d: %s is first assigned inside a Call" % (i, m.group(1)))
    print("%-70s %s" % (path[-70:], "ok (%d lines, %d labels)" % (len(lines), len(labels)) if not problems else "PROBLEMS"))
    for p in problems: print("     ", p); bad += 1
print("mission scripts: %d files checked, %d problems" % (len(sys.argv) - 1, bad))
sys.exit(1 if bad else 0)
