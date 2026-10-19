/**
 * Normalizes a list of tags: trim, Unicode NFC, lowercase, drop empties,
 * deduplicate preserving first-seen order. Never mutates the input.
 *
 * @param {string[]} values
 * @returns {string[]}
 * @throws {TypeError} when `values` is not an array of strings (sparse arrays included).
 */
export function normalizeTags(values) {
  if (!Array.isArray(values)) {
    throw new TypeError("normalizeTags expects an array of strings");
  }

  const seen = new Set();
  for (let i = 0; i < values.length; i += 1) {
    if (!(i in values) || typeof values[i] !== "string") {
      throw new TypeError(`normalizeTags: element at index ${i} is not a string`);
    }
    const tag = values[i].trim().normalize("NFC").toLowerCase().normalize("NFC");
    if (tag !== "") seen.add(tag);
  }
  return [...seen];
}
