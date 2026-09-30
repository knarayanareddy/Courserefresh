import { useCallback, useEffect, useMemo, useRef, useState, type ComponentType } from "react";
import {
  Captions,
  Maximize,
  Minimize,
  Pause,
  Play,
  RotateCcw,
  Settings2,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
} from "lucide-react";
import {
  INTRO_MS,
  LINE_GAP_MS,
  SCENES,
  SCENE_GAP_MS,
  estLineMs,
  estSceneMs,
  fmt,
} from "./script";
import { Cs101, Intro, Notice, Opening, Overload, LogoMark } from "./scenesA";
import { Act, Close, Control, Decide, Digest, Learners } from "./scenesB";
import type { SceneProps } from "./ui";

const VISUALS: Record<string, ComponentType<SceneProps>> = {
  open: Opening,
  overwhelm: Overload,
  cs101: Cs101,
  intro: Intro,
  notice: Notice,
  decide: Decide,
  act: Act,
  learners: Learners,
  trust: Control,
  digest: Digest,
  close: Close,
};

/* ───────────── voices ───────────── */
const PREFERRED: RegExp[] = [
  /samantha/i,
  /\bava\b/i,
  /allison/i,
  /serena/i,
  /zoe/i,
  /(aria|jenny|sonia|libby).*(online|natural)/i,
  /google uk english female/i,
  /google us english/i,
  /karen|moira|tessa|susan|victoria/i,
];

function scoreVoice(v: SpeechSynthesisVoice) {
  let s = 0;
  if (!/^en[-_]/i.test(v.lang)) return -1;
  if (/^en[-_](US|GB|AU|IE|CA)/i.test(v.lang)) s += 5;
  const idx = PREFERRED.findIndex((r) => r.test(v.name));
  if (idx >= 0) s += 40 - idx * 3;
  if (/premium|enhanced|natural|neural|online/i.test(v.name)) s += 25;
  if (/compact|espeak|novelty|bad news|bells|boing|cellos|albert|fred|junior|ralph|whisper|zarvox|trinoids|organ|wobble|jester|superstar|good news|bubbles/i.test(v.name)) s -= 100;
  if (/male/i.test(v.name) && !/female/i.test(v.name)) s -= 2;
  return s;
}

function useVoices() {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const load = () => setVoices(window.speechSynthesis.getVoices());
    load();
    window.speechSynthesis.addEventListener("voiceschanged", load);
    return () => window.speechSynthesis.removeEventListener("voiceschanged", load);
  }, []);
  return useMemo(
    () =>
      voices
        .map((v) => ({ v, s: scoreVoice(v) }))
        .filter((x) => x.s >= 0)
        .sort((a, b) => b.s - a.s)
        .map((x) => x.v),
    [voices]
  );
}

// Keep a reference so utterances are not garbage-collected mid-speech (Chrome bug).
const speechRef: { u: SpeechSynthesisUtterance | null } = { u: null };

const SPEECH_OK = typeof window !== "undefined" && "speechSynthesis" in window;

