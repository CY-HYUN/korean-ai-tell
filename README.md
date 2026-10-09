# korean-ai-tell

A small Python library and CLI that flags "AI tells" in Korean text: the phrases that make a Korean reader think "GPT wrote this" within three seconds. An English rule set runs as a second mode.

Each finding has a rule id, a severity (`BLOCK` or `WARN`), the matched phrase and a one-line fix hint. The CLI exits with code 1 when any finding is `BLOCK`, so it can sit in a pre-commit hook or a CI step. The repo also ships a Claude Code skill (`skill/no-ai-tell/`) with the full Korean pattern table, so an agent can diagnose and rewrite drafts, not only flag them.

**Who it is for:** Korean freelancers and teams who publish text drafted with an LLM (marketplace listings, client replies, blog posts, cover letters) and want a fast, explainable check before it goes out.

No dependencies. Python 3.9+.

## Quickstart

```bash
pip install .
ai-tell examples/before.md
```

Or without installing: `python -m korean_ai_tell examples/before.md`.

## Example

`examples/before.md` (a typical LLM-drafted service listing):

```text
안녕하세요! 오늘은 데이터 정리 서비스에 대해 알아보겠습니다.

엑셀 정리는 단순히 표를 고치는 일이 아니라 업무 효율의 핵심입니다. 저희는 혁신적인 자동화 도구를 통해 작업 시간을 줄여 드립니다.

연구에 따르면 데이터 정리에 업무 시간의 30%가 쓰인다고 합니다. 이는 자동화의 필요성을 보여줍니다.

더 궁금한 점 있으시면 언제든 말씀해 주세요. 도움이 되셨길 바랍니다!
```

Output (exit code 1):

```text
examples/before.md: lang=ko 7 finding(s)
  examples/before.md:1: BLOCK ko-guide-intro "에 대해 알아보겠" -> 첫 문장에 결론이나 구체적인 장면을 쓴다
  examples/before.md:3: BLOCK ko-inflate "핵심입니다" -> 중요하다고 말하지 말고 무엇이 달라졌는지 숫자나 사례로 보여 준다
  examples/before.md:3: BLOCK ko-promo "혁신적인" -> 홍보 형용사 대신 실제로 한 작업, 도구, 기간을 쓴다
  examples/before.md:3: BLOCK ko-negation-pair "단순히 표를 고치는 일이 아니라" -> 'A가 아니라 B' 틀을 풀고 B만 말한다
  examples/before.md:5: BLOCK ko-commentary "을 보여줍니다" -> 사실 뒤에 의미를 얹지 말고 사실에서 멈춘다
  examples/before.md:5: BLOCK ko-unsourced "연구에 따르면" -> 누가, 어디서, 언제 말했는지 붙이거나 문장을 뺀다
  examples/before.md:7: BLOCK ko-leftover "더 궁금한 점 있으시면" -> 챗봇식 맺음말은 지운다. 할 말이 끝났으면 거기서 끝낸다
```

`examples/after.md`, rewritten by a person with concrete detail instead of claims:

```text
엑셀 파일 정리해 드려요. 중복 행 지우기, 날짜 형식 맞추기, 시트 합치기까지 해요.

지난달에 받은 거래처 목록은 4,200행이었어요. 파이썬 스크립트로 정리해서 하루 만에 보내 드렸어요.

파일을 먼저 보내 주시면 걸리는 시간과 가격을 알려 드릴게요.
```

Output: `examples/after.md: lang=ko 0 finding(s)`, exit code 0.

## Usage

```bash
ai-tell draft.md                       # language detected per file
ai-tell --lang en --channel chat reply.txt
cat draft.md | ai-tell -               # read stdin
ai-tell --channel listing --baseline my_baseline.json listing.md
```

As a library:

```python
from korean_ai_tell import check

for f in check("물론이죠! 도움이 되셨길 바랍니다.", lang="ko"):
    print(f.severity, f.rule_id, f.match, f.hint)
```

As a pre-commit hook (Markdown files):

```yaml
repos:
  - repo: <this repo's URL>
    rev: v0.1.0
    hooks:
      - id: ai-tell
```

## Rules

**Korean, grade A (`BLOCK`, one hit is enough):** guide-style intro (`~에 대해 알아보겠습니다`), reaction opener (`물론이죠`, `좋은 질문`), chatbot leftovers (`도움이 되셨길`, `더 궁금한 점 있으시면`), disclaimers, placeholders (`[이름]`), importance inflation (`핵심입니다`, `패러다임의 전환`), ad tone (`혁신적인`, `압도적인`), added commentary (`~를 보여줍니다`), negation pair (`단순히 A가 아니라`), ordinal lists (`첫째, 둘째`), dash separators, unsourced authority (`연구에 따르면`), `당신`, template headings (`마무리하며`), and "must" phrases used 3+ times.

