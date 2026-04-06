import { SITE_NAME, getSiteOrigin, getPublicRegionPhrase } from './siteConfig'

function orgId(origin) {
  return `${origin}/#organization`
}

function websiteId(origin) {
  return `${origin}/#website`
}

export function buildOrganizationAndWebsite(origin) {
  const area = getPublicRegionPhrase()
  const org = {
    '@type': 'Organization',
    '@id': orgId(origin),
    name: SITE_NAME,
    url: origin,
    description:
      'Digital signage software for commercial displays, retail, hospitality, and corporate screen networks.',
  }
  if (area === 'UK') {
    org.areaServed = { '@type': 'Country', name: 'United Kingdom' }
  }
  const website = {
    '@type': 'WebSite',
    '@id': websiteId(origin),
    name: SITE_NAME,
    url: origin,
    publisher: { '@id': orgId(origin) },
  }
  return { org, website }
}

/**
 * @param {object} opts
 * @param {string} opts.path
 * @param {string} opts.title
 * @param {string} opts.description
 * @param {string} [opts.type='WebPage']
 */
export function buildWebPageGraph(origin, opts) {
  const { path, title, description, type = 'WebPage' } = opts
  const url = `${origin}${path === '/' ? '/' : path.replace(/\/$/, '')}`
  const { org, website } = buildOrganizationAndWebsite(origin)
  const page = {
    '@type': type,
    '@id': `${url}#webpage`,
    url,
    name: title,
    description,
    isPartOf: { '@id': websiteId(origin) },
    about: { '@id': orgId(origin) },
  }
  return {
    '@context': 'https://schema.org',
    '@graph': [org, website, page],
  }
}

export function buildBlogPostingGraph(origin, opts) {
  const { path, headline, description, datePublished, dateModified } = opts
  const url = `${origin}${path}`
  const { org, website } = buildOrganizationAndWebsite(origin)
  const article = {
    '@type': 'BlogPosting',
    '@id': `${url}#article`,
    mainEntityOfPage: { '@type': 'WebPage', '@id': `${url}#webpage` },
    headline,
    description,
    url,
    datePublished: datePublished || '2026-04-01',
    dateModified: dateModified || datePublished || '2026-04-01',
    author: { '@type': 'Organization', name: SITE_NAME },
    publisher: { '@id': orgId(origin) },
    isPartOf: { '@id': websiteId(origin) },
  }
  const webPage = {
    '@type': 'WebPage',
    '@id': `${url}#webpage`,
    url,
    name: headline,
    description,
    isPartOf: { '@id': websiteId(origin) },
  }
  return {
    '@context': 'https://schema.org',
    '@graph': [org, website, webPage, article],
  }
}

export function buildFaqPageGraph(origin, faqPath, faqItems) {
  const url = `${origin}${faqPath}`
  const mainEntity = faqItems.map((item) => ({
    '@type': 'Question',
    name: item.question,
    acceptedAnswer: {
      '@type': 'Answer',
      text: item.answer,
    },
  }))
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    '@id': `${url}#faq`,
    url,
    mainEntity,
  }
}

/**
 * Blog page: article + optional FAQ as extra schema nodes (same URL).
 */
export function buildBlogPostingWithFaq(origin, opts, faqItems) {
  const base = buildBlogPostingGraph(origin, opts)
  if (!faqItems?.length) return base
  const pageUrl = `${origin}${opts.path.replace(/\/$/, '') || '/blog'}`
  const faqNode = {
    '@type': 'FAQPage',
    '@id': `${pageUrl}#faq`,
    mainEntity: faqItems.map((item) => ({
      '@type': 'Question',
      name: item.question,
      acceptedAnswer: { '@type': 'Answer', text: item.answer },
    })),
  }
  return {
    '@context': 'https://schema.org',
    '@graph': [...base['@graph'], faqNode],
  }
}
