#!/usr/bin/env python3
"""Validate one edition JSON against EDITORIAL.md. Exit 1 on errors."""
import json, re, sys
from urllib.parse import urlparse

SECTIONS = ["nepal", "world", "india_china", "economy", "ai"]
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(am|pm)$")
BANNED = ["ऐतिहासिक", "चौंकाउने", "चौँकाउने", "सनसनीपूर्ण", "हामी "]

errors, warnings = [], []
def err(m): errors.append(m)
def warn(m): warnings.append(m)

def nepali_ratio(s):
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if DEVANAGARI.match(c)) / len(letters)

def check_url(u, where):
    p = urlparse(u or "")
    if p.scheme != "https" or not p.netloc:
        err(f"{where}: url must be https:// ({u!r})")

def main(path):
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: cannot parse JSON: {e}"); sys.exit(1)

    if not ID_RE.match(str(d.get("id", ""))):
        err("id must look like YYYY-MM-DD-am|pm")
    elif not path.rstrip("/").endswith(d["id"] + ".json"):
        err(f"file name must be {d['id']}.json")
    ga = str(d.get("generated_at", ""))
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?\+05:45$", ga):
        err("generated_at must be ISO time with +05:45 offset")
    elif ID_RE.match(str(d.get("id", ""))):
        date, half = d["id"][:10], d["id"][-2:]
        hour = int(ga[11:13])
        if ga[:10] != date:
            err("id date must equal the Nepal date in generated_at")
        if (half == "am") != (hour < 12):
            err("id am/pm must match the Nepal-time hour in generated_at")

    m = d.get("markets")
    if not isinstance(m, dict) or not m.get("items"):
        warn("no markets block")
    else:
        if not m.get("as_of"):
            err("markets.as_of is required (which session the figures are for)")
        names = []
        for i, it in enumerate(m["items"]):
            w = f"markets.items[{i}]"
            if not it.get("name"): err(f"{w}: name missing")
            names.append(it.get("name", ""))
            if not isinstance(it.get("value"), (int, float)):
                err(f"{w}: value must be a number")
            cp = it.get("change_pct")
            if cp is not None and not isinstance(cp, (int, float)):
                err(f"{w}: change_pct must be number or null")
            if isinstance(cp, (int, float)) and abs(cp) > 15:
                warn(f"{w}: change_pct {cp}% is unusually large — recheck")
            if not it.get("source"): err(f"{w}: source missing")
            check_url(it.get("url"), w)
        if not any("S&P" in n for n in names):
            warn("markets: S&P 500 missing")

    stories = d.get("stories")
    if not isinstance(stories, list) or not stories:
        err("stories missing"); stories = []
    if not 8 <= len(stories) <= 12:
        warn(f"{len(stories)} stories (target 8–12)")
    order = []
    titles = set()
    for i, s in enumerate(stories):
        w = f"stories[{i}]"
        sec = s.get("section")
        if sec not in SECTIONS:
            err(f"{w}: section must be one of {SECTIONS}"); continue
        order.append(SECTIONS.index(sec))
        for f in ("title", "summary"):
            v = s.get(f, "")
            if not isinstance(v, str) or not v.strip():
                err(f"{w}: {f} missing"); continue
            if nepali_ratio(v) < 0.7:
                err(f"{w}: {f} is not mostly Nepali")
            for b in BANNED:
                if b in v: warn(f"{w}: {f} contains loaded word '{b.strip()}'")
            # Latin digits are fine inside names like G7 or GPT-5; warn otherwise
            for tok in v.replace("S&P 500", "S&P").split():
                if re.search(r"[0-9]", tok) and not re.search(r"[A-Za-z]", tok):
                    warn(f"{w}: {f} uses Latin digits ('{tok}'); use Devanagari")
                    break
        t = s.get("title", "")
        if len(t) > 110: warn(f"{w}: title long ({len(t)} chars)")
        if t in titles: err(f"{w}: duplicate title")
        titles.add(t)
        summ = s.get("summary", "")
        if len(summ) > 700: warn(f"{w}: summary long ({len(summ)} chars)")
        for f in ("impact", "unverified"):
            if f in s and (not isinstance(s[f], str) or not s[f].strip()):
                err(f"{w}: {f} present but empty — omit it")
        if "sides" in s:
            if not isinstance(s["sides"], list) or len(s["sides"]) < 2:
                err(f"{w}: sides needs ≥2 entries (or omit)")
            else:
                for j, sd in enumerate(s["sides"]):
                    if not sd.get("who") or not sd.get("says"):
                        err(f"{w}.sides[{j}]: who/says missing")
        srcs = s.get("sources") or []
        if not srcs:
            err(f"{w}: no sources")
        hosts = set()
        for j, src in enumerate(srcs):
            if not src.get("name"): err(f"{w}.sources[{j}]: name missing")
            check_url(src.get("url"), f"{w}.sources[{j}]")
            hosts.add(urlparse(src.get("url", "")).netloc.removeprefix("www."))
        if len(hosts) < 2:
            err(f"{w}: needs ≥2 sources from different sites")
    if order != sorted(order):
        err("stories must be ordered by section: " + ", ".join(SECTIONS))
    present = {SECTIONS[o] for o in order}
    for sec in SECTIONS:
        if sec not in present:
            warn(f"section '{sec}' has no story")

    for w_ in warnings: print("WARN:", w_)
    for e in errors: print("ERROR:", e)
    if errors:
        sys.exit(1)
    print(f"OK — {len(stories)} stories")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: validate.py data/editions/<id>.json"); sys.exit(2)
    main(sys.argv[1])
