import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ffmpeg = path.join(here, "node_modules/@ffmpeg-installer/linux-x64/ffmpeg");
const ffprobe = path.join(here, "node_modules/@ffprobe-installer/linux-x64/ffprobe");
const audioDir = path.join(here, "public/audio");
const partsDir = path.join(here, "output/narration-parts");
const merged = path.join(audioDir, "courserefresh-narration.mp3");
const sceneCount = 8;
const tempo = 1.203;
const gapSeconds = 0.35;

function run(command, args, cwd = here) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd, stdio: "inherit" });
    child.once("error", reject);
    child.once("exit", (code, signal) => {
      if (signal) reject(new Error(`${command} stopped by ${signal}`));
      else if (code !== 0) reject(new Error(`${command} exited with ${code}`));
      else resolve();
    });
  });
}

function capture(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd: here, stdio: ["ignore", "pipe", "inherit"] });
    let stdout = "";
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.once("error", reject);
    child.once("exit", (code) => code === 0 ? resolve(stdout.trim()) : reject(new Error(`${command} exited with ${code}`)));
  });
}

await mkdir(partsDir, { recursive: true });
const parts = [];
const durations = [];
for (let i = 0; i < sceneCount; i++) {
  const input = path.join(audioDir, `narration-${String(i + 1).padStart(2, "0")}.mp3`);
  const part = path.join(partsDir, `part-${String(i + 1).padStart(2, "0")}.wav`);
  await run(ffmpeg, [
    "-hide_banner", "-loglevel", "error", "-y", "-i", input,
    "-af", `atempo=${tempo},aresample=48000`, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", part,
  ]);
  const seconds = Number(await capture(ffprobe, ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", part]));
  parts.push(part);
  durations.push(seconds);
}

const silence = path.join(partsDir, "chapter-pause.wav");
await run(ffmpeg, [
  "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
  "-t", String(gapSeconds), "-c:a", "pcm_s16le", silence,
]);
const concatInputs = [];
const concatArgs = [];
for (let i = 0; i < sceneCount; i++) {
  concatArgs.push("-i", parts[i]);
  concatInputs.push(`[${i}:a]`);
  if (i < sceneCount - 1) {
    concatArgs.push("-i", silence);
    concatInputs.push(`[${sceneCount + i}:a]`);
  }
}
const concatFilter = `${concatInputs.join("")}concat=n=${concatInputs.length}:v=0:a=1[out]`;
await run(ffmpeg, [
  "-hide_banner", "-loglevel", "error", "-y", ...concatArgs,
  "-filter_complex", concatFilter, "-map", "[out]", "-codec:a", "libmp3lame", "-b:a", "160k", merged,
]);
const totalSeconds = Number(await capture(ffprobe, ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", merged]));
if (totalSeconds > 180) throw new Error(`Narration is ${totalSeconds.toFixed(2)} s; shorten it before rendering.`);
const chapterSeconds = durations.map((duration, index) => duration + (index < sceneCount - 1 ? gapSeconds : 0));
await writeFile(
  path.join(here, "src/remotion/narration-timing.json"),
  `${JSON.stringify({ tempo, gapSeconds, durations, chapterSeconds, totalSeconds }, null, 2)}\n`,
);
console.log(`Narration prepared: ${totalSeconds.toFixed(2)} s, 8 chapters, tempo ${tempo}x.`);
