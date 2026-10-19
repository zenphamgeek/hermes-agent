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
    expect(sanitizeCardUrl('JaVaScRiPt:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('java\tscript:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('java\nscript:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('java\rscript:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('javascript\0:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('data:text/html,<script>alert(1)</script>')).toBeNull()
    expect(sanitizeCardUrl('DATA:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==')).toBeNull()
    expect(sanitizeCardUrl('vbscript:msgbox(1)')).toBeNull()
    expect(sanitizeCardUrl('VbScRiPt:msgbox(1)')).toBeNull()
    expect(sanitizeCardUrl('file:///etc/passwd')).toBeNull()
    expect(sanitizeCardUrl('blob:https://example.com/6c9f688e-67a4-4f05-8e14-e0e68cb53c6c')).toBeNull()
    expect(sanitizeCardUrl('ws://example.com/socket')).toBeNull()
    expect(sanitizeCardUrl('wss://example.com/socket')).toBeNull()
    expect(sanitizeCardUrl('ftp://ftp.example.com/file.txt')).toBeNull()
    expect(sanitizeCardUrl('view-source:https://example.com')).toBeNull()
    expect(sanitizeCardUrl('intent://example.com#Intent;action=android.intent.action.VIEW;end')).toBeNull()
  })

  it('rejects control characters and malformed inputs', () => {
    expect(sanitizeCardUrl(null)).toBeNull()
    expect(sanitizeCardUrl(undefined)).toBeNull()
    expect(sanitizeCardUrl('')).toBeNull()
    expect(sanitizeCardUrl('   ')).toBeNull()
    expect(sanitizeCardUrl('https://example.com/\u0000bad')).toBeNull()
    expect(sanitizeCardUrl('https://example.com/\u001Fbad')).toBeNull()
    expect(sanitizeCardUrl('https://example.com/\u007Fbad')).toBeNull()
    expect(sanitizeCardUrl('\u001Fhttps://example.com/')).toBeNull()
  })

  it('rejects percent-encoded and multi-pass obfuscated schemes', () => {
    expect(sanitizeCardUrl('java%73cript:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('JaVa%73CrIpT:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('%6a%61%76%61%73%63%72%69%70%74:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('%256a%2561%2576%2561%2573%2563%2572%2569%2570%2574:alert(1)')).toBeNull()
    expect(sanitizeCardUrl('javascript%3aalert(1)')).toBeNull()
    expect(sanitizeCardUrl('data%3atext/html,<script>alert(1)</script>')).toBeNull()
    expect(sanitizeCardUrl('https://example.com/%00evil')).toBeNull()
    expect(sanitizeCardUrl('https://example.com/%1fevil')).toBeNull()
    expect(sanitizeCardUrl('https://example.com/%7fevil')).toBeNull()
    expect(sanitizeCardUrl('/relative/path/only')).toBeNull()
    expect(sanitizeCardUrl('//protocol-relative.com')).toBeNull()
  })
})


