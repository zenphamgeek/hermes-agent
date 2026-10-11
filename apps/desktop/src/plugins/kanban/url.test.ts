import { describe, expect, it } from 'vitest'
import { sanitizeCardUrl } from './url'

describe('sanitizeCardUrl', () => {
  it('allows safe http, https, and mailto URLs', () => {
    expect(sanitizeCardUrl('https://example.com/page?x=1')).toBe('https://example.com/page?x=1')
    expect(sanitizeCardUrl('http://example.com')).toBe('http://example.com/')
    expect(sanitizeCardUrl('mailto:security@example.com')).toBe('mailto:security@example.com')
  })

  it('rejects dangerous and executable URI schemes', () => {
    expect(sanitizeCardUrl('javascript:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('JavaScript:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('java\tscript:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('data:text/html,<script>alert(1)</script>')).toBeNull()
    expect(sanitizeCardUrl('vbscript:msgbox(1)')).toBeNull()
    expect(sanitizeCardUrl('file:///etc/passwd')).toBeNull()
  })

  it('rejects control characters and malformed inputs', () => {
    expect(sanitizeCardUrl(null)).toBeNull()
    expect(sanitizeCardUrl(undefined)).toBeNull()
    expect(sanitizeCardUrl('')).toBeNull()
    expect(sanitizeCardUrl('   ')).toBeNull()
    expect(sanitizeCardUrl('https://example.com/\u0000bad')).toBeNull()
  })
})
