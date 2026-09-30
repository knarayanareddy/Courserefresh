export type Line = { text: string; say?: string };
export type SceneDef = {
  id: string;
  label: string;
  hue: number;
  lines: Line[];
};

/**
 * The narration script. Each sentence is one "beat": the visuals advance
 * in lock-step with the voice, so the picture is always in sync with the words,
 * no matter which voice or speed the viewer's device uses.
 */
export const SCENES: SceneDef[] = [
  {
    id: "open",
    label: "The promise",
    hue: 0,
    lines: [
      { text: "Every semester, a professor makes a quiet promise." },
      { text: "That what they teach is still true." },
    ],
  },
  {
    id: "overwhelm",
    label: "The overload",
    hue: 35,
    lines: [
      {
        text: "But professors juggle more than anyone sees: lectures, grading, office hours, committees, research, and an inbox that never empties.",
      },
      { text: "Meanwhile, the subject they teach keeps moving." },
      {
        text: "And refreshing a course, rereading changelogs, rewriting slides, rebuilding quizzes, is always the first thing to slip.",
      },
    ],
  },
  {
    id: "cs101",
    label: "CS 101",
    hue: -20,
    lines: [
      {
        text: "Meet Professor Rivera, and her course: Introduction to Computer Science, CS 101.",
        say: "Meet Professor Rivera, and her course: Introduction to Computer Science, C S, one oh one.",
      },
      { text: "In Lesson Four, students install a package with pip. It worked for years." },
      { text: "Then the ground shifted, and nobody told the syllabus." },
    ],
  },
  {
    id: "intro",
    label: "Courserefresh",
    hue: 10,
    lines: [
      { text: "So we built Courserefresh." },
      {
        text: "A course that watches the thing it teaches, and keeps itself current, so the professor doesn't have to.",
      },
    ],
  },
  {
    id: "notice",
    label: "Notice",
    hue: -40,
    lines: [
      {
        text: "It monitors release notes, documentation, and changelogs, fetching real pages with Apify, and fingerprinting each one as evidence.",
        say: "It monitors release notes, documentation, and changelogs, fetching real pages with Appify, and fingerprinting each one as evidence.",
      },
      {
        text: "This week, two independent sources reported the same change: pip now refuses to install into the system Python.",
      },
    ],
  },
  {
    id: "decide",
    label: "Decide",
    hue: 60,
    lines: [
      { text: "Then it asks one question: is the course now wrong?" },
      { text: "It never acts on a single source. Two independent sources agree, so this change qualifies." },
      {
        text: "And when a web page tries to trick it into approving an edit, Courserefresh refuses, and shows exactly what it refused.",
      },
    ],
  },
  {
    id: "act",
    label: "Rewrite",
    hue: 20,
    lines: [
      {
        text: "Lesson Four is rewritten to teach virtual environments. The matching quiz question is regenerated too, but held for her approval, because assessments are always human-only.",
      },
      { text: "The change is committed as a new version, with a diff, and a receipt." },
    ],
  },
  {
    id: "learners",
    label: "Learners",
    hue: -10,
    lines: [
      { text: "Students who opted in receive a short note explaining what changed, and why it matters." },
      {
        text: "If a few get stuck on the same step, they get a two-minute micro-lesson, before they ever write to the professor.",
      },
    ],
  },
  {
    id: "trust",
    label: "Control",
    hue: 80,
    lines: [
      {
        text: "Professor Rivera stays in control. She chooses how much authority the system has, and a kill switch freezes everything.",
      },
      {
        text: "At publish time, it states what would prove the change wrong. If results get worse, it reverts itself, openly, as a new version.",
      },
    ],
  },
  {
    id: "digest",
    label: "The morning",
    hue: 120,
    lines: [
      { text: "The next morning, she gets one digest: what changed, what was refused, and what needs her eyes." },
      { text: "A few minutes over coffee, instead of a weekend of rewrites." },
    ],
  },
  {
    id: "close",
    label: "Close",
    hue: 0,
    lines: [
      { text: "And it's verifiable. One command runs two hundred ninety-five checks, with no credentials." },
      { text: "Courserefresh. The course that stays true." },
      { text: "So professors can get back to teaching." },
    ],
  },
];

export const INTRO_MS = 750;
export const LINE_GAP_MS = 420;
export const SCENE_GAP_MS = 520;

export const wordCount = (s: string) => s.trim().split(/\s+/).length;

/** Estimated duration of a spoken line at a given speech rate (ms). */
export const estLineMs = (line: Line, rate: number) => {
  const wps = 2.7 * (rate / 0.95);
  return (wordCount(line.say ?? line.text) / wps) * 1000;
};

export const estSceneMs = (scene: SceneDef, rate: number) =>
  INTRO_MS +
  scene.lines.reduce((a, l) => a + estLineMs(l, rate) + LINE_GAP_MS, 0) +
  SCENE_GAP_MS;

export const fmt = (ms: number) => {
  const s = Math.max(0, Math.round(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};
