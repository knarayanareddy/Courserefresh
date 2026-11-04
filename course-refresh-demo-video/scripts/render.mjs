import { spawn } from "node:child_process";
import { copyFile, mkdir, symlink, unlink } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import chromium, { inflate } from "@sparticuz/chromium";

const here = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const binaryDir = path.join(here, ".remotion-binaries");
const outputDir = path.join(here, "output");
const videoOnly = path.join(outputDir, ".courserefresh-video-only.mp4");
const outputFile = path.join(outputDir, "courserefresh-demo-3min.mp4");
const narration = path.join(here, "public/audio/courserefresh-narration.mp3");
const pagesCopy = path.resolve(here, "../viz/public/courserefresh-demo-3min.mp4");
const ffmpeg = path.join(here, "node_modules/@ffmpeg-installer/linux-x64/ffmpeg");
const ffprobe = path.join(here, "node_modules/@ffprobe-installer/linux-x64/ffprobe");

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

await mkdir(binaryDir, { recursive: true });
await mkdir(outputDir, { recursive: true });
await mkdir(path.dirname(pagesCopy), { recursive: true });
await run(process.execPath, [path.join(here, "scripts/prepare-narration.mjs")]);
for (const [name, target] of [["ffmpeg", ffmpeg], ["ffprobe", ffprobe]]) {
  const link = path.join(binaryDir, name);
  try {
    await symlink(target, link);
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
  }
}
const browser = await chromium.executablePath();
// Load the compatibility libraries packaged beside Chromium on this Debian render host.
const libraryPath = "/tmp/al2023/lib";
await inflate(path.join(here, "node_modules/@sparticuz/chromium/bin/al2023.tar.br"));
process.env.LD_LIBRARY_PATH = [libraryPath, process.env.LD_LIBRARY_PATH].filter(Boolean).join(":");
process.env.FONTCONFIG_PATH ??= "/tmp/fonts";

try {
  await run(path.join(here, "node_modules/.bin/remotion"), [
    "render", "src/remotion-entry.tsx", "CourserefreshDemo", videoOnly,
    "--browser-executable", browser,
    "--binaries-directory", binaryDir,
    "--codec", "h264",
    "--crf", "18",
    "--x264-preset", "medium",
    "--concurrency", "2",
    "--overwrite",
    "--log", "info",
  ]);
  // Keep only the narration: no music bed or background effects in the final film.
  await run(binaryDir + "/ffmpeg", [
    "-hide_banner", "-loglevel", "warning", "-y",
    "-i", videoOnly,
    "-i", narration,
    "-map", "0:v:0", "-map", "1:a:0",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-t", "180", "-movflags", "+faststart", outputFile,
  ]);
  await copyFile(outputFile, pagesCopy);
  await unlink(videoOnly);
  console.log(`\nFinished: ${outputFile}`);
  console.log(`GitHub Pages video asset: ${pagesCopy}`);
} catch (error) {
  console.error(error);
  process.exitCode = 1;
}
