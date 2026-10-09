---
name: no-ai-tell
description: Finds and fixes "AI tells" in Korean text (patterns that make a reader think "this is GPT"). Use when asked "AI 티 나?", "자연스럽게 고쳐줘", "사람이 쓴 것처럼", or as a last check after finishing any Korean text that will be published or sent (marketplace listings, client replies, e-mail, cover letters, blog and social posts).
---

# No AI tell (Korean)

Based on the no-ai-tell skill by 에이미 (@ai_me____), published with an attribution requirement, and on Wikipedia's WikiProject AI Cleanup page "Signs of AI writing" (en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), regrouped for general writing with Korean translationese signals added.

> If the session already has stricter local rules for the same job (a CLAUDE.md, project memory, a team style file), those win. This skill fills gaps only.

Two jobs: **find** AI tells in text that is already written, and **prevent** them when writing new text.

The goal is not to pass an AI detector. The goal is that a reader does not decide in three seconds that a machine wrote it and stop trusting the sender.

**Machine check.** The grade A signals that a regex can catch are in the `korean_ai_tell` package of this repo. Run `ai-tell draft.md` before you report; if you add a signal here that a regex can catch, add it to `korean_ai_tell/rules.py` too, with a test.

---

## Register

- Match the other person's register (~요 / ~습니다 / 반말). If there is nothing to match, use plain ~요체 ("보내 드렸어요", "금요일까지 가능해요").
- No over-politeness ("~드리고자 합니다") and no extra friendliness (emoji, "ㅎㅎ") unless the other person used it first.
- Facts and numbers only from what the user gave you. Anything missing becomes `[확인 필요: …]`.
- A Korean text that must mirror an English original sentence by sentence (a translation) is out of scope: do not restyle it.

---

## Modes

| The user says | Mode |
|---|---|
| "이거 AI 같아?", "검사해줘", "티 나?" | **A. Diagnose** |
| "AI 표현 빼줘", "자연스럽게 다듬어줘", "사람처럼 고쳐줘" | **A. Diagnose, then B. Fix** |
| "이 주제로 글 써줘" for text that will be published | Write with **C. Writing rules**, then run **A** on your own draft |

When you finish a draft, run A once even if nobody asked. Report only if something was found.

---

## Judging rules: read first

**One signal is not a verdict.** People also use a dash or a list of three. Wikipedia says the same: no single sign proves AI writing. Say "reads as AI" only when **3 or more signals from different categories** show up.

**Do not over-remove.** Stripping every signal makes the text flat, and flatness is a stronger tell. Priority:

1. Grade **A**: remove even one.
2. Grade **B**: act only when 3 or more cluster in one text.
3. Grade **C**: leave it if it fits.

**Swapping words is not a fix.** Changing "중요합니다" to "핵심입니다" moves the tell. Rewrite the whole sentence or delete it.

---

## A. Diagnose

Scan with the signal table below. Output:

```
판정: AI 티 남 / 애매함 / 사람 글로 읽힘
근거: (how many signals, from how many categories)

[강한 신호]
- "exact quote" → which signal → how to fix it

[누적 신호]  (only when 3 or more)
- (same format)

[비어 있는 것]  (the "missing" check, section 8)
- concrete numbers, dates, names: yes/no
- something only the writer could know: yes/no
- a claim that could be wrong (a real opinion): yes/no
```

At most **7 points**, strong signals first. If one type repeats, group it ("이 유형이 반복돼요"). Do not hand back a rewritten text in this mode. Suggest; the user decides.

## B. Fix

- **Rewrite whole sentences**, not single words.
- **Vary length.** Mix short and long sentences.
- **Add concrete detail**: numbers, dates, real cases. Facts you were not given become `[확인 필요: 실제 수치]`.
- Show before and after side by side. Do not return only a new text.

## C. Writing rules

