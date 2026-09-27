// ─── Courses data — adapted in its entirety from the Next.js variant (courserefresh1)
// Source of truth: ~/Downloads/courserefresh1/src/db/seed.ts. That file was executed
// against a capture stub (not hand-transcribed), so every body, diff and quiz below is
// byte-identical to the seed. 3 courses · 8 lessons · 13 versioned histories · 6 quizzes.
//
// Honesty notes, per the repo's own rules (specs/courserefresh/spec.md §honesty):
//  ml-engineering and web-security are DEMO COURSES — the shipped repo has exactly one
//  real course (agent-ops). They are shown with the same paper/ink treatment and remain
//  clearly labelled as what they are: a catalogue view of what the product WOULD manage.

export interface CourseSource { url: string; captured_at: string; publisher: string; }

export interface VersionSource extends CourseSource { confidence: number; }

export interface QuizItem {
  id: string;
  version: number;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
  objectiveRef?: string | null;
}

export interface LessonVersion {
  id: number;
  version: number;
  body: string;
  changeLog: string | null;
  diffText: string | null;
  action: string;          // PUBLISH | REVERT | ESCALATE | NO_CHANGE | DRAFT
  authority: string;       // PA0..PA3
  reasonCodes: string[];
  sources: VersionSource[];
  confidence: number;
}

export interface Lesson {
  id: number;
  slug: string;
  title: string;
  version: number;
  body: string;
  objectives: string[];
  prerequisites: string[];
  sources: CourseSource[];
  status: string;
  quizzes: QuizItem[];
  versions: LessonVersion[];
}

export interface Course {
  id: number;
  slug: string;
  title: string;
  description: string;
  subject: string;
  totalLessons: number;
  authority: string;
  consecutiveAcceptedPublishes: number;
  lessons: Lesson[];
  real: boolean;           // true = the repo's actual shipped course
}

