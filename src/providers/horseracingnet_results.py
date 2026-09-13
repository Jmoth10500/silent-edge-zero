"""
Real results parser for horseracing.net — a genuine, fetchable,
structured alternative found 2026-09-13 while independently verifying a
ChatGPT-compiled results table Jonathan brought in (his own message:
"Ive just Chat GPT the rase pick and got this"). The table's claimed
41.2% win strike rate was far enough above this project's own backtested
~23% (and the market's ~33%) to need real verification before trusting
it — see docs/BUILD_LOG.md's "sanity-check suspicious results" rule.
Spot-checked 9 real data points across 3 courses (wins, places, a
non-runner, a voided race) directly against a fresh real fetch of this
site — all 9 matched exactly. This module fetches and parses it
properly from the real source itself, rather than trusting an LLM's
transcription of it.

**Real page shape, confirmed live:** one course+day page
(`https://www.horseracing.net/results/<course-slug>/<dd-mm-yy>/`)
covers every race at that meeting. Each race is introduced by a real
`<h2 id="HH:MM">` heading; each runner is a `<li class="results-table-row">`
containing a `class="number position"` span whose visible text is either
plain ("3rd"), wrapped in a nested `<span class="position-highlight">`
for the winner ("1st"), or a real non-finish marker ("NR", "-" for a
voided race).
"""
import re

_RACE_HEADER_RE = re.compile(r'<h2 id="(\d{1,2}:\d{2})">[^<]*Result</h2>')
_RUNNER_ROW_OPEN_RE = re.compile(r'<li class="results-table-row"[^>]*>')
_RUNNER_NAME_RE = re.compile(r'class="runner-title">\s*([^<]+?)\s*</a>')
_POSITION_MARKER = 'class="number position"'


def split_into_races(html: str) -> list[tuple[str, str]]:
    """Real page -> [(off_time 'HH:MM', that race's own HTML section)].
    Splits on the page's own real `<h2 id="HH:MM">...Result</h2>`
    headings — never guesses race boundaries."""
    matches = list(_RACE_HEADER_RE.finditer(html))
    sections = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        sections.append((m.group(1), html[start:end]))
    return sections


def _extract_finish_text(li_html: str) -> str | None:
    """Real finishing-position text for one runner's `<li>` block,
    whether it's plain ('3rd'), nested in a winner's highlight span
    ('1st'), or a real non-finish marker ('NR', '-'). None if the real
    marker itself isn't present — never guessed."""
    idx = li_html.find(_POSITION_MARKER)
    if idx == -1:
        return None
    tag_end = li_html.find(">", idx)  # end of the <span class="number position"> tag itself
    if tag_end == -1:
        return None
    window = li_html[tag_end + 1:tag_end + 1 + 250]
    text = re.sub(r"<[^>]+>", " ", window)
    tokens = text.split()
    return tokens[0] if tokens else None


def parse_race_runners(section_html: str) -> list[dict]:
    """Real runner list for one race's section — [{horse_name, finish_text}, ...].
    `finish_text` is the real raw marker text (a position like '3rd', or
    a real non-finish code like 'NR'/'-') — turning that into a
    structured finishing_position/result_note is the caller's job (see
    parse_finish_text), same separation of concerns as
    scripts/collect_race_results.py's own parse_outcome_code.

    Real, deliberate design: each runner's real `<li class="results-
    table-row">` block contains its OWN nested `<ul><li>` (jockey/trainer
    detail) — a naive '.*?</li>' regex would truncate at that inner
    closing tag before reaching the real horse name or, on some rows,
    the position marker. Splitting on the OPENING row tag instead (never
    trying to find its matching close) sidesteps that entirely — a
    runner's own real name/position always appear before the next
    runner's opening tag, regardless of what's nested inside its own
    block."""
    opens = list(_RUNNER_ROW_OPEN_RE.finditer(section_html))
    out = []
    for i, m in enumerate(opens):
        start = m.end()
        end = opens[i + 1].start() if i + 1 < len(opens) else len(section_html)
        block = section_html[start:end]
        name_match = _RUNNER_NAME_RE.search(block)
        if not name_match:
            continue
        finish_text = _extract_finish_text(block)
        out.append({"horse_name": name_match.group(1).strip(), "finish_text": finish_text})
    return out


def parse_finish_text(finish_text: str | None) -> tuple[int | None, str | None]:
    """Real (finishing_position, result_note) from horseracing.net's raw
    marker text. A real ordinal ('1st', '2nd', '23rd'...) becomes a real
    int position; 'NR' and '-' (voided) become a real result_note with
    no position; anything else unrecognised is returned as its own
    result_note rather than guessed into a number."""
    if not finish_text:
        return None, None
    text = finish_text.strip()
    if text == "-":
        return None, "VOID"
    if text.upper() == "NR":
        return None, "NR"
    m = re.match(r"^(\d+)(?:st|nd|rd|th)$", text, re.IGNORECASE)
    if m:
        return int(m.group(1)), None
    return None, text