**Korean, grade B (`WARN`, only when 3+ different kinds appear in one text):** `~에 있어서`, `~를 통해`, passive overuse, closing summaries (`결론적으로`), connectives (`또한`, `게다가`), `것이 가능합니다`, over-polite forms (`안내드립니다`), fake ranges (`기초부터 심화까지`), lecturing asides. One of these alone is normal Korean, so they are reported only in a cluster.

**English:** dashes, label openers (`Summary:`, `Heads up,`), formal connectors (`Moreover`), LLM vocabulary (`delve`, `leverage`, `seamless`), ordinal lists, arrows, pleasantries, agreeing as the first words, moral closers, stock frames (`short answer`, `here's the thing`), one-word acknowledgements (`noted.`), acknowledgement or count openers (`Understood.`, `Three things...`), sentences over 38 words, stacked hedges and fillers.

Code blocks, inline code, URLs and table rows are ignored. Each rule reports its first match.

## Baseline file

Length budgets and "phrases this writer never uses" differ per person, so they live in a JSON file instead of the code. `baseline.example.json` is a neutral starting point: copy it, then fill it from text you really send (your own word counts per channel, the phrases a model adds that you never write). Keys you leave out keep the built-in defaults. A length check runs only when you pass `--channel`.

## Claude Code skill

Copy `skill/no-ai-tell/` to `~/.claude/skills/no-ai-tell/`. The skill has three modes (diagnose, fix, write) and the full signal table, including the semantic signals a regex cannot judge, such as "no concrete number anywhere" or "no claim that could be wrong". Its rule ids match the CLI's.

## Tests

```bash
python tests/test_rules.py        # 13/13 passed, no dependencies
python -m pytest -q               # same tests, if pytest is installed
```

Every rule has a firing case, and human-written samples (a plain client message, a Markdown bullet list, casual spoken English, social assent like "sounds good") must stay quiet.

## Limits

- Regex only. It finds surface patterns. It cannot tell whether a text has real experience, numbers or an opinion in it; the skill's section 8 covers that by hand.
- A clean result does not mean a person wrote the text, and a hit does not prove a model did. People write `또한` and `연구에 따르면` too. Use it on your own drafts, not to accuse anyone.
- Grade B and the English rules will have false alarms on formal or academic writing. Treat `WARN` as a prompt to reread, not a verdict.
- Line numbers point at the first occurrence of the matched phrase.

## Credits

The Korean signal table is based on the no-ai-tell skill by 에이미 (@ai_me____), shared on condition of attribution, and on Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (WikiProject AI Cleanup).

## 한국어 설명

LLM으로 초안을 쓴 한국어 글에서 "AI 티"를 찾아 주는 작은 파이썬 도구입니다. 크몽 같은 플랫폼의 상품 설명, 고객 답장, 블로그 글, 자기소개서를 내보내기 전에 돌려 보는 용도예요.

걸린 곳마다 규칙 이름, 심각도(`BLOCK` 또는 `WARN`), 걸린 문구, 고치는 방법 한 줄을 보여 줍니다. `BLOCK`이 하나라도 있으면 종료 코드 1을 돌려주니 pre-commit 훅이나 CI에 그대로 넣을 수 있어요.

```bash
pip install .
ai-tell 초안.md
```

- **A등급(BLOCK)**: 하나만 있어도 고칩니다. "~에 대해 알아보겠습니다", "물론이죠", "도움이 되셨길 바랍니다", "혁신적인", "연구에 따르면", "단순히 A가 아니라" 같은 표현이에요.
- **B등급(WARN)**: "~에 있어서", "~를 통해", "또한" 같은 표현은 사람도 자주 씁니다. 그래서 한 글에 서로 다른 종류가 3개 이상 몰릴 때만 알려 줘요.
- 코드 블록, 인라인 코드, URL, 표는 검사하지 않습니다.
- 글자 수 기준과 "나는 안 쓰는 말" 목록은 사람마다 달라서 `baseline.example.json`을 복사해 자기 글에 맞게 채워 쓰면 됩니다.

`skill/no-ai-tell/` 폴더를 `~/.claude/skills/`에 복사하면 Claude Code가 진단, 수정, 집필 세 가지 모드로 같은 기준을 씁니다. 정규식이 못 잡는 신호(구체적인 숫자나 직접 겪은 일이 없는 글)도 그 스킬의 점검표에 있어요.

주의: 정규식 검사라서 겉모양만 봅니다. 걸리지 않았다고 사람 글이라는 뜻은 아니고, 걸렸다고 AI가 썼다는 증거도 아니에요. 남의 글을 "AI로 썼죠?"라고 단정하는 데 쓰지 말고, 자기 원고 점검에 쓰세요.

## License

MIT. See `LICENSE`.
