import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const start = html.indexOf("const STEPS = ");
const end = html.indexOf("\n    const $ = (id)", start);
if (start < 0 || end < 0) {
  throw new Error("Could not find STEPS in index.html");
}
const STEPS = eval(html.slice(start, end).replace("const STEPS = ", "").trim().replace(/;$/, ""));

function stepSpeech(step) {
  const parts = [];
  if (step.lead) parts.push(step.lead);
  for (const block of step.blocks || []) {
    if (block.vars?.length) {
      parts.push("Here is what each symbol means.");
      for (const item of block.vars) {
        parts.push(`${item.say} means ${item.meaning}.`);
      }
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

async function googleTTS(text) {
  const url = `https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=en-US&q=${encodeURIComponent(text)}`;
  const res = await fetch(url, {
    headers: {
      "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
      Accept: "audio/mpeg,audio/webm,audio/*;q=0.9,*/*;q=0.8",
      Referer: "https://translate.google.com/"
    }
  });
  if (!res.ok) {
    throw new Error(`TTS HTTP ${res.status} for: ${text.slice(0, 80)}`);
  }
  const buf = Buffer.from(await res.arrayBuffer());
  if (buf.length < 500) {
    throw new Error(`TTS returned too little audio (${buf.length} bytes)`);
  }
  return buf;
}

const audioDir = path.join(root, "audio");
fs.mkdirSync(audioDir, { recursive: true });
const manifest = [];

for (let i = 0; i < STEPS.length; i += 1) {
  const text = stepSpeech(STEPS[i]);
  const parts = chunks(text);
  const buffers = [];
  console.log(`Step ${i + 1}: ${parts.length} clip(s), ${text.split(/\s+/).length} words`);
  for (const part of parts) {
    buffers.push(await googleTTS(part));
    await new Promise((r) => setTimeout(r, 250));
  }
  const file = `step-${String(i + 1).padStart(2, "0")}.mp3`;
  fs.writeFileSync(path.join(audioDir, file), Buffer.concat(buffers));
  manifest.push({ file, title: STEPS[i].title, words: text.split(/\s+/).length });
}

fs.writeFileSync(path.join(audioDir, "manifest.json"), JSON.stringify(manifest, null, 2));
console.log("Wrote", manifest.length, "mp3 files to", audioDir);
