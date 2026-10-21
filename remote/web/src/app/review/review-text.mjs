const secretAssignment = /((?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd|secret|token|authorization|cookie|session[_-]?id)\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;]+)/gi;

/** @param {string} value */
export function redactReviewText(value) {
  return value
    .replace(/-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/gi, "[REDACTED PRIVATE KEY]")
    .replace(/(\bBearer\s+)[A-Za-z0-9._~+\/-]+=*/gi, "$1[REDACTED]")
    .replace(/(\bBasic\s+)[A-Za-z0-9+/]+=*/gi, "$1[REDACTED]")
    .replace(/\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|ASIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|npm_[A-Za-z0-9]{20,}|glpat-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{35})\b/g, "[REDACTED TOKEN]")
    .replace(/\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g, "[REDACTED TOKEN]")
    .replace(/(https?:\/\/)[^\s/@:]+:[^\s/@]+@/gi, "$1[REDACTED]@")
    .replace(secretAssignment, "$1[REDACTED]");
}
