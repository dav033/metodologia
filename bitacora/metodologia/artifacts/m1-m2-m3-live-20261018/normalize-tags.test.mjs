import assert from "node:assert/strict";
import { test } from "node:test";

import { normalizeTags } from "./normalize-tags.mjs";

test("trims and lowercases tags", () => {
  assert.deepEqual(normalizeTags(["  Foo ", "BAR"]), ["foo", "bar"]);
});

test("normalizes Unicode to NFC", () => {
  const decomposed = "Café";
  const [tag] = normalizeTags([decomposed]);
  assert.equal(tag, "café");
  assert.equal(tag, tag.normalize("NFC"));
});

test("deduplicates canonically equivalent tags", () => {
  assert.deepEqual(normalizeTags(["café", "CAFÉ"]), ["café"]);
});

test("discards empty and whitespace-only tags", () => {
  assert.deepEqual(normalizeTags(["", "   ", "\t\n", "a"]), ["a"]);
});

test("deduplicates preserving first-seen order", () => {
  assert.deepEqual(normalizeTags(["b", "A", "B", "a", "c"]), ["b", "a", "c"]);
});

test("returns an empty array for an empty input", () => {
  assert.deepEqual(normalizeTags([]), []);
});

test("does not mutate the input and returns a new array", () => {
  const input = [" A ", "a", ""];
  const snapshot = [...input];
  const result = normalizeTags(input);
  assert.deepEqual(input, snapshot);
  assert.notEqual(result, input);
});

test("throws TypeError when input is not an array", () => {
  for (const bad of [undefined, null, "a", 1, {}, new Set(["a"]), { length: 0 }]) {
    assert.throws(() => normalizeTags(bad), TypeError);
  }
});

test("throws TypeError when any element is not a string", () => {
  for (const bad of [1, null, undefined, {}, ["a"], Symbol("x"), new String("a")]) {
    assert.throws(() => normalizeTags(["ok", bad]), TypeError);
  }
});

test("throws TypeError for sparse arrays", () => {
  // eslint-disable-next-line no-sparse-arrays
  assert.throws(() => normalizeTags(["a", , "b"]), TypeError);
});
