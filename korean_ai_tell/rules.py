"""The rule tables and the checker.

Two rule sets: Korean (the main mode) and English. Each rule is a regex plus a one-line fix hint.
Only what a regex can judge without many false alarms lives here; the semantic signals (no concrete
numbers, no real experience, no opinion that could be wrong) are in the skill's checklist.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

BLOCK, WARN = "BLOCK", "WARN"


@dataclass(frozen=True)
class Finding:
    severity: str  # BLOCK or WARN
    rule_id: str
    match: str
    hint: str


# ---------------------------------------------------------------- baseline (configurable)
# Length caps per channel and the phrases a writer never uses. Measure your own from what you
# really send (see baseline.example.json); these defaults are a neutral starting point.
DEFAULT_BASELINE = {
    "channels": {
        "chat": {"cap": 60, "hard": 100},
        "speech": {"cap": 55, "hard": 80},
        "email": {"cap": 150, "hard": 220},
        "linkedin": {"cap": 80, "hard": 120},
        "letter": {"min": 250, "cap": 350, "hard": 420},
        "listing": {"lines": 10},
    },
    "avoid_phrases": ["let me know", "i hope this helps"],
    "short_sentence_words": 5,
}


def load_baseline(path: str | Path | None) -> dict:
    """DEFAULT_BASELINE, with the keys of a JSON file laid over it."""
    if path is None:
        return DEFAULT_BASELINE
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {**DEFAULT_BASELINE, **{k: v for k, v in data.items() if not k.startswith("_")}}


# ---------------------------------------------------------------- Korean, grade A (one hit is enough)
# (id, regex, hint). Grades follow the skill: A = remove even a single one.
KO_A = [
    ("ko-guide-intro", r"(에 대해|를|을)\s*(알아보겠|살펴보겠|짚어보겠|정리해\s*보겠)|지금부터\s*하나씩",
     "첫 문장에 결론이나 구체적인 장면을 쓴다"),
    ("ko-reaction", r"물론이죠|좋은 질문|훌륭한 (접근|질문)|탁월한 (질문|선택)",
     "리액션을 빼고 바로 답부터 쓴다"),
    ("ko-leftover", r"도움이 되(셨|었)(길|으면)|더 궁금한 (점|것)(이)? 있(으시|으)면|필요하(시)?면 수정해 ?드릴",
     "챗봇식 맺음말은 지운다. 할 말이 끝났으면 거기서 끝낸다"),
    ("ko-disclaimer", r"제가 아는 (한|바로는)|정확한 (건|것은|정보는) 공식",
     "확인한 사실만 쓰고, 모르면 '[확인 필요]'로 남긴다"),
    ("ko-placeholder", r"\[(여기에 입력|이름|회사명)\]|\((예시를|내용을) 넣",
     "자리표시자를 실제 내용으로 채운다"),
    ("ko-inflate", r"핵심입니다|빼놓을 수 없는|중요한 이정표|패러다임의 전환|새로운 지평",
     "중요하다고 말하지 말고 무엇이 달라졌는지 숫자나 사례로 보여 준다"),
    ("ko-promo", r"혁신적인|압도적인|놓칠 수 없는|매력적인",
     "홍보 형용사 대신 실제로 한 작업, 도구, 기간을 쓴다"),
    ("ko-commentary", r"(를|을) (보여줍니다|시사합니다)|라는 점에서 의미가 있습니다",
     "사실 뒤에 의미를 얹지 말고 사실에서 멈춘다"),
    ("ko-negation-pair", r"단순히 [^.\n]{0,20}아니라|뿐만 아니라",
     "'A가 아니라 B' 틀을 풀고 B만 말한다"),
    ("ko-ordinal", r"(^|\n)\s*(첫째|둘째|셋째|첫 번째로)",
     "첫 항목을 말하고 '그리고'로 잇는다"),
    # a dash between words on one line; a markdown bullet ("\n- 항목") is not a separator
    ("ko-dash", r"[–—]|(?<=\S)[ \t]-[ \t]",
     "대시 대신 쉼표, 마침표, 괄호를 쓴다"),
    ("ko-unsourced", r"많은 전문가들은|연구에 따르면|업계에서는|라고 알려져 있습니다|일각에서는",
     "누가, 어디서, 언제 말했는지 붙이거나 문장을 뺀다"),
    ("ko-you", r"당신(은|이|의|에게)",
     "'당신'은 빼거나 생략한다"),
    ("ko-section-title", r"(^|\n)\s*#*\s*(도전과제|향후 전망|결론|마무리하며)\s*$",
     "정형 소제목 대신 그 절의 내용을 담은 제목을 쓴다"),
]
KO_A_RE = [(rid, re.compile(rx, re.M), hint) for rid, rx, hint in KO_A]
KO_MUST_RE = re.compile(r"하는 것이 중요합니다|할 필요가 있습니다|해야 합니다")  # grade A at 3+ uses

# ---------------------------------------------------------------- Korean, grade B (only when 3+ cluster)
KO_B = [
    ("ko-eseo", r"에 있어서", "'~에 있어서'를 '~에서'로"),
    ("ko-through", r"(을|를) 통해", "'~를 통해'를 '~로'로"),
    ("ko-passive", r"되어집니다|여겨집니다|것으로 보입니다", "피동을 능동으로"),
    ("ko-summary", r"결론적으로|종합하면|정리하자면", "앞에서 한 말을 다시 요약하지 않는다"),
    ("ko-connective", r"또한|게다가|더 나아가", "접속부사를 빼고 그냥 잇는다"),
    ("ko-geot", r"것이 가능합니다", "'~하는 것이 가능합니다'를 '~할 수 있어요'로"),
    ("ko-over-polite", r"말씀드리고자|안내드립니다|드리고자 합니다", "과공손체를 담백한 ~요체로"),
    ("ko-fake-range", r"부터 심화까지|부터 Z까지|에 이르기까지", "범위 대신 실제로 하는 일을 쓴다"),
    ("ko-lecture", r"짚고 넘어갈|간과해서는 안", "훈수 문장을 빼고 내용만 쓴다"),
]
KO_B_RE = [(rid, re.compile(rx), hint) for rid, rx, hint in KO_B]
KO_B_CLUSTER = 3

# ---------------------------------------------------------------- English
EN_RULES = [  # (id, severity, regex, hint); searched once over the prose
    ("emdash", BLOCK, r"[–—]", "Use a comma, a period or a new sentence instead of a dash."),
    ("ai-opener", BLOCK,
     r"(?im)^\s*(?:>\s*)?(quick one\b|heads?[- ]up[,:]|just a quick|hope (this|you're)|i hope this (finds|helps)|"
     r"great question|absolutely[,!]|(?:the )?(?:short|long) version[,:]|long story short|"
     r"(?:my |the |in )?(?:conclusions?|summary|verdict|bottom line|short answer|key points?|takeaways?|"
     r"answer|results?|in short)\s*[:：])",
     "Open with the point itself, not a label or a greeting."),
    ("formal-connector", BLOCK, r"(?m)\b(Moreover|Furthermore|Additionally|Consequently|Nevertheless|Nonetheless)\b[,;]?",
     "Drop the connector and just continue."),
    ("llm-vocab", BLOCK,
     r"(?i)\b(delve|leverage[sd]?|utiliz\w+|seamless\w*|holistic\w*|streamlin\w+|cutting[- ]edge|game[- ]chang\w+|"
     r"robust(?:ness)?\b(?! (check|test))|comprehensive\w*|pivotal|underscor\w+|showcas\w+|paradigm)",
     "Use the plain word (use, full, smooth, show)."),
    ("ordinal", BLOCK, r"(?m)^\s*(?:>\s*)?(First|Second|Third|Firstly|Secondly)\s*[,:]",
     "Say the first item, then join the next with 'and'."),
    ("not-only", WARN, r"(?i)\bnot only\b[^.]{0,80}\bbut\b", "Drop the 'not only... but' frame and say the second half."),
    ("arrow", BLOCK, r"→|=>|-->", "Write the word ('then', 'becomes', 'leads to')."),
    ("pleasantry", WARN, r"(?i)\b(certainly|of course|happy to \w+|glad to \w+|no problem at all|feel free to)\b",
     "Cut the politeness tic and go straight to the content."),
    # anchored to the start: conceding first turns a judgement into deference; mid-text it reads as reasoning
    ("agreement-opener", BLOCK,
     r"(?i)\A\W{0,3}(you'?re (so )?right|that'?s (quite |exactly )?right|you'?re correct|yes,? you'?re|correct,|"
     r"good (point|catch)|fair (enough|point)|agreed\b|i agree\b)",
     "State the fact first and fold the agreement into it."),
    ("moral-closer", WARN,
     r"(?i)(so the (lesson|takeaway|key point) (is|here)|this (shows|means|proves) (that )?we|"
     r"the (lesson|takeaway) (is|here)|in (summary|conclusion)|the bottom line is)",
     "End on the finding and let the reader draw the lesson."),
    ("stock-frame", BLOCK,
     r"(?i)\b(short answer|short version|long story short|the (first|second|third) one is|one more thing|"
     r"honest reason|here's the thing)\b",
     "Remove the frame and say the thing."),
    # a one-word acknowledgement standing as its own clause ("thanks, noted."), not "as noted above"
    ("ack-filler", BLOCK, r"(?i)(?:^|[.!?]\s+|,\s*)(?:duly\s+)?noted\s*[.!,]",
     "Replace 'noted' with what you will do and when."),
]
EN_RULES_RE = [(rid, sev, re.compile(rx), hint) for rid, sev, rx, hint in EN_RULES]
# checked on the first sentence only
SPOKEN_OPENER_RE = re.compile(
    r"^\W*(understood|great question|good question|thanks? (you )?for (asking|the question)|absolutely|certainly|"
    r"definitely|of course|sure thing|that's a (great|good) question|happy to)\b", re.I)
COUNT_ANNOUNCE_RE = re.compile(r"^\W*(two|three|four|five|a few) (things|points|reasons|parts|steps|aspects)\b", re.I)
FILLER_RE = re.compile(r"(?i)\b(just|really|basically|actually|simply|essentially|literally)\b")
HEDGE_RE = re.compile(r"(?i)\b(maybe|perhaps|possibly|i think|i guess|kind of|sort of)\b")
RUNON_WORDS = 38

HANGUL = re.compile(r"[가-힣]")
LATIN = re.compile(r"[A-Za-z]")


def lang_of(text: str) -> str:
    """'ko' when Hangul syllables are at least a third of the Latin letters, so code and names in a Korean
    text do not flip it to English."""
    text = strip_nonprose(text)
    return "ko" if len(HANGUL.findall(text)) >= len(LATIN.findall(text)) / 3 else "en"


def strip_nonprose(text: str) -> str:
    """Drop code, URLs, link-only lines, emphasis markers, short HTML tags and table rows."""
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"(?m)^\s*!?\[[^\]]*\]\([^)]*\)\s*$", " ", text)
    text = re.sub(r"\*\*?|__", "", text)  # "...point.**" would hide the sentence end from the splitter
    text = re.sub(r"<[^>\n]{1,40}>", "", text)
    return "\n".join(line for line in text.split("\n") if not line.lstrip().startswith("|"))


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?。])\s+|\n+", text) if s.strip()]


def _check_en(prose: str, channel: str | None, baseline: dict) -> list[Finding]:
    out = []
    for rid, sev, rx, hint in EN_RULES_RE:
        m = rx.search(prose)
        if m:
            out.append(Finding(sev, rid, m.group(0).strip()[:60], hint))
    first = sentences(prose)[:1]
    if first and SPOKEN_OPENER_RE.search(first[0]):
        out.append(Finding(BLOCK, "spoken-opener", first[0][:50], "Start with the answer, not an acknowledgement."))
    if first and COUNT_ANNOUNCE_RE.search(first[0]):
        out.append(Finding(BLOCK, "count-announce", first[0][:50], "Skip the count and give the first point."))
    fillers = sorted({m.lower() for m in FILLER_RE.findall(prose)})
    if len(FILLER_RE.findall(prose)) >= 2:
        out.append(Finding(WARN, "filler", ", ".join(fillers[:4]), "Cut the filler adverbs."))
    for phrase in baseline.get("avoid_phrases", []):
        m = re.search(r"\b" + re.escape(phrase) + r"\b", prose, re.I)
        if m:
            out.append(Finding(WARN, "avoid-phrase", m.group(0), "Not in this writer's baseline; say it their way."))
    for sent in re.split(r"(?<=[.!?])\s+|\n\s*(?=[-*#>]|\d+\.\s)", prose):
        words = sent.split()
        if len(words) > RUNON_WORDS:
            out.append(Finding(BLOCK, "runon", " ".join(words[:9]) + "...", f"{len(words)} words; split it."))
        if len(HEDGE_RE.findall(sent)) >= 2:
            out.append(Finding(WARN, "hedge-stack", sent.strip()[:60], "Keep one hedge or none."))
    sents = sentences(prose)
    short = baseline.get("short_sentence_words", 5)
    if channel in ("speech", "chat") and len(sents) >= 3 and not any(len(s.split()) <= short for s in sents):
        out.append(Finding(WARN, "no-short-sentence", "", f"Mix in one sentence of {short} words or fewer."))
    return out


def _check_ko(prose: str) -> list[Finding]:
    out = []
    for rid, rx, hint in KO_A_RE:
        m = rx.search(prose)
        if m:
            out.append(Finding(BLOCK, rid, m.group(0).strip()[:40], hint))
    must = KO_MUST_RE.findall(prose)
    if len(must) >= 3:
        out.append(Finding(BLOCK, "ko-must-repeat", f"{len(must)}x {must[0]}", "당위 표현은 글 전체에서 한 번까지"))
    b = [(rid, m.group(0), hint) for rid, rx, hint in KO_B_RE if (m := rx.search(prose))]
    if len(b) >= KO_B_CLUSTER:  # grade B counts only when several kinds pile up in one text
        out += [Finding(WARN, rid, match, hint) for rid, match, hint in b]
    return out


def check(text: str, lang: str | None = None, channel: str | None = None, baseline: dict | None = None) -> list[Finding]:
    """All findings for one text. lang: 'ko', 'en' or None (detect). channel: a key of baseline['channels']
    or None (no length check)."""
    baseline = baseline or DEFAULT_BASELINE
    lang = lang or lang_of(text)
    prose = strip_nonprose(text)
    out = _check_ko(prose) if lang == "ko" else _check_en(prose, channel, baseline)
    if channel is None:
        return out
    spec = baseline["channels"].get(channel)
    if spec is None:
        raise ValueError(f"unknown channel {channel!r}; known: {', '.join(baseline['channels'])}")
    words = len(prose.split())
    if "lines" in spec:
        n = len([line for line in prose.splitlines() if line.strip()])
        if n > spec["lines"]:
            out.append(Finding(WARN, "length", f"{n} lines", f"Over {spec['lines']} lines for {channel}; cut."))
    elif spec.get("cap") and words > spec["cap"]:
        sev = BLOCK if words > spec.get("hard", 10**9) else WARN
        out.append(Finding(sev, "length", f"{words} words", f"Over {spec['cap']} words for {channel}; cut."))
    elif spec.get("min") and words < spec["min"]:
        out.append(Finding(WARN, "length", f"{words} words", f"Under {spec['min']} words for {channel}."))
    return out