// REAL COURSE — agent-ops
export const courseAgentOps: Course = {
  id: 1,
  slug: "agent-ops",
  title: "Agent Ops: n8n + Apify in Production",
  description: "A six-lesson course on building, running, and governing AI agents with n8n and Apify. Continuously updated as n8n and Apify ship new releases.",
  subject: "AI Agent Operations",
  totalLessons: 6,
  authority: "PA2",
  consecutiveAcceptedPublishes: 4,
  real: true,
  lessons: [
    {
      id: 1, slug: "lesson-01-n8n-fundamentals", title: "Lesson 1 \u2014 n8n Workflow Fundamentals",
      version: 4,
      body: "## What is n8n?\n\nn8n (pronounced \"n-eight-n\") is a workflow automation platform that lets you connect any app, API, or service through a visual canvas. Unlike traditional iPaaS tools, n8n is **source-available**, self-hostable, and designed with a code-when-needed philosophy.\n\n### Core Concepts\n\n**Nodes** are the building blocks of every workflow. Each node connects to one service or performs one transformation. In n8n 1.85+, the node sidebar is organised by category: Triggers, Actions, Logic, and Data.\n\n**Executions** are the recorded runs of a workflow. Every execution carries a status (success / partial / error), a start time, and an itemised log of each node's input and output. This makes n8n inherently auditable.\n\n**Credentials** are stored encrypted, scoped per-node, and never appear in workflow exports. This separation between the canvas and the key store is a key safety property.\n\n### Connecting Nodes\n\nConnect nodes by dragging from one node's output handle to another's input handle. Data flows as **items** — an array of JSON objects. Each node receives the full item array and may transform, filter, or fan it out.\n\n> **v1.85 change (2026-04-14):** The \"Workflow Settings\" panel was renamed to \"Workflow Preferences\". Any documentation or lesson referring to the old name is now stale. The setting key in the API remains `settings` — only the UI label changed.\n\n### The Execute Once Pattern\n\nWhen processing a list of items (e.g., 50 snapshots), the default behaviour runs the downstream nodes once per item. Toggle **\"Execute Once\"** in a node's settings to batch the entire array in a single call — critical for expensive downstream nodes like LLM judges.\n\n### Error Handling\n\nAttach an **Error Workflow** to any workflow via Workflow Preferences → Error Workflow. The error workflow receives the full execution context, including the failing node name, the input that caused the failure, and the error message.\n\n### What Changed in v1.85\n\n| Before | After |\n|---|---|\n| \"Workflow Settings\" (sidebar tab) | \"Workflow Preferences\" (top-right gear icon) |\n| Error workflow set globally | Error workflow set per-workflow |\n| Node panel alphabetical | Node panel by category |\n\n---\n\n*Sources verified 2026-04-18 · Lesson v4 · Confidence 0.94*",
      objectives: [
  "Explain what n8n nodes, executions, and credentials are",
  "Connect nodes and trace data flow as items",
  "Configure error handling per workflow",
  "Identify what changed in n8n 1.85"
],
      prerequisites: [
  "Basic understanding of REST APIs",
  "Familiarity with JSON"
],
      sources: [
  {
    "url": "https://docs.n8n.io/workflows/",
    "captured_at": "2026-04-18",
    "publisher": "n8n"
  },
  {
    "url": "https://github.com/n8n-io/n8n/releases/tag/n8n%401.85.0",
    "captured_at": "2026-04-14",
    "publisher": "n8n GitHub"
  }
],
      status: "PUBLISHED",
      quizzes: [
        {
          id: "lesson-01-n8n-fundamentals-q1",
          version: 4,
          question: "In n8n 1.85+, what is the new name for the panel previously called 'Workflow Settings'?",
          options: [
  "Workflow Configuration",
  "Workflow Preferences",
  "Workflow Controls",
  "Node Settings"
],
          correctIndex: 1,
          explanation: "n8n 1.85 renamed 'Workflow Settings' to 'Workflow Preferences', accessible via the top-right gear icon. The API key 'settings' is unchanged.",
          objectiveRef: "Identify what changed in n8n 1.85",
        },
        {
          id: "lesson-01-n8n-fundamentals-q2",
          version: 4,
          question: "What does the 'Execute Once' toggle do in an n8n node?",
          options: [
  "Runs the workflow only one time total",
  "Skips the node if it has already run in a previous execution",
  "Passes the entire item array to the node in a single call instead of once per item",
  "Disables error handling for that node"
],
          correctIndex: 2,
          explanation: "Execute Once batches all items into a single node call, which is critical for expensive downstream nodes like LLM judges to avoid N calls for N items.",
          objectiveRef: "Connect nodes and trace data flow as items",
        },
      ],
      versions: [
        {
          id: 1, version: 1,
          body: "## What is n8n?\n\nn8n is a workflow automation platform. Nodes connect services. Executions are recorded runs. Credentials are encrypted.\n\n*Sources verified 2026-03-01 · Lesson v1 · Confidence 0.80*",
          changeLog: "Initial version",
          diffText: null,
          action: "PUBLISH", authority: "PA1",
          reasonCodes: [
  "initial_publish"
],
          sources: [
  {
    "url": "https://docs.n8n.io/",
    "captured_at": "2026-03-01",
    "publisher": "n8n",
    "confidence": 0.8
  }
],
          confidence: 0.8,
        },
        {
          id: 2, version: 2,
          body: "## What is n8n?\n\nn8n is a workflow automation platform that lets you connect any app, API, or service through a visual canvas. Unlike traditional iPaaS tools, n8n is source-available and self-hostable.\n\n### Core Concepts\n\n**Nodes** are the building blocks. **Executions** are recorded runs. **Credentials** are encrypted and scoped.\n\n> **v1.80 change:** The HTTP Request node now supports OAuth2 with PKCE by default.\n\n*Sources verified 2026-03-28 · Lesson v2 · Confidence 0.86*",
          changeLog: "Added v1.80 OAuth2/PKCE change; expanded core concepts section",
          diffText: "--- v1\n+++ v2\n@@ -1,3 +1,8 @@\n ## What is n8n?\n \n-n8n is a workflow automation platform. Nodes connect services. Executions are recorded runs.\n+n8n is a workflow automation platform that lets you connect any app, API, or service through a visual canvas.\n+Unlike traditional iPaaS tools, n8n is source-available and self-hostable.\n+\n+> **v1.80 change:** The HTTP Request node now supports OAuth2 with PKCE by default.",
          action: "PUBLISH", authority: "PA1",
          reasonCodes: [
  "corroborated_change",
  "above_materiality"
],
          sources: [
  {
    "url": "https://docs.n8n.io/",
    "captured_at": "2026-03-28",
    "publisher": "n8n",
    "confidence": 0.86
  },
  {
    "url": "https://github.com/n8n-io/n8n/releases/tag/n8n%401.80.0",
    "captured_at": "2026-03-28",
    "publisher": "n8n GitHub",
    "confidence": 0.91
  }
],
          confidence: 0.88,
        },
        {
          id: 3, version: 3,
          body: "## What is n8n?\n\nn8n is a workflow automation platform. Nodes are the building blocks.\n\n> **REVERTED:** v3 incorrectly stated that the Webhook node was deprecated. This was sourced from a single community forum post that misread the release notes. Reverted to v2 content.\n\n*Revert receipt: rcpt-e8-0021 · gate_satisfied · quiz_delta: -0.08*",
          changeLog: "REVERT: v3 claimed Webhook node deprecated — single source, uncorroborated, quiz delta -0.08 triggered gate",
          diffText: "--- v3\n+++ v3-revert\n@@ -3,4 +3,4 @@\n-INCORRECT: The Webhook node is deprecated in n8n 1.82.\n+> **REVERTED:** v3 incorrectly stated that the Webhook node was deprecated.",
          action: "REVERT", authority: "PA2",
          reasonCodes: [
  "revert_gate_satisfied",
  "quiz_delta_negative"
],
          sources: [
  {
    "url": "https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/",
    "captured_at": "2026-04-02",
    "publisher": "n8n",
    "confidence": 0.99
  }
],
          confidence: 0.99,
        },
        {
          id: 4, version: 4,
          body: "## What is n8n?\n\nn8n is a workflow automation platform that lets you connect any app, API, or service through a visual canvas. Unlike traditional iPaaS tools, n8n is source-available, self-hostable, and designed with a code-when-needed philosophy.\n\n> **v1.85 change (2026-04-14):** The \"Workflow Settings\" panel was renamed to \"Workflow Preferences\".\n\n*Sources verified 2026-04-18 · Lesson v4 · Confidence 0.94*",
          changeLog: "n8n 1.85: \"Workflow Settings\" renamed to \"Workflow Preferences\"; category-based node panel added",
          diffText: "--- v3-revert\n+++ v4\n@@ -2,4 +2,6 @@\n n8n is a workflow automation platform that lets you connect any app.\n \n+> **v1.85 change (2026-04-14):** The \"Workflow Settings\" panel was renamed to \"Workflow Preferences\".\n+> Any documentation referring to the old name is now stale.\n \n *Sources verified 2026-04-18 · Lesson v4 · Confidence 0.94*",
          action: "PUBLISH", authority: "PA2",
          reasonCodes: [
  "corroborated_change",
  "above_materiality"
],
          sources: [
  {
    "url": "https://docs.n8n.io/workflows/",
    "captured_at": "2026-04-18",
    "publisher": "n8n",
    "confidence": 0.94
  },
  {
    "url": "https://github.com/n8n-io/n8n/releases/tag/n8n%401.85.0",
    "captured_at": "2026-04-14",
    "publisher": "n8n GitHub",
    "confidence": 0.96
  }
],
          confidence: 0.94,
        },
      ],
    },
    {
      id: 2, slug: "lesson-02-apify-actors", title: "Lesson 2 \u2014 Apify Actors & Datasets",
      version: 3,
      body: "## Apify Actors\n\nAn **Actor** is a cloud-native scraping or automation program that runs on Apify's infrastructure. Think of it as a Docker container pre-wired with retries, proxy rotation, and a standardised dataset output.\n\n### Actor Anatomy\n\nEvery actor has:\n- **Input schema** — a JSON Schema that validates the parameters you pass at run time\n- **Dataset** — an append-only structured output store; each item is a JSON row\n- **Key-value store** — for arbitrary binary artefacts (screenshots, HTML snapshots)\n- **Run log** — a timestamped stdout stream, accessible via the API and the Apify Console\n\n### Running an Actor from n8n\n\nUse the **Apify node** in n8n (category: Data → Extract):\n\n```\nActor ID:   apify/website-content-crawler\nBuild tag:  latest  ← pin this to a specific build hash in production\nWait:       For Run to Finish\nOutput:     Dataset items\n```\n\n> **v3.3.2 change (2026-03-28):** `apify/website-content-crawler` now returns a `metadata.statusCode` field on every item. Downstream nodes that parse item shapes must handle this new field or they will throw on unexpected keys.\n\n### Pinning Actor Versions\n\nIn production, always pin to a specific build, not `latest`:\n\n```json\n{\n  \"actorId\": \"apify~website-content-crawler\",\n  \"build\": \"1.11.112-beta.0\"\n}\n```\n\nThis ensures reproducible runs and a clear audit trail — the run history shows exactly which build produced which dataset.\n\n### Deduplication with Content Hashes\n\nCourserefresh hashes each captured item (`SHA-256(url + content)`) and stores the hash in `snapshots/seen.json`. On the next scan cycle, items whose hash matches are silently skipped and the run receipt records `no_delta` for that source.\n\n### Dataset Pagination\n\nLarge datasets are paginated at 1,000 items per page. The Apify node in n8n automatically pages through the full dataset. If you call the Apify API directly, remember to pass `offset` and `limit` query parameters.\n\n---\n\n*Sources verified 2026-04-16 · Lesson v3 · Confidence 0.91*",
      objectives: [
  "Describe the anatomy of an Apify Actor",
  "Run an actor from n8n and extract its dataset",
  "Pin actors to specific build versions",
  "Implement content-hash deduplication"
],
      prerequisites: [
  "Lesson 1 — n8n Workflow Fundamentals"
],
      sources: [
  {
    "url": "https://docs.apify.com/actors",
    "captured_at": "2026-04-16",
    "publisher": "Apify"
  },
  {
    "url": "https://github.com/apify/apify-sdk-js/releases/tag/v3.3.2",
    "captured_at": "2026-03-28",
    "publisher": "Apify GitHub"
  }
],
      status: "PUBLISHED",
      quizzes: [
        {
          id: "lesson-02-apify-actors-q1",
          version: 3,
          question: "What new field does apify/website-content-crawler v3.3.2 return on every item?",
          options: [
  "metadata.capturedAt",
  "metadata.statusCode",
  "metadata.version",
  "metadata.checksum"
],
          correctIndex: 1,
          explanation: "v3.3.2 added metadata.statusCode to every item. Downstream nodes that parse item shapes must handle this new field.",
          objectiveRef: "Run an actor from n8n and extract its dataset",
        },
      ],
      versions: [
        {
          id: 5, version: 1,
          body: "## Apify Actors\n\nActors are cloud-native automation programs. They have input schemas, datasets, and key-value stores.\n\n*Sources verified 2026-03-05 · Lesson v1 · Confidence 0.82*",
          changeLog: "Initial version",
          diffText: null,
          action: "PUBLISH", authority: "PA1",
          reasonCodes: [
  "initial_publish"
],
          sources: [
  {
    "url": "https://docs.apify.com/actors",
    "captured_at": "2026-03-05",
    "publisher": "Apify",
    "confidence": 0.82
  }
],
          confidence: 0.82,
        },
        {
          id: 6, version: 2,
          body: "## Apify Actors\n\nActors are cloud-native programs. Added section on pinning build versions for reproducibility.\n\n*Sources verified 2026-03-20 · Lesson v2 · Confidence 0.87*",
          changeLog: "Added build pinning section; added dataset pagination notes",
          diffText: "--- v1\n+++ v2\n+### Pinning Actor Versions\n+Always pin to a specific build hash, not `latest`.",
          action: "PUBLISH", authority: "PA1",
          reasonCodes: [
  "corroborated_change",
  "above_materiality"
],
          sources: [
  {
    "url": "https://docs.apify.com/actors",
    "captured_at": "2026-03-20",
    "publisher": "Apify",
    "confidence": 0.87
  },
  {
    "url": "https://docs.apify.com/api/v2",
    "captured_at": "2026-03-20",
    "publisher": "Apify",
    "confidence": 0.85
  }
],
          confidence: 0.87,
        },
        {
          id: 7, version: 3,
          body: "## Apify Actors v3\n\n> **v3.3.2 change:** website-content-crawler now returns metadata.statusCode on every item.\n\n*Sources verified 2026-04-16 · Lesson v3 · Confidence 0.91*",
          changeLog: "Added v3.3.2 statusCode field change; added deduplication section",
          diffText: "--- v2\n+++ v3\n+> **v3.3.2 change (2026-03-28):** `apify/website-content-crawler` now returns a `metadata.statusCode` field.",
          action: "PUBLISH", authority: "PA2",
          reasonCodes: [
  "corroborated_change",
  "above_materiality"
],
          sources: [
  {
    "url": "https://docs.apify.com/actors",
    "captured_at": "2026-04-16",
    "publisher": "Apify",
    "confidence": 0.91
  },
  {
    "url": "https://github.com/apify/apify-sdk-js/releases/tag/v3.3.2",
    "captured_at": "2026-03-28",
    "publisher": "Apify GitHub",
    "confidence": 0.95
  }
],
          confidence: 0.91,
        },
      ],
    },
    {
      id: 3, slug: "lesson-03-policy-decisions", title: "Lesson 3 \u2014 The Policy Node: Deterministic Decisions",
      version: 5,
      body: "## Why a Policy Node?\n\nLanguage models are powerful but non-deterministic. For a system that rewrites course content, non-determinism is a liability — the same evidence should always produce the same action. The **Policy Node** is Courserefresh's answer: a deterministic, rule-based decision engine that lives in n8n and is tested against a Python oracle.\n\n### The Authority Ladder\n\n| Level | What runs | How earned |\n|---|---|---|\n| **PA0** | Draft only, notify nobody | Default on first run |\n| **PA1** | Auto-publish to `course/**` | First clean preflight passes |\n| **PA2** | Auto-publish + notify cohort | 3 consecutive accepted publishes, 0 rollbacks |\n| **PA3** | Human-only | Assessment changes, learner records, irreversible actions |\n\n### Rule Order (R1–R8)\n\n```javascript\n// POLICY node — rules execute in order, first match wins\nR1: if (injection_score >= 0.7)        → ESCALATE(injection_or_jailbreak)\nR2: if (sources_verified < 2)          → ESCALATE(insufficient_corroboration)\nR3: if (source_conflict)               → ESCALATE(source_conflict)\nR4: if (assessment_touched)            → ESCALATE(assessment_integrity)   // PA3 forever\nR5: if (budget_exceeded)               → ESCALATE(over_budget)\nR6: if (materiality < threshold)       → NO_CHANGE(below_materiality)\nR7: if (action == \"REVERT\" && !gate)   → ESCALATE(gate_missing)\nR8: default                            → PUBLISH(authority: current_pa_level)\n```\n\n### Parity Testing\n\nThe same rules run in two runtimes:\n- **Production:** `app/n8n/policy_node.js` (runs inside the n8n Code node)\n- **Oracle:** `specs/courserefresh/skin/policy.py` (Python, used in tests)\n\n`test_gate_parity.py` runs all 59 gold rows through both and fails if any row disagrees. Zero disagreements is the floor.\n\n> **Update 2026-04-20:** Threshold `materiality_floor` raised from 0.45 → 0.52 after post-build panel review (specs/reviews/04). Three gold rows that previously returned PUBLISH now return NO_CHANGE. Lesson updated to reflect new threshold.\n\n### Reading a Receipt\n\nEvery decision writes one receipt:\n\n```json\n{\n  \"receipt_id\": \"rcpt-e8-0042\",\n  \"action\": \"PUBLISH\",\n  \"authority\": \"PA2\",\n  \"reason_codes\": [\"corroborated_change\", \"above_materiality\"],\n  \"sources\": [\n    {\"url\": \"...\", \"confidence\": 0.94},\n    {\"url\": \"...\", \"confidence\": 0.89}\n  ],\n  \"revert_gate\": {\n    \"metric\": \"quiz_delta\",\n    \"threshold\": 0,\n    \"cohort_min\": 5,\n    \"deadline_h\": 48\n  }\n}\n```\n\n---\n\n*Sources verified 2026-04-20 · Lesson v5 · Confidence 0.97*",
      objectives: [
  "Explain the authority ladder PA0–PA3 and how each level is earned",
  "Read the rule order R1–R8 and predict the output for a given input",
  "Understand why parity testing across two runtimes matters",
  "Parse a receipt and identify all required fields"
],
      prerequisites: [
  "Lesson 1 — n8n Workflow Fundamentals",
  "Lesson 2 — Apify Actors & Datasets"
],
      sources: [
  {
    "url": "https://github.com/knarayanareddy/Courserefresh/blob/main/specs/constitution.md",
    "captured_at": "2026-04-20",
    "publisher": "Courserefresh Repo"
  },
  {
    "url": "https://docs.n8n.io/code/code-node/",
    "captured_at": "2026-04-20",
    "publisher": "n8n"
  }
],
      status: "PUBLISHED",
      quizzes: [
        {
          id: "lesson-03-policy-decisions-q1",
          version: 5,
          question: "What is the minimum number of independent sources required for a PUBLISH action?",
          options: [
  "1",
  "2",
  "3",
  "5"
],
          correctIndex: 1,
          explanation: "Art. III requires ≥2 independent sources from different publishers and different content origins. Two pages from the same organisation count as one source.",
          objectiveRef: "Read the rule order R1–R8 and predict the output for a given input",
        },
        {
          id: "lesson-03-policy-decisions-q2",
          version: 5,
          question: "What is the materiality_floor threshold as of Lesson 3 v5?",
          options: [
  "0.35",
  "0.45",
  "0.52",
  "0.70"
],
          correctIndex: 2,
          explanation: "The materiality_floor was raised from 0.45 to 0.52 after the post-build panel review (specs/reviews/04). Three gold rows now return NO_CHANGE instead of PUBLISH.",
          objectiveRef: "Read the rule order R1–R8 and predict the output for a given input",
        },
      ],
      versions: [
        {
          id: 8, version: 3,
          body: "## Policy Node v3\n\nmateriality_floor = 0.45\n\nR8 default: PUBLISH if materiality >= 0.45\n\n*Sources verified 2026-04-10 · Lesson v3 · Confidence 0.90*",
          changeLog: "Added rule order documentation",
          diffText: "--- v2\n+++ v3\n+R6: if (materiality < 0.45) → NO_CHANGE(below_materiality)",
          action: "PUBLISH", authority: "PA1",
          reasonCodes: [
  "corroborated_change"
],
          sources: [
  {
    "url": "https://github.com/knarayanareddy/Courserefresh/blob/main/specs/constitution.md",
    "captured_at": "2026-04-10",
    "publisher": "Courserefresh Repo",
    "confidence": 0.9
  }
],
          confidence: 0.9,
        },
        {
          id: 9, version: 4,
          body: "## Policy Node v4\n\nmateriality_floor = 0.45 (unchanged)\n\nAdded parity testing section.\n\n*Sources verified 2026-04-15 · Lesson v4 · Confidence 0.93*",
          changeLog: "Added parity testing explanation and gold set reference",
          diffText: "--- v3\n+++ v4\n+### Parity Testing\n+The same rules run in two runtimes: policy_node.js (production) and policy.py (oracle).",
          action: "PUBLISH", authority: "PA2",
          reasonCodes: [
  "corroborated_change",
  "above_materiality"
],
          sources: [
  {
    "url": "https://github.com/knarayanareddy/Courserefresh/blob/main/specs/constitution.md",
    "captured_at": "2026-04-15",
    "publisher": "Courserefresh Repo",
    "confidence": 0.93
  },
  {
    "url": "https://docs.n8n.io/code/code-node/",
    "captured_at": "2026-04-15",
    "publisher": "n8n",
    "confidence": 0.91
  }
],
          confidence: 0.93,
        },
        {
          id: 10, version: 5,
          body: "## Policy Node v5\n\n> materiality_floor raised: 0.45 → 0.52 after post-build panel review.\n\n*Sources verified 2026-04-20 · Lesson v5 · Confidence 0.97*",
          changeLog: "materiality_floor 0.45→0.52; three gold rows now return NO_CHANGE instead of PUBLISH",
          diffText: "--- v4\n+++ v5\n-materiality_floor: 0.45\n+materiality_floor: 0.52\n+\n+> Three gold rows that previously returned PUBLISH now return NO_CHANGE.",
          action: "PUBLISH", authority: "PA2",
          reasonCodes: [
  "corroborated_change",
  "above_materiality",
  "threshold_update"
],
          sources: [
  {
    "url": "https://github.com/knarayanareddy/Courserefresh/blob/main/specs/reviews/04-post-build-panel-and-audit.md",
    "captured_at": "2026-04-20",
    "publisher": "Courserefresh Repo",
    "confidence": 0.97
  },
  {
    "url": "https://docs.n8n.io/code/code-node/",
    "captured_at": "2026-04-20",
    "publisher": "n8n",
    "confidence": 0.91
  }
],
          confidence: 0.97,
        },
      ],
    },
    {
      id: 4, slug: "lesson-04-revert-gates", title: "Lesson 4 \u2014 Revert Gates & the Falsification Clause",
      version: 3,
      body: "## Publishing Means Promising to Undo\n\nA course update is a hypothesis: \"this new content is more accurate than the old\". Like any hypothesis, it must be falsifiable. Courserefresh enforces this through **Revert Gates** — a condition written at publish time that, if satisfied, triggers an automatic rollback.\n\n### Gate Structure\n\n```json\n{\n  \"metric\": \"quiz_delta\",\n  \"threshold\": 0,\n  \"cohort_min\": 5,\n  \"deadline_h\": 48\n}\n```\n\n- **metric:** what to measure (`quiz_delta`, `completion_rate_delta`, `stuck_rate_delta`)\n- **threshold:** the value at or below which the gate triggers a revert\n- **cohort_min:** minimum learners needed for a valid measurement (Art. V.3)\n- **deadline_h:** hours after publish when the gate is evaluated\n\n### The Three Gate States\n\n| State | Meaning | Action |\n|---|---|---|\n| **open** | Evaluation pending; within deadline | No action |\n| **satisfied** | Metric crossed threshold with n ≥ cohort_min | Auto-revert |\n| **unmeasured** | n < cohort_min or telemetry lost | Report \"unmeasured\", no revert claim |\n\n### What a Revert Looks Like\n\nA revert is **not** an undo. It is a new version:\n\n```\nlesson-04/\n  v1.md   ← original\n  v2.md   ← updated (published 2026-04-18)\n  v3.md   ← revert of v2 (published 2026-04-20, gate_satisfied)\n  diffs/\n    v2.diff\n    v3.diff\n  CHANGELOG.md\n```\n\nVersion v3 has its own receipt, its own diff, and it notifies the same cohort that received v2.\n\n> **Important:** A revert on \"vibes\" — an author feeling the change was wrong — is not allowed (Art. XI.2). The gate must be satisfied by measured telemetry. If you want to override, write a new receipt as `actor: human:your_name`.\n\n### When Gates Cannot Be Measured\n\nIf fewer than `cohort_min` learners interacted with the lesson in the window, the gate status is `unmeasured`. The digest reports this explicitly:\n\n```\nGate: lesson-04 v2 → UNMEASURED (n=3, required n≥5, deadline 2026-04-20 07:30 UTC)\nNo revert claim is made.\n```\n\n---\n\n*Sources verified 2026-04-20 · Lesson v3 · Confidence 0.95*",
      objectives: [
  "Write a valid revert gate for a published lesson",
  "Interpret the three gate states and their consequences",
  "Distinguish a legitimate revert from a vibes-based rollback",
  "Identify when a gate is unmeasured and what the system must report"
],
      prerequisites: [
  "Lesson 3 — The Policy Node"
],
      sources: [
  {
    "url": "https://github.com/knarayanareddy/Courserefresh/blob/main/specs/constitution.md",
    "captured_at": "2026-04-20",
    "publisher": "Courserefresh Repo"
  },
  {
    "url": "https://docs.n8n.io/workflows/executions/",
    "captured_at": "2026-04-20",
    "publisher": "n8n"
  }
],
      status: "PUBLISHED",
      quizzes: [
        {
          id: "lesson-04-revert-gates-q1",
          version: 3,
          question: "When is a revert gate in the 'unmeasured' state?",
          options: [
  "When the metric value is above the threshold",
  "When fewer than cohort_min learners interacted with the lesson in the window",
  "When the deadline has passed",
  "When the system is in PA0 mode"
],
          correctIndex: 1,
          explanation: "A gate is unmeasured when n < cohort_min (or telemetry is lost). The system reports 'unmeasured' and makes no revert claim.",
          objectiveRef: "Identify when a gate is unmeasured and what the system must report",
        },
      ],
      versions: [
        {
          id: 11, version: 1,
          body: "## Revert Gates\n\nA revert gate is written at publish time.\n\n*Sources verified 2026-03-10 · Lesson v1 · Confidence 0.80*",
          changeLog: "Initial version",
          diffText: null,
          action: "PUBLISH", authority: "PA1",
          reasonCodes: [
  "initial_publish"
],
          sources: [
  {
    "url": "https://github.com/knarayanareddy/Courserefresh/blob/main/specs/constitution.md",
    "captured_at": "2026-03-10",
    "publisher": "Courserefresh Repo",
    "confidence": 0.8
  }
],
          confidence: 0.8,
        },
        {
          id: 12, version: 2,
          body: "## Revert Gates v2\n\nAdded gate structure JSON and three gate states (open, satisfied, unmeasured).\n\n*Sources verified 2026-04-05 · Lesson v2 · Confidence 0.89*",
          changeLog: "Added gate JSON structure; documented three states",
          diffText: "--- v1\n+++ v2\n+### The Three Gate States\n+open · satisfied · unmeasured",
          action: "PUBLISH", authority: "PA2",
          reasonCodes: [
  "corroborated_change",
  "above_materiality"
],
          sources: [
  {
    "url": "https://github.com/knarayanareddy/Courserefresh/blob/main/specs/constitution.md",
    "captured_at": "2026-04-05",
    "publisher": "Courserefresh Repo",
    "confidence": 0.89
  },
  {
    "url": "https://docs.n8n.io/workflows/executions/",
    "captured_at": "2026-04-05",
    "publisher": "n8n",
    "confidence": 0.85
  }
],
          confidence: 0.89,
        },
        {
          id: 13, version: 3,
          body: "## Revert Gates v3\n\nAdded revert-as-new-version section and unmeasured gate reporting.\n\n*Sources verified 2026-04-20 · Lesson v3 · Confidence 0.95*",
          changeLog: "Added versioned revert example; clarified unmeasured reporting format",
          diffText: "--- v2\n+++ v3\n+### What a Revert Looks Like\n+A revert is not an undo. It is a new version with its own receipt and diff.",
          action: "PUBLISH", authority: "PA2",
          reasonCodes: [
  "corroborated_change",
  "above_materiality"
],
          sources: [
  {
    "url": "https://github.com/knarayanareddy/Courserefresh/blob/main/specs/constitution.md",
    "captured_at": "2026-04-20",
    "publisher": "Courserefresh Repo",
    "confidence": 0.95
  },
  {
    "url": "https://docs.n8n.io/workflows/executions/",
    "captured_at": "2026-04-20",
    "publisher": "n8n",
    "confidence": 0.91
  }
],
          confidence: 0.95,
        },
      ],
    },
    {
      id: 5, slug: "lesson-05-learner-telemetry", title: "Lesson 5 \u2014 Learner Telemetry & Stuck Detection",
      version: 2,
      body: "## Knowing Before They Ask\n\nThe most powerful thing a course can do is help a learner before they know they need it. Courserefresh's telemetry layer does this by watching two signals:\n\n1. **consecutive_wrong ≥ 2** — two wrong quiz answers in a row on the same objective\n2. **dwell ≥ 3 × median** — time on a section is 3× the cohort median (confusion, not deep reading)\n\nWhen either signal fires, and the learner has given consent, a **micro-lesson** is dispatched.\n\n### Consent First\n\nTelemetry is only stored for learners who have explicitly opted in (Art. V.1). The consent flow:\n\n```\nPOST /telemetry\n{ \"learner_handle\": \"learner:a3f2c1d4\", \"consent\": true, ... }\n\n→ HTTP 403 if consent is false or absent (nothing stored)\n→ HTTP 200 + receipt if consent is true\n```\n\nHandles are hashed: `learner:<sha256[..8]>`. Real names never enter the system.\n\n### Micro-Lesson Format\n\n```markdown\n**Concept:** The Execute Once toggle in n8n\n\nIn n8n, when your workflow processes a list of items, every downstream\nnode runs once per item by default. If you want to pass the entire list\nto an expensive node (like an LLM call), toggle **Execute Once** in the\nnode's settings.\n\n**Practice:** Open your workflow. Find the Code node that calls the\nJUDGE model. Count how many times it executes per run. If it runs N times\n(once per item), enable Execute Once and re-run. The execution count\nshould drop to 1.\n\n*[Opt out of future micro-lessons]*\n```\n\nRules: one concept, ≤ 2 minutes reading, one practice item, always an opt-out.\n\n### Rate Limits\n\nHard-coded in the policy, not configurable without an amendment:\n\n| Cap | Value |\n|---|---|\n| Per learner per day | 1 micro-lesson |\n| Per learner per week | 3 micro-lessons |\n| Cohort minimum for statistics | n ≥ 3 |\n| Cohort minimum for gate evaluation | n ≥ 5 |\n\n---\n\n*Sources verified 2026-04-19 · Lesson v2 · Confidence 0.89*",
      objectives: [
  "Identify the two stuck signals and their thresholds",
  "Explain why consent is checked before storage, not after",
  "Write a valid micro-lesson following the three-part format",
  "State the four hard rate-limit values"
],
      prerequisites: [
  "Lesson 3 — The Policy Node",
  "Lesson 4 — Revert Gates"
],
      sources: [
  {
    "url": "https://github.com/knarayanareddy/Courserefresh/blob/main/specs/constitution.md",
    "captured_at": "2026-04-19",
    "publisher": "Courserefresh Repo"
  },
  {
    "url": "https://docs.apify.com/api/v2",
    "captured_at": "2026-04-19",
    "publisher": "Apify"
  }
],
      status: "PUBLISHED",
      quizzes: [],
      versions: [],
    },
    {
      id: 6, slug: "lesson-06-morning-digest", title: "Lesson 6 \u2014 The Morning Digest & Ops Runbook",
      version: 2,
      body: "## The Digest: The System's Face\n\nThe morning digest (sent at 07:30 UTC) is the one document that captures everything the system did while nobody was watching. It is ≤ 4096 bytes, generated from receipts only, and follows a fixed section order:\n\n1. **Run header** — run_id · mode · cadence · budgets used\n2. **Refusals** (first, always) — each with reason code and preserved quote\n3. **Changes** — published diffs with version numbers\n4. **Learner panel** — cohort window, gate states, unmeasured badges\n5. **Discipline strip** — chain integrity, receipt coverage, unmeasured list\n\n### Section Order Is a Safety Property\n\nRefusals appear first because the most important information is what the system *refused to do*. An operator who reads only the first section knows whether any safety boundary was approached. A digest that leads with successes buries the signal.\n\n### Sample Digest\n\n```\n=== COURSEREFRESH DIGEST ===\nrun_id: e8-20260418-0730 · mode: live · cadence: 63 min (measured)\nApify: 18.4 units · Tokens: 42,100 · Publishes: 2 · Refusals: 3\n\n── REFUSALS (3) ──────────────────────────────────────\n[REFUSED] cr-single-01 · insufficient_corroboration\n  Quote: \"n8n 1.86 removes the HTTP Request node\"\n  One source (n8n community forum). No corroboration found.\n\n[REFUSED] cr-inject-01 · injection_or_jailbreak\n  Hostile instruction detected in scraped page.\n  Event preserved in receipts/rcpt-e8-0041.json\n\n[REFUSED] cr-assess-01 · assessment_integrity\n  Change would alter quiz answer key. PA3 — human required.\n\n── CHANGES (2) ───────────────────────────────────────\n[PUBLISHED] lesson-01 v3→v4 · corroborated_change · PA2\n  n8n 1.85 UI rename: \"Workflow Settings\" → \"Workflow Preferences\"\n  Gate: quiz_delta ≤ 0 at 48 h, cohort n=12\n\n[PUBLISHED] lesson-03 v4→v5 · corroborated_change · PA2\n  materiality_floor updated 0.45→0.52 (post-build panel)\n\n── LEARNER PANEL ─────────────────────────────────────\nCohort: 12 learners · Window: 48 h · Gate: lesson-01 v4 OPEN\nMicro-lessons dispatched: 2 (consent verified)\n\n── DISCIPLINE ────────────────────────────────────────\nChain: ✓ (42 receipts, 0 gaps)\nCoverage: 100%\nUnmeasured: gate lesson-02 v3 (n=3, required n≥5)\n\n=== END ===\n```\n\n### Reading in One Minute\n\nThe digest is designed to be read in 60 seconds. If it takes longer, the system has too much noise. The 4 KB limit enforces this: older sections are trimmed if needed, but refusals are never trimmed.\n\n---\n\n*Sources verified 2026-04-18 · Lesson v2 · Confidence 0.92*",
      objectives: [
  "State the five digest sections and their fixed order",
  "Explain why refusals appear first",
  "Identify what 'unmeasured' means in the discipline strip",
  "Read a real digest and extract the key operational facts"
],
      prerequisites: [
  "Lesson 5 — Learner Telemetry"
],
      sources: [
  {
    "url": "https://github.com/knarayanareddy/Courserefresh/blob/main/specs/courserefresh/plan.md",
    "captured_at": "2026-04-18",
    "publisher": "Courserefresh Repo"
  },
  {
    "url": "https://docs.n8n.io/workflows/executions/",
    "captured_at": "2026-04-18",
    "publisher": "n8n"
  }
],
      status: "PUBLISHED",
      quizzes: [],
      versions: [],
    },
  ],
};

