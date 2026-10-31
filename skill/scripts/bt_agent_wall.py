"""What keeps an agent in tmux from acting on a message, read from its screen, and the notices waiting for it to pass.

A message typed into an agent is delivered only if the agent can act on it. pictures REQ-021's Planner (Codex, 2026-10-30
16:25) took a plan change request, emptied its input box and answered «■ You've hit your usage limit … try again at
4:32 PM»; later a Codex modal («Switch to gpt-6-luna for lower credit usage?») swallowed every notice until the operator
pressed 2. This module only reads text: `bt_agent_terminal` does the typing, the account move and the retries.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

# What an agent prints when its account ran out. Claude Code: «You've hit your weekly limit · resets Oct 31, 6pm»,
# «5-hour limit reached ∙ resets 3am», «Claude usage limit reached|1761868800», «You're out of extra usage · resets 3pm»;
# Codex: «■ You've hit your usage limit. Upgrade to Pro (…) or try again at 4:32 PM.»
LIMITED = re.compile(r"hit your (?:weekly |usage |session )?limit|usage limit reached|/usage-credits|"
                     r"(?:5-hour|weekly|session|opus|sonnet) limit reached|reached your (?:weekly |usage |session )?limit|"
                     r"out of extra usage", re.IGNORECASE)
# A question only the owner may answer: Claude Code's first run under an account asks him to accept bypass-permissions
# mode, and a Planner moved to that account waits on it (claude-luis, 2026-10-29); an operator may not accept it for him.
OWNER_PROMPT = re.compile(r"Bypass Permissions mode.*Yes, I accept", re.DOTALL)
# Codex's rate-limit prompt: harmless, answered «Keep current model» (the owner chose the model; never «never show again»)
MODEL_SWITCH = re.compile(r"Switch to \S+ for lower credit usage\?.*Keep current model", re.DOTALL | re.IGNORECASE)
KEEP_OPTION = re.compile(r"^\W*(\d)\.\s*Keep current model\s*$", re.MULTILINE | re.IGNORECASE)
# any other selection list or confirmation an agent waits on: typing into it would pick an option the owner never chose
BLOCKING = re.compile(r"enter select · esc back|Enter to confirm · Esc to cancel", re.IGNORECASE)

_MONTHS = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
                                       "dec"), 1)}
_CLOCK = re.compile(r"(?:try again at|resets?(?: at)?)\s+(?:(?P<mon>[A-Za-z]{3})[a-z]*\.?\s+(?P<day>\d{1,2})"
                    r"(?:st|nd|rd|th)?,?\s+(?:(?P<year>\d{4}),?\s+)?(?:at\s+)?)?(?P<h>\d{1,2})(?::(?P<m>\d{2}))?"
                    r"\s*(?P<ap>[ap])\.?m\b", re.IGNORECASE)
_IN = re.compile(r"try again in\s+(?:(?P<d>\d+)\s*days?)?\W*(?:(?P<h>\d+)\s*h(?:ours?|rs?)?)?\W*"
                 r"(?:(?P<m>\d+)\s*m(?:in(?:ute)?s?)?)?", re.IGNORECASE)
_EPOCH = re.compile(r"limit reached\|(\d{10})\b", re.IGNORECASE)


def modal(shown: str) -> tuple[str, str]:
    """(kind, key) of the modal at the bottom of the screen: ("model-switch", "2"), ("blocking", ""), or ("", "")."""
    if MODEL_SWITCH.search(shown or ""):
        keep = KEEP_OPTION.search(shown)
        return "model-switch", keep.group(1) if keep else "2"
    if OWNER_PROMPT.search(shown or ""):
        return "owner", ""
    if BLOCKING.search(shown or ""):
        return "blocking", ""
    return "", ""


def reset_at(shown: str, now: float | None = None, *, fresh: bool = False) -> float | None:
    """When the last quota wall on `shown` says the account comes back (epoch), or None when it does not say.
    A clock time without a date is the occurrence nearest to `now` (it may be past: the wall is stale), or, `fresh`
    (the wall just appeared), the next one."""
    now = time.time() if now is None else now
    walls = list(LIMITED.finditer(shown or ""))
    if not walls:
        return None
    base = datetime.fromtimestamp(now)
    for wall in reversed(walls):             # the last wall that says when; «/usage-credits» follows Claude's
        if epoch := _EPOCH.search(shown[max(0, wall.start() - 40):wall.end() + 20]):
            return float(epoch.group(1))
        text = " ".join(shown[wall.start():wall.start() + 500].split())
        if (rel := _IN.search(text)) and any(rel.group(k) for k in "dhm"):
            return now + timedelta(days=int(rel.group("d") or 0), hours=int(rel.group("h") or 0),
                                   minutes=int(rel.group("m") or 0)).total_seconds()
        if clock := _CLOCK.search(text):
            break
    else:
        return None
    hour = int(clock.group("h")) % 12 + (12 if clock.group("ap").lower() == "p" else 0)
    minute = int(clock.group("m") or 0)
    if hour > 23 or minute > 59:
        return None
    if clock.group("mon"):
        month = _MONTHS.get(clock.group("mon").lower())
        if not month:
            return None
        years = [int(clock.group("year"))] if clock.group("year") else [base.year - 1, base.year, base.year + 1]
        try:
            options = [datetime(y, month, int(clock.group("day")), hour, minute) for y in years]
        except ValueError:
            return None
    else:
        day = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        options = [day + timedelta(days=d) for d in (-1, 0, 1)]
    stamps = [o.timestamp() for o in options]
    if fresh:
        ahead = [s for s in stamps if s > now]
        return min(ahead) if ahead else max(stamps)
    return min(stamps, key=lambda s: abs(s - now))


def limited(shown: str, now: float | None = None, *, fresh: bool = False) -> tuple[bool, float | None]:
    """(the screen shows a quota wall the agent is behind now, when it comes back). A wall whose reset time has passed
    is stale: the account came back and the text just stayed on the screen."""
    if not LIMITED.search(shown or ""):
        return False, None
    now = time.time() if now is None else now
    until = reset_at(shown, now, fresh=fresh)
    if until is not None and until <= now and not fresh:
        return False, until
    return True, until


def clock(epoch: float | None) -> str:
    """«16:32», or «30/10 16:32» when it is not today."""
    if epoch is None:
        return ""
    when = datetime.fromtimestamp(epoch)
    return when.strftime("%H:%M" if when.date() == datetime.now().date() else "%d/%m %H:%M")


# ------------------------------------------------------------------ notices waiting for an agent to come back

HELD = ".planning/notices-held.json"
HELD_FOR_DAYS = 3                        # a notice nobody could deliver in three days is dropped (and said so)


def held(rdir: Path) -> list[dict]:
    try:
        data = json.loads((Path(rdir) / HELD).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return []
    return [n for n in data.get("notices", []) if isinstance(n, dict) and n.get("text")] if isinstance(data, dict) else []


def _save(rdir: Path, notices: list[dict]) -> None:
    target = Path(rdir) / HELD
    if not notices:
        target.unlink(missing_ok=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"notices": notices}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def hold(rdir: Path, text: str, due: float, why: str) -> None:
    """Keep `text` to be delivered at `due`; the same text held again keeps its place and only moves its time."""
    notices = held(rdir)
    for notice in notices:
        if notice["text"] == text:
            notice.update(due=due, why=why, tries=int(notice.get("tries", 0)) + 1)
            break
    else:
        notices.append({"text": text, "due": due, "why": why, "since": time.time(), "tries": 0})
    _save(rdir, notices)


def drop(rdir: Path, texts: list[str]) -> None:
    _save(rdir, [n for n in held(rdir) if n["text"] not in set(texts)])
