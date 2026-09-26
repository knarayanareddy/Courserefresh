"The Course That Rewrites Itself": a curriculum that watches its own subject

World: Learning & Knowledge

One-liner: A course that monitors the thing it teaches — changelogs, docs, releases, papers, regulations — and rewrites its own lessons, regenerates its quizzes, versions the change, and tells every learner what changed and why it matters, before anyone asks.

The problem. Every course rots the moment its subject moves, and the rot is invisible: learners study last year's API while the world ships this year's. The information needed to detect the rot is public and timestamped; the labour of fixing it is what nobody does.

Autonomy loop.

    Notice: Apify scheduled monitors on the subject's authoritative sources (docs sites, GitHub releases, changelogs, regulatory registers) + Tavily Research for context; plus learner telemetry (time-on-task, wrong-answer patterns).
    Decide: Jev Noul "is this change material to lesson 4?" and Choice (rewrite lesson / add a callout / no change / escalate to the author), Score materiality.
    Act: edits the real lesson in its real home (Notion/Google Docs/LMS), regenerates the quiz and examples, commits a version with a diff, and notifies enrolled learners with a three-line "what changed and why you care."
    Learn: tracks whether the rewrite improved quiz scores and completion; rewrites that didn't help get reverted automatically.
    Report: "Claude shipped a model update at 23:40 yesterday. By 23:52 lesson 4 and its quiz were updated and 340 learners had the diff in their inbox. Two learners were stuck on the old example — both got the targeted micro-lesson before they asked."
    Stop: if it can't verify the change against two independent sources, it drafts but does not publish, and escalates to the human author.

Real data & real actions. The subject genuinely changes during your hackathon weekend — pick something that ships constantly (the AI tooling you're using is perfect and slightly cheeky). Real lessons, real learners (recruit participants Saturday night), real notifications. The strongest autonomy narrative on the list; the weakest side-effect narrative.
