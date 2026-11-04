import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import chromium, { inflate } from "@sparticuz/chromium";

const here = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const command = process.argv[2];
if (!new Set(["studio", "compositions"]).has(command)) throw new Error("Use studio or compositions.");
const browser = await chromium.executablePath();
const libraryPath = "/tmp/al2023/lib";
await inflate(path.join(here, "node_modules/@sparticuz/chromium/bin/al2023.tar.br"));
process.env.LD_LIBRARY_PATH = [libraryPath, process.env.LD_LIBRARY_PATH].filter(Boolean).join(":");
process.env.FONTCONFIG_PATH ??= "/tmp/fonts";
const cli = path.join(here, "node_modules/.bin/remotion");
const args = [command, "src/remotion-entry.tsx", "--browser-executable", browser];
if (command === "studio") args.push("--no-open");
const child = spawn(cli, args, { cwd: here, stdio: "inherit" });
child.once("error", (error) => { console.error(error); process.exitCode = 1; });
child.once("exit", (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  else process.exitCode = code ?? 1;
});