// DEMO COURSE (catalogue illustration) — ml-engineering
export const courseMlEngineering: Course = {
  id: 2,
  slug: "ml-engineering",
  title: "ML Engineering & Model Ops",
  description: "End-to-end machine learning engineering from feature pipelines to production model monitoring. Tracks MLflow, Weights & Biases, and framework releases.",
  subject: "Machine Learning Engineering",
  totalLessons: 5,
  authority: "PA1",
  consecutiveAcceptedPublishes: 1,
  real: false,
  lessons: [
    {
      id: 7, slug: "lesson-01-feature-pipelines", title: "Lesson 1 \u2014 Feature Pipelines & Data Versioning",
      version: 2,
      body: "## Feature Pipelines\n\nA feature pipeline transforms raw data into model-ready features. Reproducibility requires that every feature set be versioned — not just the model.\n\n### DVC for Data Versioning\n\nDVC (Data Version Control) tracks large files outside git:\n\n```bash\ndvc init\ndvc add data/features.parquet\ngit add data/features.parquet.dvc\ngit commit -m \"feat: add feature set v1\"\n```\n\n> **MLflow 2.13 change (2026-03-10):** The `mlflow.data` module now supports Delta Lake as a first-class dataset source. Lessons using the `PandasDataset` API must account for the new `DeltaDataset` type returned by `mlflow.data.from_delta()`.\n\n*Sources verified 2026-04-10 · Lesson v2 · Confidence 0.88*",
      objectives: [
  "Version datasets with DVC",
  "Log feature sets in MLflow 2.13+"
],
      prerequisites: [
  "Python basics",
  "SQL"
],
      sources: [
  {
    "url": "https://mlflow.org/docs/latest/python_api/mlflow.data.html",
    "captured_at": "2026-04-10",
    "publisher": "MLflow"
  }
],
      status: "PUBLISHED",
      quizzes: [],
      versions: [],
    },
  ],
};

