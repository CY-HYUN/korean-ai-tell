"""Each rule fires on its case and stays quiet on human samples.

    python tests/test_rules.py      (no dependencies)
    python -m pytest -q             (if pytest is installed)
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from korean_ai_tell import BLOCK, WARN, check, lang_of, load_baseline  # noqa: E402
from korean_ai_tell.cli import main  # noqa: E402


def ids(text, lang=None, channel=None, baseline=None):
    return {f.rule_id for f in check(text, lang, channel, baseline)}


# ---------------------------------------------------------------- Korean, grade A
KO_FIRE = [
    ("이번 글에서는 크롤링에 대해 알아보겠습니다.", "ko-guide-intro"),
    ("좋은 질문이에요! 바로 정리해 드릴게요.", "ko-reaction"),
    ("자료 보내 드렸어요. 더 궁금한 점 있으시면 말씀해 주세요.", "ko-leftover"),
    ("제가 아는 한 그 기능은 유료입니다.", "ko-disclaimer"),
    ("안녕하세요, [이름]님.", "ko-placeholder"),
    ("데이터 정제가 이 작업의 핵심입니다.", "ko-inflate"),
    ("혁신적인 자동화 서비스를 소개합니다.", "ko-promo"),
    ("이 결과는 시장의 변화를 보여줍니다.", "ko-commentary"),
    ("단순히 코드가 아니라 경험을 팝니다.", "ko-negation-pair"),
    ("목록입니다.\n첫째, 빠릅니다.", "ko-ordinal"),
    ("가격은 3만 원 — 수정 2회 포함입니다.", "ko-dash"),
    ("작업은 금요일 - 늦어도 토요일 끝납니다.", "ko-dash"),
    ("연구에 따르면 이 방식이 더 빠릅니다.", "ko-unsourced"),
    ("당신의 시간을 아껴 드립니다.", "ko-you"),
    ("본문입니다.\n## 마무리하며\n", "ko-section-title"),
    ("확인하는 것이 중요합니다. 기록하는 것이 중요합니다. 공유하는 것이 중요합니다.", "ko-must-repeat"),
]
KO_QUIET = [
    "안녕하세요, 요청하신 데이터 정리는 금요일까지 드릴 수 있어요. 파일 형식만 알려 주시면 맞춰서 보낼게요.",
    "할 일:\n- 데이터 받기\n- 정리해서 보내기",  # a markdown bullet is not a dash separator
    "확인하는 것이 중요합니다. 나머지는 금요일에 보낼게요.",  # one "must" is fine
    "코드는 `a - b`로 계산해요.",  # code is not prose
]


def test_korean_rules_fire():
    for text, rid in KO_FIRE:
        got = ids(text, "ko")
        assert rid in got, (rid, text, got)
        assert all(f.severity == BLOCK for f in check(text, "ko") if f.rule_id == rid)


def test_korean_human_samples_stay_quiet():
    for text in KO_QUIET:
        assert ids(text, "ko") == set(), (text, ids(text, "ko"))


def test_korean_grade_b_needs_a_cluster():
    two = "업무에 있어서 정리가 필요해요. AI를 통해 줄였어요."
    assert ids(two, "ko") == set(), ids(two, "ko")
    three = two + " 결론적으로 빨라졌어요."
    got = check(three, "ko")
    assert {f.rule_id for f in got} == {"ko-eseo", "ko-through", "ko-summary"}, got
    assert all(f.severity == WARN for f in got)


def test_each_finding_has_match_and_hint():
    for f in check("물론이죠! 혁신적인 서비스입니다. 도움이 되셨길 바랍니다.", "ko"):
        assert f.match and f.hint, f


# ---------------------------------------------------------------- English
EN_FIRE = [
    ("Heads up, the run finished.", "ai-opener"),
    ("The pipeline uses one prompt — the reader gets two.", "emdash"),
    ("Moreover, we leverage the planner for this.", "formal-connector"),
    ("Moreover, we leverage the planner for this.", "llm-vocab"),
    ("You're right, the count was off by one.", "agreement-opener"),
    ("First, the planner. Second, the builder.", "ordinal"),
    ("the planner output → the builder input.", "arrow"),
    ("the planner reads the request and then the builder takes the plan and then the "
     "refiner looks at the result and then the scorer compares it with the ground truth "
     "and then the report writer puts all of it in one table for the team to read.", "runon"),
    ("Understood. The reading branch finished overnight.", "spoken-opener"),
    ("Three things changed since last week. First the parser.", "count-announce"),
    ("Short answer to your question. We already have one.", "stock-frame"),
    ("So the first one is the parser, the second one is the ranker.", "stock-frame"),
    ("Sounds good, let me know when it's merged.", "avoid-phrase"),
    ("Hi Sam, thanks, noted. I'll remove it by the 9th.", "ack-filler"),
    ("Noted! I'll send it tomorrow.", "ack-filler"),
]
EN_QUIET = [
    "the branch is pushed. i ran 12 of the 40 parts, 9 built.",
    "sounds good, i'll take the second ticket",  # social assent, not technical
    "TLDR: the run is green.",
    "```\nx — y\n```\nthe fence is code, the prose is clean.",
    "the robust check passed on all 12 parts.",
    "As noted above, the run failed twice.",
    "So the answer was short. Yeah.",
]


def test_english_rules_fire():
    for text, rid in EN_FIRE:
        assert rid in ids(text, "en"), (rid, text, ids(text, "en"))


def test_english_human_samples_stay_quiet():
    for text in EN_QUIET:
        assert ids(text, "en") == set(), (text, ids(text, "en"))


def test_plain_spoken_style_stays_quiet():
    spoken = "So I worked on the reading part. Yeah, mostly the dimensions. It took a while. I think it's stable now."
    assert ids(spoken, "en", "speech") == set(), ids(spoken, "en", "speech")


# ---------------------------------------------------------------- channels and baseline
LONG = " ".join(["The parser now reads every dimension on the sheet and checks it against the view."] * 6)
LETTER = " ".join(["I built an evaluation that caught a silent regression before release."] * 30)


def test_channels():
    assert "length" in ids(LONG, "en", "speech")
    assert "no-short-sentence" in ids(LONG, "en", "speech")
    assert "length" not in ids(LETTER, "en", "letter")
    assert "length" in ids(LETTER, "en", "chat")
    assert "length" not in ids(LONG, "en")  # no channel, no length check
    assert "length" in ids("\n".join(f"{i}번째 줄이에요." for i in range(12)), "ko", "listing")


def test_baseline_file_overrides_defaults():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "baseline.json"
        p.write_text(json.dumps({"_note": "x", "avoid_phrases": ["circle back"]}), encoding="utf-8")
        b = load_baseline(p)
        assert "avoid-phrase" in ids("Let's circle back on Monday.", "en", None, b)
        assert "avoid-phrase" not in ids("Sounds good, let me know.", "en", None, b)
        assert "chat" in b["channels"]  # keys the file leaves out keep their defaults


def test_example_baseline_loads():
    b = load_baseline(Path(__file__).resolve().parents[1] / "baseline.example.json")
    assert b["channels"]["chat"]["cap"] > 0 and b["avoid_phrases"]


# ---------------------------------------------------------------- language detection
def test_lang_of():
    assert lang_of("Rechecked the reply above against the files and found nothing to correct.") == "en"
    mixed = ("실행기를 `py -3`로 바꿨고 `hooks/dispatch.py`가 `hook_registry.json`을 읽어 PreToolUse 훅 11개를 "
             "한 번에 돌립니다. 결과는 https://github.com/example/repo 에 push했습니다. "
             "Stop 게이트·MCP·LoRA·RAG 같은 이름은 그대로 둡니다.")
    assert lang_of(mixed) == "ko"
    assert lang_of("결과입니다.\n\n```\nTraceback (most recent call last): File \"x.py\", line 3\n```") == "ko"


# ---------------------------------------------------------------- CLI
def _run(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(list(argv))
    return code, buf.getvalue()


def test_cli_exit_codes():
    with tempfile.TemporaryDirectory() as d:
        bad, good = Path(d) / "bad.md", Path(d) / "good.md"
        bad.write_text("안녕하세요.\n자료 보내 드렸어요. 더 궁금한 점 있으시면 말씀해 주세요.\n", encoding="utf-8")
        good.write_text(KO_QUIET[0], encoding="utf-8")
        code, out = _run(str(bad))
        assert code == 1 and "ko-leftover" in out and "bad.md:2:" in out, out
        code, out = _run(str(good))
        assert code == 0 and "0 finding(s)" in out, out


def test_examples_before_and_after():
    ex = Path(__file__).resolve().parents[1] / "examples"
    assert _run(str(ex / "before.md"))[0] == 1
    assert _run(str(ex / "after.md")) == (0, f"{ex / 'after.md'}: lang=ko 0 finding(s)\n")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}  {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
