import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({
  gfm: true,
  breaks: true,
})

/**
 * Render Markdown to sanitized HTML for public blog content.
 * @param {string} markdown
 * @returns {string}
 */
export function renderMarkdown(markdown) {
  const raw = marked.parse(markdown || '', { async: false })
  return DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } })
}
