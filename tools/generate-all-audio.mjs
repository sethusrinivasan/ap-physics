import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CONCURRENCY = Number(process.env.TTS_CONCURRENCY || 6);
const FORCE = process.env.TTS_FORCE === "1";
const ONLY_FIRST = process.env.TTS_ONLY_FIRST === "1";
const KEEP = new Set([1, 2, 4, 5].map((n) => `unit2-q${n}`));

function loadSteps(htmlPath) {
  const html = fs.readFileSync(htmlPath, "utf8");
  const start = html.indexOf("const STEPS = ");
  const end = html.indexOf("\n    const $ = (id)", start);
  if (start < 0 || end < 0) throw new Error(`Could not find STEPS in ${htmlPath}`);
  return eval(html.slice(start, end).replace("const STEPS = ", "").trim().replace(/;$/, ""));
}

function stepSpeech(step) {
  const parts = [];
  if (step.lead) parts.push(step.lead);
  for (const block of step.blocks || []) {
    if (block.vars?.length) {
      parts.push("Here is what each symbol means.");
      for (const item of block.vars) parts.push(`${item.say} means ${item.meaning}.`);
    }
    if (block.explain) parts.push(block.explain);
    if (block.speakFormula) parts.push(block.speakFormula);
  }
  return parts.join(" ");
}

function chunks(text, max = 150) {
  text = String(text).replace(/[’‘]/g, "'").replace(/[“”]/g, '"');
  const sentences = text.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [text];
  const out = [];
  let cur = "";
  const pushWords = (s) => {
    const words = s.split(/\s+/);
    let piece = "";
    for (const w of words) {
      const next = piece ? `${piece} ${w}` : w;
      if (next.length > max && piece) {
        out.push(piece);
        piece = w;
      } else piece = next;
    }
    if (piece) out.push(piece);
  };
  for (const raw of sentences) {
    const s = raw.trim();
    if (!s) continue;
    if (s.length > max) {
      if (cur) {
        out.push(cur);
        cur = "";
      }
      pushWords(s);
      continue;
    }
    if (!cur) {
      cur = s;
      continue;
    }
    const next = `${cur} ${s}`;
    if (next.length <= max) cur = next;
    else {
      out.push(cur);
      cur = s;
    }
  }
  if (cur) out.push(cur);
  return out;
}

async function googleTTS(text, attempt = 1) {
  const url = `https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=en-US&q=${encodeURIComponent(text)}`;
  try {
    const res = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        Accept: "audio/mpeg,audio/webm,audio/*;q=0.9,*/*;q=0.8",
        Referer: "https://translate.google.com/"
      }
    });
    if (!res.ok) {
      if (attempt < 5) {
        await new Promise((r) => setTimeout(r, 500 * attempt));
        return googleTTS(text, attempt + 1);
      }
      throw new Error(`TTS HTTP ${res.status} for: ${text.slice(0, 80)}`);
    }
    const buf = Buffer.from(await res.arrayBuffer());
    if (buf.length < 500) throw new Error(`TTS too small (${buf.length})`);
    return buf;
  } catch (err) {
    if (attempt < 5) {
      await new Promise((r) => setTimeout(r, 600 * attempt));
      return googleTTS(text, attempt + 1);
    }
    throw err;
  }
}

function problemDirs() {
  return fs.readdirSync(ROOT)
    .filter((name) => /^unit2-q\d+$/.test(name))
    .sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]))
    .map((name) => path.join(ROOT, name));
}

function complete(dir, stepCount) {
  if (FORCE && !KEEP.has(path.basename(dir))) return false;
  const audio = path.join(dir, "audio");
  if (!fs.existsSync(audio)) return false;
  for (let i = 1; i <= stepCount; i += 1) {
    const f = path.join(audio, `step-${String(i).padStart(2, "0")}.mp3`);
    if (!fs.existsSync(f) || fs.statSync(f).size < 800) return false;
  }
  return true;
}

async function writeStepAudio(audioDir, i, step) {
  const text = stepSpeech(step);
  const parts = chunks(text);
  const buffers = [];
  for (const part of parts) {
    buffers.push(await googleTTS(part));
    await new Promise((r) => setTimeout(r, 120));
  }
  const file = `step-${String(i + 1).padStart(2, "0")}.mp3`;
  fs.writeFileSync(path.join(audioDir, file), Buffer.concat(buffers));
  return { file, title: step.title, words: text.split(/\s+/).length };
}

async function generateOne(dir) {
  const htmlPath = path.join(dir, "index.html");
  const STEPS = loadSteps(htmlPath);
  if (complete(dir, STEPS.length)) {
    return { dir, skipped: true };
  }
  const audioDir = path.join(dir, "audio");
  fs.mkdirSync(audioDir, { recursive: true });
  if (ONLY_FIRST) {
    const manifestPath = path.join(audioDir, "manifest.json");
    let manifest = [];
    if (fs.existsSync(manifestPath)) {
      try { manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8")); } catch { manifest = []; }
    }
    manifest[0] = await writeStepAudio(audioDir, 0, STEPS[0]);
    while (manifest.length > STEPS.length) manifest.pop();
    for (let extra = STEPS.length + 1; extra <= 12; extra += 1) {
      const leftover = path.join(audioDir, `step-${String(extra).padStart(2, "0")}.mp3`);
      if (fs.existsSync(leftover)) fs.unlinkSync(leftover);
    }
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
    return { dir, skipped: false, steps: STEPS.length, onlyFirst: true };
  }
  const manifest = [];
  for (let i = 0; i < STEPS.length; i += 1) {
    manifest.push(await writeStepAudio(audioDir, i, STEPS[i]));
  }
  fs.writeFileSync(path.join(audioDir, "manifest.json"), JSON.stringify(manifest, null, 2));
  return { dir, skipped: false, steps: STEPS.length };
}

async function pool(items, limit, worker) {
  const pending = new Set();
  const results = [];
  for (const item of items) {
    const job = Promise.resolve()
      .then(() => worker(item))
      .then((res) => {
        pending.delete(job);
        return res;
      });
    pending.add(job);
    results.push(job);
    if (pending.size >= limit) await Promise.race(pending);
  }
  return Promise.all(results);
}

const dirs = problemDirs();
console.log(`Audio jobs: ${dirs.length} problems, concurrency ${CONCURRENCY}`);
const results = await pool(dirs, CONCURRENCY, async (dir) => {
  const name = path.basename(dir);
  try {
    const res = await generateOne(dir);
    console.log(res.skipped ? `skip ${name}` : `ok   ${name} (${res.steps} steps)`);
    return res;
  } catch (err) {
    console.error(`FAIL ${name}: ${err.message}`);
    return { dir, error: err.message };
  }
});
const failed = results.filter((r) => r.error);
const made = results.filter((r) => r.skipped === false);
console.log(`Done. wrote ${made.length}, skipped ${results.length - made.length - failed.length}, failed ${failed.length}`);
if (failed.length) process.exit(1);