- The first sentence is the conclusion or a concrete scene. Never "~에 대해 알아보겠습니다".
- "~하는 것이 중요합니다", "~할 필요가 있습니다": at most once per text.
- "단순히 A가 아니라 B입니다": at most once per text.
- Three adjectives in a row: at most once per text.
- Do not end a paragraph by adding meaning ("~를 보여줍니다", "~를 시사합니다").
- No unsourced "많은 전문가들은", "연구에 따르면". Add who, where and when, or drop the sentence.
- No chatbot leftovers ("도움이 되셨길 바랍니다", "더 궁금한 점 있으면").
- No emoji on every heading.
- **Each section gets one** number, date, tool name or real event.

---

## Platform checks

| Platform | Watch for |
|---|---|
| Freelance marketplace listing or reply | Ad tone ("압도적인", "혁신적인"), unsupported "다수의 프로젝트 경험". Write the real job, tool and time span |
| Instagram caption | Markdown leftovers (`**`, `##`), too many emoji, first two lines that only announce |
| Blog | Headings all the same length and shape, paragraphs all the same length |
| Video script | Read it aloud: translationese shows up when spoken |
| Slides, PDF handouts | Template headings: "도전과제", "향후 전망", "마무리하며" |

---

## Final check

- No grade A signal left
- Sentence lengths still vary after the fix
- The user's own sentences were not changed without asking
- No invented numbers or cases
- The text did not go stiff from removing everything (the most common failure)

---

# Signal table

Grades: **A** remove even one · **B** only when 3+ cluster · **C** leave it if it fits. `regex` = the CLI catches it (rule id in brackets).

## 1. Tone and openings

| Grade | Signal | Example |
|---|---|---|
| A | Guide-style intro `regex` [ko-guide-intro] | "~에 대해 알아보겠습니다", "~를 살펴보겠습니다", "지금부터 하나씩 짚어볼게요" |
| A | Reaction opener `regex` [ko-reaction] | "물론이죠!", "좋은 질문이에요", "훌륭한 접근입니다" |
| A | Chatbot leftovers `regex` [ko-leftover] | "도움이 되셨길 바랍니다", "더 궁금한 점 있으면 말씀해주세요", "필요하면 수정해드릴게요" |
| A | Letter phrases in a post | "이 글이 잘 닿았으면 좋겠습니다" in a blog or article body |
| A | Knowledge cutoff, disclaimer `regex` [ko-disclaimer] | "제가 아는 한", "2024년 기준으로는", "정확한 건 공식 홈페이지에서 확인하세요" out of nowhere |
| A | Placeholder left in `regex` [ko-placeholder] | `[여기에 입력]`, `[이름]`, `(예시를 넣으세요)` |
| B | Greeting as the first line | Body starts with "안녕하세요, OOO입니다" |

## 2. Inflated meaning (the strongest tell for Wikipedia editors)

| Grade | Signal | Example |
|---|---|---|
| A | Importance inflation `regex` [ko-inflate] | "~의 핵심입니다", "빼놓을 수 없는", "중요한 이정표", "패러다임의 전환", "새로운 지평을 열었습니다" |
| A | Repeated "must" `regex` [ko-must-repeat] | "~하는 것이 중요합니다", "~할 필요가 있습니다", "~해야 합니다" three or more times |
| A | Ad tone `regex` [ko-promo] | "혁신적인", "압도적인", "놓칠 수 없는", "매력적인", "아름답게 자리 잡은" |
| A | Added commentary `regex` [ko-commentary] | After a fact: "~를 보여줍니다", "~를 시사합니다", "~라는 점에서 의미가 있습니다" (translated English -ing clauses) |
| B | Lecturing aside `regex` [ko-lecture] | "여기서 짚고 넘어갈 점은", "간과해서는 안 되는 것은" |

## 3. Sentence habits

