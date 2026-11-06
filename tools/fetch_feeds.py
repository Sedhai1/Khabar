#!/usr/bin/env python3
"""Collect recent headlines from the RSS/Atom feeds in tools/feeds.json.

Writes one JSON file (default: latest.json) with the items published in the
last MAX_AGE_HOURS hours. Standard library only. A broken feed is recorded
in the "feeds" status list and skipped; it never stops the run.

Usage: python3 tools/fetch_feeds.py [output.json]
"""
import html, json, re, sys, time
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

MAX_AGE_HOURS = 36
MAX_PER_FEED = 40
SUMMARY_CHARS = 400
UA = "Mozilla/5.0 (compatible; KhabarFeedBot/1.0; +https://github.com/Sedhai1/Khabar)"
NPT = timezone(timedelta(hours=5, minutes=45))

def strip(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()

def local(tag):
    return tag.rsplit("}", 1)[-1].lower()

def child_text(el, *names):
    for c in el:
        if local(c.tag) in names:
            if local(c.tag) == "link" and c.get("href"):
                if c.get("rel", "alternate") == "alternate":
                    return c.get("href")
                continue
            if (c.text or "").strip():
                return c.text.strip()
    return ""

def parse_date(s):
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except Exception:
        try:
            d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def fetch(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"})
    with urlopen(req, timeout=25) as r:
        return r.read()

def parse(raw):
    root = ET.fromstring(raw)
    out = []
    for el in root.iter():
        if local(el.tag) not in ("item", "entry"):
            continue
        title = strip(child_text(el, "title"))
        link = child_text(el, "link") or child_text(el, "guid", "id")
        summ = strip(child_text(el, "description", "summary", "content", "encoded"))
        date = parse_date(child_text(el, "pubdate", "published", "updated", "date"))
        if title and link:
            out.append((title, link.strip(), summ, date))
    return out

def main(out_path):
    feeds = json.loads(Path(__file__).with_name("feeds.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=MAX_AGE_HOURS)
    items, status, seen = [], [], set()
    for f in feeds:
        st = {"name": f["name"], "section": f["section"], "ok": False, "count": 0}
        try:
            entries = parse(fetch(f["url"]))
            n = 0
            for title, link, summ, date in entries:
                if date and date < cutoff:
                    continue
                key = link.split("?")[0] if "news.google.com" not in link else title.lower()
                if key in seen:
                    continue
                seen.add(key)
                if len(summ) > SUMMARY_CHARS:
                    summ = summ[:SUMMARY_CHARS].rsplit(" ", 1)[0] + " …"
                if summ == title or summ.startswith(title):
                    summ = ""
                items.append({
                    "source": f["name"], "section": f["section"], "title": title,
                    "summary": summ, "link": link,
                    "published": date.isoformat() if date else None,
                })
                n += 1
                if n >= MAX_PER_FEED:
                    break
            st.update(ok=True, count=n)
        except Exception as e:
            st["error"] = f"{type(e).__name__}: {e}"[:200]
        status.append(st)
        time.sleep(0.5)
    items.sort(key=lambda i: i["published"] or "", reverse=True)
    data = {
        "fetched_at": now.astimezone(NPT).isoformat(timespec="minutes"),
        "max_age_hours": MAX_AGE_HOURS,
        "feeds": status,
        "items": items,
    }
    Path(out_path).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(s["ok"] for s in status)
    print(f"{ok}/{len(status)} feeds OK, {len(items)} items -> {out_path}")
    for s in status:
        if not s["ok"]:
            print(f"  FAILED {s['name']}: {s.get('error')}")
    if ok == 0:
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "latest.json")
