import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { redactReviewText } from "../src/app/review/review-text.mjs";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFile(join(root, path), "utf8");

test("failure review renders its four sections from the fixture", async () => {
  const page = await read("src/app/review/page.tsx");
  const fixture = await read("src/app/review/review-fixture.ts");
  for (const section of ["Causa", "Salida de verificación", "Estadística del diff", "Final del log"]) {
    assert.match(page, new RegExp(`title="${section}"`));
  }
  for (const field of ["cause", "verificationOutput", "diffStat", "logTail"]) {
    assert.match(page, new RegExp(`reviewFixture\\.${field}`));
    assert.match(fixture, new RegExp(`${field}:`));
  }
});

test("long review output scrolls inside a bounded panel", async () => {
  const css = await read("src/app/review/review.module.css");
  assert.match(css, /\.output\s*\{[^}]*max-height:\s*210px/s);
  assert.match(css, /\.output\s*\{[^}]*overflow:\s*auto/s);
  assert.match(css, /\.output\s*\{[^}]*overscroll-behavior:\s*contain/s);
});

test("review text redacts credentials, tokens and private keys", () => {
  const output = redactReviewText([
    "Authorization: Bearer abc.def.ghi",
    "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz123456",
    "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456",
    "password='my-secret-value'",
    "https://user:pass@example.test/path",
    "-----BEGIN PRIVATE KEY-----\\nprivate-material\\n-----END PRIVATE KEY-----",
  ].join("\\n"));

  assert.doesNotMatch(output, /abc\.def\.ghi|ghp_abcdefghijklmnopqrstuvwxyz123456|sk-abcdefghijklmnopqrstuvwxyz123456|my-secret-value|user:pass|private-material/);
  assert.match(output, /\[REDACTED/);
});