| Grade | Signal | Example |
|---|---|---|
| A | Negation pair `regex` [ko-negation-pair] | "단순히 A가 아니라 B입니다", "A뿐만 아니라 B도", "A도 아니고 B도 아닌, 그저 C" (once per text at most) |
| A | Dash as a sentence separator `regex` [ko-dash] | —, –, " - " between clauses. Use a comma, period or brackets |
| A | Ordinal list `regex` [ko-ordinal] | "첫째, 둘째, 셋째", "첫 번째로". Say the first item and join the next with "그리고" |
| B | Always three | "빠르고, 정확하고, 효율적으로" / headings or reasons always come in threes |
| B | Closing summary `regex` [ko-summary] | "결론적으로", "종합하면", "정리하자면" followed by what was already said |
| B | Fake range `regex` [ko-fake-range] | "기초부터 심화까지", "A부터 Z까지", "전략 수립에서 실행 지원에 이르기까지" |
| B | Connective overuse `regex` [ko-connective] | "또한", "게다가", "더 나아가", "뿐만 아니라" in every paragraph |

## 4. Authority without a source

| Grade | Signal | Example |
|---|---|---|
| A | Unsourced citation `regex` [ko-unsourced] | "많은 전문가들은", "연구에 따르면", "업계에서는", "~라고 알려져 있습니다", "일각에서는" |
| A | Invented source | A link, paper, ISBN or DOI that does not exist; "한 연구" never named |
| B | Anonymous crowd | "사람들은 흔히", "대부분의 사용자들이" with nothing behind it |

## 5. Korean translationese (not in the Wikipedia list; the strongest Korean tell)

| Grade | Signal | Example → fix |
|---|---|---|
| A | Inanimate subject | "이 기능은 편의를 제공합니다" → "이 기능 쓰면 편해요" |
| A | "당신" `regex` [ko-you] | Korean text rarely uses it. Drop it |
| B | "~에 있어서" `regex` [ko-eseo] | "업무에 있어서" → "업무에서" |
| B | "~를 통해" overuse `regex` [ko-through] | "AI를 통해 효율을 높일 수 있습니다" → "AI로 빨라져요" |
| B | Passive overuse `regex` [ko-passive] | "~되어집니다", "~라고 여겨집니다", "~것으로 보입니다" |
| B | Plural "들" | "사용자들은", "많은 사람들이" → "사용자는", "많은 사람이" |
| B | "것" noun phrase `regex` [ko-geot] | "~하는 것이 가능합니다" → "~할 수 있어요" |
| B | Over-polite forms `regex` [ko-over-polite] | "말씀드리고자 합니다", "안내드립니다" mixed in |

## 6. Formatting

| Grade | Signal |
|---|---|
| A | Markdown leftovers in a caption or blog: `**bold**`, `## heading`, `---` |
| A | An emoji on every heading |
| B | Bold everywhere |
| B | Bullets where prose belongs |
| B | Title Case English headings |
| C | Curly and straight quotes mixed in one text |

## 7. Structure

| Grade | Signal |
|---|---|
| A | Template headings `regex` [ko-section-title]: "도전과제", "향후 전망", "결론", "마무리하며" |
| B | Intro, body, conclusion of equal length |
| B | The same point said in the intro, body and conclusion |
| B | Every sentence about the same length (mix in at least one very short sentence) |

## 8. What is missing (removing words cannot fix this)

If these fail, the text reads as AI however well it is polished. Judge each as yes/no.

- **Concrete**: no numbers, dates, product or tool names, proper nouns
- **Experience**: no sentence only someone who did it could write ("예를 들어 마케팅 담당자라면" is a made-up example, it does not count)
- **Position**: no claim that could turn out wrong
- **Failure**: no limits, downsides or cases where it does not work
- **Voice**: no view that could only come from this writer's job or history

---

## Notes

- No signal **alone** proves AI writing. Models learned from human text.
- Newer models are tuned to avoid the classic tells such as the em dash. **Formatting signals are getting weaker; section 8 matters more every year.**
- Do not use this to accuse someone else of using AI. False positives hurt people. This skill is for checking **your own** drafts.
