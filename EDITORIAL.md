# खबर — editorial rules for each edition

This file is the standing brief for whoever writes an edition (normally the
scheduled Claude run). The reader is a Nepali man in Nepal, moderate tech
comfort, who reads Nepali comfortably. The goal is accurate, calm, balanced
news — the opposite of a social-media feed.

## When
Two editions per day, Nepal time (UTC+05:45):
- `am` edition ~06:30 NPT (catches the US market close, ~02:45 NPT)
- `pm` edition ~18:30 NPT
Edition id = `YYYY-MM-DD-am` / `YYYY-MM-DD-pm`, using the **Nepal** date and
`am` if the Nepal-time hour is < 12, else `pm`.

## What goes in (8–12 stories total)
Sections, in this order (`section` field value in brackets):
1. नेपाल (`nepal`) — 2–3 stories: national politics, economy, major events.
2. विश्व राजनीति (`world`) — 2–3 stories: the biggest global political stories.
3. भारत–चीन (`india_china`) — 1–2 stories: India, China, India–China, and
   either country's dealings with Nepal.
4. अर्थतन्त्र र सेयर बजार (`economy`) — 1–2 stories plus the `markets` block.
   US markets are the priority (S&P 500, Nasdaq Composite, Dow Jones), then
   NEPSE, then USD→NPR. Oil (Brent) if it moved notably.
5. AI र प्रविधि (`ai`) — 1–2 stories: important AI/technology developments
   explained for a non-specialist (what it is, why it matters).

Selection test: "Will this still matter in a week, or does it affect many
people?" Skip celebrity, crime-of-the-day, viral items, sports (unless huge),
and anything sourced only from social media.
If a story was in the previous edition and nothing new happened, drop it. If
it developed, keep it and say what is new.

## Sourcing (non-negotiable)
- Every story needs **≥2 independent sources**, at least one of them a wire
  service or public broadcaster: Reuters, AP, AFP, BBC, NHK, DW, Al Jazeera,
  The Hindu / Indian Express (for India), SCMP / Xinhua-as-official-position
  (for China), Kathmandu Post / Kantipur / Onlinekhabar / BBC Nepali / RSS
  (for Nepal). Partisan outlets may be used only to report what a side says.
- Contested political stories: read at least two outlets from different
  countries or political leanings before writing.
- Use only facts stated in a source you actually opened or saw in results.
  If sources disagree on a number, give the range or say "स्रोतअनुसार फरक".
- If a fact could not be confirmed, either leave it out or put it in the
  story's `unverified` field. Never fill gaps from memory.
- Market figures must come from a page showing the close and its date. If you
  cannot find a dated figure, omit that item rather than guess. `as_of` must
  say which session the figures are for (e.g. "शुक्रबार, अक्टोबर २३ को बन्द").

## Writing (Nepali)
- Plain spoken Nepali as written by Kantipur / BBC Nepali — short sentences,
  common words. Avoid heavy Sanskritised vocabulary and English jargon; if an
  English term is unavoidable (e.g. AI, Nasdaq), keep it and explain once.
- Use Devanagari digits (०१२३४५६७८९) in prose.
- Big numbers: write in both systems when it matters, e.g.
  "१० अर्ब डलर (१ हजार करोड डलर)". Double-check: 1 million = १० लाख,
  1 billion = १ अर्ब = १०० करोड, 1 trillion = १० खर्ब.
- Foreign names: standard Nepali-media spelling (ट्रम्प, मोदी, सी जिनपिङ,
  पुटिन, जेलेन्स्की, नेतन्याहु). Be consistent within an edition.
- `title`: one line, factual, no adjectives like "ऐतिहासिक", "चौंकाउने".
- `summary`: 2–4 sentences — what happened, where, when, who. Facts only.
- `sides` (for any story with disagreement): what each side says, attributed
  ("सरकारको भनाइ …", "विपक्षीको भनाइ …"). Equal length and tone for each.
- `impact` (optional): one sentence, only when there is a concrete, sourced
  link to Nepal (remittance, trade, prices, Nepali workers, border, aid).
  Do not invent speculative impacts.
- No opinions, no predictions presented as facts, no "हामी", no emojis.
- Summaries are written fresh in Nepali; never translate a whole article
  or copy sentences from a source.

## Format
Write `data/editions/<id>.json` matching this shape:

```json
{
  "id": "2026-10-25-am",
  "generated_at": "2026-10-25T06:35:00+05:45",
  "markets": {
    "as_of": "शुक्रबार, अक्टोबर २३ को बन्द",
    "items": [
      {"name": "S&P 500", "value": 6791.69, "change_pct": 0.79,
       "source": "Reuters", "url": "https://..."},
      {"name": "डलर (USD→NPR)", "value": 140.25, "unit": "रु",
       "change_pct": null, "source": "नेपाल राष्ट्र बैंक", "url": "https://..."}
    ]
  },
  "stories": [
    {
      "section": "world",
      "title": "…",
      "summary": "…",
      "sides": [{"who": "…", "says": "…"}],
      "impact": "…",
      "unverified": "…",
      "sources": [{"name": "Reuters", "url": "https://..."},
                  {"name": "BBC", "url": "https://..."}]
    }
  ]
}
```
`sides`, `impact`, `unverified` are optional (omit rather than leave empty).
`value` and `change_pct` are plain numbers (Latin digits); the page formats
them. `change_pct` may be null.

## Publish steps
1. `python3 tools/validate.py data/editions/<id>.json` — must print OK.
   Fix every error; warnings should be fixed unless genuinely impossible.
2. `python3 tools/update_index.py` — rebuilds `data/index.json`, keeps the
   newest 14 editions and deletes older edition files.
3. Commit and push to `main`. GitHub Pages redeploys in 1–2 minutes.
4. Check `https://sedhai1.github.io/khabar/data/index.json` shows the new id.