export default function App() {
  const voices = useVoices();
  const [voiceURI, setVoiceURI] = useState("");
  const voice = useMemo(
    () => voices.find((v) => v.voiceURI === voiceURI) ?? voices[0] ?? null,
    [voices, voiceURI]
  );

  const [started, setStarted] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [ended, setEnded] = useState(false);
  const [sceneIdx, setSceneIdx] = useState(0);
  const [step, setStep] = useState(-1);
  const [muted, setMuted] = useState(false);
  const [captionsOn, setCaptionsOn] = useState(true);
  const [rate, setRate] = useState(0.95);
  const [elapsed, setElapsed] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [controlsVisible, setControlsVisible] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const [scale, setScale] = useState(1);
  const [leaving, setLeaving] = useState<number | null>(null);
  const prevScene = useRef(0);

  /* stage scaling */
  useEffect(() => {
    const f = () => setScale(Math.min(window.innerWidth / 1920, window.innerHeight / 1080));
    f();
    window.addEventListener("resize", f);
    return () => window.removeEventListener("resize", f);
  }, []);

  /* crossfade bookkeeping */
  useEffect(() => {
    if (prevScene.current !== sceneIdx) {
      setLeaving(prevScene.current);
      prevScene.current = sceneIdx;
      const id = window.setTimeout(() => setLeaving(null), 800);
      return () => window.clearTimeout(id);
    }
  }, [sceneIdx]);

  /* timeline maths (estimated, used for progress + clock) */
  const sceneStarts = useMemo(() => {
    let acc = 0;
    return SCENES.map((s) => {
      const start = acc;
      acc += estSceneMs(s, rate);
      return start;
    });
  }, [rate]);
  const totalMs = useMemo(
    () => SCENES.reduce((a, s) => a + estSceneMs(s, rate), 0),
    [rate]
  );

  /* narration + pacing engine */
  useEffect(() => {
    if (!started || !playing || ended) return;
    let cancelled = false;
    const timers: number[] = [];
    const later = (fn: () => void, ms: number) => {
      timers.push(
        window.setTimeout(() => {
          if (!cancelled) fn();
        }, ms)
      );
    };
    const scene = SCENES[sceneIdx];
    const last = step >= scene.lines.length - 1;

    const advance = () => {
      if (!last) {
        setStep(step + 1);
      } else if (sceneIdx < SCENES.length - 1) {
        setSceneIdx(sceneIdx + 1);
        setStep(-1);
      } else {
        setEnded(true);
        setPlaying(false);
      }
    };

    if (step < 0) {
      later(advance, INTRO_MS);
    } else {
      const line = scene.lines[step];
      const est = estLineMs(line, rate);
      const gap = last ? SCENE_GAP_MS : LINE_GAP_MS;
      let done = false;
      const finish = () => {
        if (done) return;
        done = true;
        later(advance, gap);
      };
      if (!muted && SPEECH_OK && voice) {
        later(() => {
          const synth = window.speechSynthesis;
          synth.cancel();
          const u = new SpeechSynthesisUtterance(line.say ?? line.text);
          u.voice = voice;
          u.lang = voice.lang;
          u.rate = rate;
          u.pitch = 1;
          u.volume = 1;
          u.onend = finish;
          u.onerror = (e) => {
            if (e.error === "canceled" || e.error === "interrupted") return;
            finish();
          };
          speechRef.u = u;
          synth.speak(u);
        }, 60);
        // watchdog in case a voice never fires onend
        later(finish, est * 2.2 + 5000);
      } else {
        later(finish, est + 250);
      }
    }

    return () => {
      cancelled = true;
      timers.forEach((t) => window.clearTimeout(t));
      if (SPEECH_OK) window.speechSynthesis.cancel();
    };
  }, [started, playing, ended, sceneIdx, step, muted, voice, rate]);

  /* clock */
  useEffect(() => {
    if (!started || !playing) return;
    const id = window.setInterval(() => setElapsed((e) => e + 250), 250);
    return () => window.clearInterval(id);
  }, [started, playing]);

  /* position in timeline (0..1) */
  const posMs = useMemo(() => {
    const s = SCENES[sceneIdx];
    let p = sceneStarts[sceneIdx];
    if (ended) return totalMs;
    if (step >= 0) {
      p += INTRO_MS;
      for (let i = 0; i < step; i++) p += estLineMs(s.lines[i], rate) + LINE_GAP_MS;
      p += estLineMs(s.lines[step], rate) * 0.5;
    }
    return p;
  }, [sceneIdx, step, ended, sceneStarts, rate, totalMs]);

  /* actions */
  const goScene = useCallback(
    (i: number) => {
      const n = Math.max(0, Math.min(SCENES.length - 1, i));
      setSceneIdx(n);
      setStep(-1);
      setEnded(false);
      setElapsed(sceneStarts[n]);
      if (started) setPlaying(true);
    },
    [started, sceneStarts]
  );

  const start = useCallback(() => {
    // Unlock speech synthesis inside the user gesture.
    if (SPEECH_OK) {
      window.speechSynthesis.cancel();
      const warm = new SpeechSynthesisUtterance(" ");
      warm.volume = 0;
      window.speechSynthesis.speak(warm);
    }
    setStarted(true);
    setEnded(false);
    setSceneIdx(0);
    setStep(-1);
    setElapsed(0);
    setPlaying(true);
  }, []);

  const toggle = useCallback(() => {
    if (!started || ended) return start();
    setPlaying((p) => !p);
  }, [started, ended, start]);

  const toggleFullscreen = useCallback(() => {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen?.();
  }, []);

  useEffect(() => {
    const f = () => setFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", f);
    return () => document.removeEventListener("fullscreenchange", f);
  }, []);

  /* keyboard */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === "SELECT") return;
      if (e.code === "Space") {
        e.preventDefault();
        toggle();
      } else if (e.key === "ArrowRight") goScene(sceneIdx + 1);
      else if (e.key === "ArrowLeft") goScene(sceneIdx - 1);
      else if (e.key.toLowerCase() === "f") toggleFullscreen();
      else if (e.key.toLowerCase() === "m") setMuted((m) => !m);
      else if (e.key.toLowerCase() === "c") setCaptionsOn((c) => !c);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [toggle, goScene, sceneIdx, toggleFullscreen]);

  /* auto-hide controls */
  const hideTimer = useRef<number | undefined>(undefined);
  const poke = useCallback(() => {
    setControlsVisible(true);
    window.clearTimeout(hideTimer.current);
    hideTimer.current = window.setTimeout(() => setControlsVisible(false), 2800);
  }, []);
  useEffect(() => {
    poke();
    return () => window.clearTimeout(hideTimer.current);
  }, [poke]);

  const showControls = controlsVisible || !playing || showSettings;
  const Current = VISUALS[SCENES[sceneIdx].id];
  const LeavingVisual = leaving !== null ? VISUALS[SCENES[leaving].id] : null;
  const scene = SCENES[sceneIdx];
  const caption = step >= 0 ? scene.lines[step]?.text : "";
  const sceneProgress = (i: number) => {
    if (i < sceneIdx || (ended && i <= sceneIdx)) return 100;
    if (i > sceneIdx) return 0;
    const s = SCENES[i];
    const dur = estSceneMs(s, rate);
    return Math.min(100, ((posMs - sceneStarts[i]) / dur) * 100);
  };

  return (
    <div
      className="relative h-full w-full select-none overflow-hidden bg-black"
      onMouseMove={poke}
      onClick={() => showSettings && setShowSettings(false)}
      style={{ cursor: showControls ? "default" : "none" }}
    >
      {/* ───────── 1920×1080 stage ───────── */}
      <div
        className="absolute left-1/2 top-1/2 overflow-hidden bg-black"
        style={{
          width: 1920,
          height: 1080,
          transform: `translate(-50%, -50%) scale(${scale})`,
          transformOrigin: "center",
        }}
      >
        {/* aurora */}
        <div className="aurora" style={{ filter: `hue-rotate(${scene.hue}deg)` }}>
          <div className="blob" style={{ left: "18%", top: "12%", width: 900, height: 900, background: "#0a84ff", animation: "drift-a 26s ease-in-out infinite" }} />
          <div className="blob" style={{ left: "52%", top: "30%", width: 800, height: 800, background: "#8e44ff", animation: "drift-b 32s ease-in-out infinite" }} />
          <div className="blob" style={{ left: "30%", top: "58%", width: 700, height: 700, background: "#ff375f", opacity: 0.32, animation: "drift-c 29s ease-in-out infinite" }} />
        </div>
        <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,.35) 0%, rgba(0,0,0,.82) 100%)" }} />

        {/* chrome */}
        <div className="absolute left-[72px] top-[56px] flex items-center gap-4">
          <div className="h-[40px] w-[40px] overflow-hidden rounded-[11px]">
            <LogoMark size={40} />
          </div>
          <span className="text-[30px] font-semibold tracking-tight">Courserefresh</span>
        </div>
        <div className="absolute right-[72px] top-[58px] rounded-full border border-white/10 bg-white/[0.06] px-6 py-2 text-[22px] font-medium text-[var(--ink-2)] backdrop-blur-xl">
          Illustrative walkthrough · Introduction to CS 101
        </div>

        {/* scenes */}
        {started && (
          <>
            {LeavingVisual && leaving !== null && (
              <div key={`out-${leaving}`} className="scene-out absolute bottom-[230px] left-[120px] right-[120px] top-[130px]">
                <LeavingVisual step={SCENES[leaving].lines.length - 1} />
              </div>
            )}
            <div key={`in-${sceneIdx}`} className="scene-in absolute bottom-[230px] left-[120px] right-[120px] top-[130px]">
              <Current step={step} />
            </div>
          </>
        )}

        {/* captions */}
        {started && captionsOn && caption && (
          <div className="pointer-events-none absolute inset-x-0 bottom-[78px] flex justify-center px-[160px]">
            <div
              key={`${sceneIdx}-${step}`}
              className="caption-in max-w-[1500px] rounded-[30px] bg-black/45 px-12 py-6 text-center text-[42px] font-medium leading-[1.25] tracking-[-0.01em] backdrop-blur-2xl"
              style={{ border: "1px solid rgba(255,255,255,.08)", textShadow: "0 2px 12px rgba(0,0,0,.5)" }}
            >
              {caption}
            </div>
          </div>
        )}
      </div>

      {/* ───────── start screen ───────── */}
      {!started && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-black/30 text-center backdrop-blur-sm">
          <div style={{ transform: `scale(${Math.max(0.55, Math.min(1, scale * 1.4))})` }} className="flex flex-col items-center">
            <div className="scene-in">
              <LogoMark size={132} />
            </div>
            <h1 className="scene-in mt-8 text-[84px] font-semibold leading-none tracking-[-0.04em]">Courserefresh</h1>
            <p className="scene-in mt-5 max-w-[760px] text-[30px] leading-snug text-[var(--ink-2)]">
              A demo for the professors who never have time to refresh their courses.
            </p>
            <button
              onClick={start}
              className="mt-12 flex items-center gap-4 rounded-full bg-white px-12 py-5 text-[28px] font-semibold text-black shadow-[0_20px_60px_-10px_rgba(255,255,255,.35)] transition hover:scale-[1.03] active:scale-[0.98]"
            >
              <Play size={30} fill="black" /> Play demo
            </button>
            <div className="mt-8 text-[20px] text-[var(--ink-3)]">
              About 2 min 45 s · Narrated — turn your sound on
              {SPEECH_OK && voice ? ` · Voice: ${voice.name}` : ""}
            </div>
            {!SPEECH_OK && (
              <div className="mt-3 text-[18px] text-[var(--orange)]">
                This browser has no speech synthesis — captions will play on their own.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ───────── controls ───────── */}
      {started && (
        <div
          className="absolute inset-x-0 bottom-6 z-30 flex justify-center px-6 transition-all duration-500"
          style={{
            opacity: showControls ? 1 : 0,
            transform: showControls ? "none" : "translateY(14px)",
            pointerEvents: showControls ? "auto" : "none",
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="glass relative flex w-full max-w-[980px] flex-col gap-3 rounded-[26px] px-5 py-3.5">
            {/* segmented progress */}
            <div className="flex gap-[5px]">
              {SCENES.map((s, i) => (
                <button
                  key={s.id}
                  title={s.label}
                  onClick={() => goScene(i)}
                  className="group relative h-[14px] flex-1 cursor-pointer"
                  style={{ flexGrow: estSceneMs(s, rate) }}
                >
                  <span className="absolute inset-x-0 top-[5px] h-[4px] overflow-hidden rounded-full bg-white/15 transition-all group-hover:top-[3px] group-hover:h-[8px]">
                    <span
                      className="block h-full rounded-full bg-white"
                      style={{ width: `${sceneProgress(i)}%`, transition: "width 700ms linear" }}
                    />
                  </span>
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1.5 text-white">
              <IconBtn label="Previous scene" onClick={() => goScene(sceneIdx - 1)}>
                <SkipBack size={20} />
              </IconBtn>
              <IconBtn label={ended ? "Replay" : playing ? "Pause" : "Play"} onClick={toggle} big>
                {ended ? <RotateCcw size={22} /> : playing ? <Pause size={22} fill="white" /> : <Play size={22} fill="white" />}
              </IconBtn>
              <IconBtn label="Next scene" onClick={() => goScene(sceneIdx + 1)}>
                <SkipForward size={20} />
              </IconBtn>

              <div className="mono ml-3 text-[13px] tabular-nums text-white/70">
                {fmt(Math.min(elapsed, totalMs * 1.2))} <span className="text-white/35">/ ~{fmt(totalMs)}</span>
              </div>
              <div className="ml-4 hidden truncate text-[14px] font-medium text-white/85 sm:block">
                {String(sceneIdx + 1).padStart(2, "0")} · {scene.label}
              </div>

              <div className="ml-auto flex items-center gap-1">
                <IconBtn label="Captions (C)" onClick={() => setCaptionsOn((c) => !c)} active={captionsOn}>
                  <Captions size={21} />
                </IconBtn>
                <IconBtn label="Mute narration (M)" onClick={() => setMuted((m) => !m)}>
                  {muted ? <VolumeX size={21} /> : <Volume2 size={21} />}
                </IconBtn>
                <IconBtn label="Voice & speed" onClick={() => setShowSettings((s) => !s)} active={showSettings}>
                  <Settings2 size={21} />
                </IconBtn>
                <IconBtn label="Fullscreen (F)" onClick={toggleFullscreen}>
                  {fullscreen ? <Minimize size={21} /> : <Maximize size={21} />}
                </IconBtn>
              </div>
            </div>

            {showSettings && (
              <div className="glass absolute bottom-[calc(100%+12px)] right-0 w-[360px] rounded-[22px] p-5 text-[14px]">
                <div className="mb-2 font-semibold text-white">Narrator voice</div>
                <select
                  value={voice?.voiceURI ?? ""}
                  onChange={(e) => setVoiceURI(e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-black/50 px-3 py-2.5 text-white outline-none"
                >
                  {voices.length === 0 && <option value="">System default</option>}
                  {voices.slice(0, 30).map((v) => (
                    <option key={v.voiceURI} value={v.voiceURI}>
                      {v.name} ({v.lang})
                    </option>
                  ))}
                </select>
                <div className="mb-1 mt-5 flex items-center justify-between font-semibold text-white">
                  Pace <span className="mono font-normal text-white/60">{rate.toFixed(2)}×</span>
                </div>
                <input
                  type="range"
                  min={0.8}
                  max={1.1}
                  step={0.01}
                  value={rate}
                  onChange={(e) => setRate(parseFloat(e.target.value))}
                  className="w-full"
                />
                <p className="mt-3 text-[12px] leading-snug text-white/50">
                  Tip: on Mac or iPhone, choose “Samantha” or an Enhanced/Premium voice. On Windows, pick a “Natural” voice in Edge.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function IconBtn({
  children,
  label,
  onClick,
  big,
  active,
}: {
  children: React.ReactNode;
  label: string;
  onClick: () => void;
  big?: boolean;
  active?: boolean;
}) {
  return (
    <button
      aria-label={label}
      title={label}
      onClick={onClick}
      className={`flex items-center justify-center rounded-full transition hover:bg-white/15 active:scale-95 ${
        big ? "h-11 w-11" : "h-9 w-9"
      } ${active ? "bg-white/15" : ""}`}
    >
      {children}
    </button>
  );
}
