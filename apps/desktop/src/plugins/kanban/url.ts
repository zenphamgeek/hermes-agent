// kanban/url.ts
// Strict URL scheme sanitization for Kanban cards to prevent stored XSS (CWE-79) and reverse tabnabbing (CWE-1022).

const SAFE_SCHEMES = new Set(['http:', 'https:', 'mailto:'])
const DANGEROUS_SCHEMES_REGEX = /^\s*(javascript|data|vbscript|blob|file):/i

/**
 * Returns a safe absolute URL string, or null if the input is unsafe, malformed,
 * or using a dangerous URI scheme (e.g. javascript:, data:, vbscript:, java%73cript:).
 */
export function sanitizeCardUrl(raw: string | null | undefined): string | null {
  if (!raw || typeof raw !== 'string') return null
  const trimmed = raw.trim()
  if (!trimmed) return null

  // Fast-path guard against raw whitespace and control characters
  if (/[\u0000-\u001F\u007F-\u009F]/.test(trimmed)) {
    return null
  }

  // Guard against percent-encoded control characters or null bytes
  if (/%0[0-8b-f]|%1[0-9a-f]|%7f/i.test(trimmed)) {
    return null
  }

  // Multi-pass URL decoding check to prevent single and double encoding bypasses (e.g. java%73cript:, %6a%61%76%61...)
  let decoded = trimmed
  for (let pass = 0; pass < 2; pass++) {
    try {
      const nextDecoded = decodeURIComponent(decoded)
      if (nextDecoded === decoded) break
      decoded = nextDecoded
    } catch {
      // Malformed percent-encoding
      return null
    }
  }

  if (DANGEROUS_SCHEMES_REGEX.test(decoded)) {
    return null
  }

  let parsed: URL
  try {
    // Parse strictly as an absolute URL to avoid turning relative paths into localhost links
    parsed = new URL(trimmed)
  } catch {
    return null
  }

  // URL.protocol is lowercased by the WHATWG URL constructor
  return SAFE_SCHEMES.has(parsed.protocol) ? parsed.toString() : null
}

