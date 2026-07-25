---
name: study-session
description: Teach a topic by asking rather than telling - one question at a time, checking what the user can already reconstruct, exposing the gap, and only then filling it. Use when the user says 공부하자, 가르쳐줘, 설명해줘 with intent to learn rather than look up, 이해했는지 확인해줘, 퀴즈 내줘, 파인만 기법, or wants to understand a topic well enough to use it. Do NOT use it for a quick factual lookup the user just needs answered, and do NOT let the questioning become a quiz the user cannot leave.
---

# study-session — Learn by reconstructing, not by reading

## Why

An explanation that is read and agreed with is forgotten. The same content
recovered by the learner under a question is not. The whole method here is to
move the work of assembling the answer from the agent to the user, and to spend
the agent's effort on finding exactly where their model breaks.

This is also the harness's own goal stated as a workflow: the point is the user
understanding, not the agent producing an answer.

## When not to run this

If the user needs a fact and asked for it plainly, answer it. Turning a lookup
into a lesson is a way of not being useful. Say what you know, and offer a
session only if the topic is worth holding.

Stop when the user says so, and stop without arguing. A session they cannot
leave teaches them to avoid the skill.

## Procedure

1. **Search first.** Read `vault/index.md` and the relevant `wiki/` notes
   before asking anything. A session that ignores what the user already wrote
   makes them repeat themselves and teaches nothing.
2. **Ask what they can already reconstruct**, starting from what the notes
   suggest they know. One question at a time. Not a list - a list gets answered
   shallowly and hides which part failed.
3. **Follow the answer, not the syllabus.** The next question comes from what
   their answer revealed. When an answer is right, go one level deeper rather
   than moving sideways; the interesting boundary is where reconstruction stops.
4. **Find the gap before filling it.** When an answer is wrong or vague, do not
   correct it immediately. Ask the question whose answer makes the conflict
   visible to them. A contradiction they notice costs one exchange and lasts;
   a correction they accept costs nothing and does not.
5. **Then explain**, only the part they could not reach, and check it took by
   asking them to apply it somewhere the phrasing does not carry over.
6. **Name what stayed unresolved.** An open question is a result, not a
   failure, and it is what the next session starts from.
7. **Offer to keep it.** When the session produced understanding worth reusing,
   hand it to `note-writer`. Do not write the note silently - the user decides
   what enters their vault.

## Rules that keep it honest

- **Do not accept fluent restatement as understanding.** A user echoing your
  words has learned the words. Ask for an application, a boundary case, or a
  prediction instead.
- **Do not ask questions you cannot mark.** If you would accept any answer, the
  question tests nothing; ask something with a wrong answer.
- **Do not smuggle the answer into the question.** A question containing its
  own answer measures politeness, not knowledge.
- **The evidence rules still apply.** When you fill a gap with a material
  claim, it needs the same grounding as any other - a session is not a licence
  to teach something you have not checked. When you are unsure, say so and make
  the uncertainty part of the lesson.
- **Do not invent a wrong answer for the user to catch.** Confusion is found,
  not manufactured.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Who assembles the answer | The agent | The user, with the agent finding the gap |
| Diagnosis | Explanation aimed at the average learner | Aimed at where this user's model breaks |
| Retention check | Agreement read as understanding | Application, boundary case, or prediction |
| Exit | Session runs until the agent is done | User can stop, open questions recorded |