// DEMO COURSE (catalogue illustration) — web-security
export const courseWebSecurity: Course = {
  id: 3,
  slug: "web-security",
  title: "Modern Web Security & Zero Trust",
  description: "Hands-on web application security aligned with OWASP Top 10 and NIST SP 800-207. Auto-updated when CVEs or spec revisions emerge.",
  subject: "Web Application Security",
  totalLessons: 6,
  authority: "PA1",
  consecutiveAcceptedPublishes: 2,
  real: false,
  lessons: [
    {
      id: 8, slug: "lesson-01-owasp-top10", title: "Lesson 1 \u2014 OWASP Top 10 (2025 Edition)",
      version: 3,
      body: "## OWASP Top 10 — 2025\n\nThe OWASP Top 10 is the de facto standard for web application security risks.\n\n> **2025 Update:** A01 has shifted from Broken Access Control to **Injection** in the 2025 revision, reflecting the rise of LLM prompt injection as a primary attack vector alongside classic SQL injection.\n\n### A01 — Injection\n\nInjection attacks occur when untrusted data is sent to an interpreter as part of a command or query.\n\n**Mitigation:** Use parameterised queries, ORMs, and input validation at the schema level.\n\n*Sources verified 2026-04-15 · Lesson v3 · Confidence 0.93*",
      objectives: [
  "List the OWASP Top 10 2025 risks in order",
  "Explain the A01 mitigation strategy"
],
      prerequisites: [
  "HTTP basics"
],
      sources: [
  {
    "url": "https://owasp.org/www-project-top-ten/",
    "captured_at": "2026-04-15",
    "publisher": "OWASP"
  }
],
      status: "PUBLISHED",
      quizzes: [],
      versions: [],
    },
  ],
};

export const catalogCourses = [courseAgentOps, courseMlEngineering, courseWebSecurity];

// The repo's one REAL course, still exported under the name other views expect.
export const courseAgentOpsNew = courseAgentOps;