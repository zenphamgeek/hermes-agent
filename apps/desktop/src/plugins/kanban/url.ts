// kanban/url.ts
// Strict URL scheme sanitization for Kanban cards to prevent stored XSS (CWE-79) and reverse tabnabbing (CWE-1022).

const SAFE_SCHEMES = new Set(['http:', 'https:', 'mailto:'])

/**
 * Returns a safe absolute URL string, or null if the input is unsafe, malformed,
 * or using a dangerous URI scheme (e.g. javascript:, data:, vbscript:).
 */
export function sanitizeCardUrl(raw: string | null | undefined): string | null {
  if (!raw || typeof raw !== 'string') return null
  const trimmed = raw.trim()
  if (!trimmed) return null

  // Fast-path guard against whitespace and control characters in schemes
  if (/[\u0000-\u001F\u007F-\u009F]/.test(trimmed)) {
    return null
  }

  let parsed: URL
  try {
    const base = typeof window !== 'undefined' && window.location?.origin
      ? window.location.origin
      : 'http://localhost'
    parsed = new URL(trimmed, base)
  } catch {
    return null
  }

  // URL.protocol is lowercased by the URL constructor
  return SAFE_SCHEMES.has(parsed.protocol) ? parsed.toString() : null
}
