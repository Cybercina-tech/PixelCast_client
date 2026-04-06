import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useHead, useSeoMeta } from '@unhead/vue'
import {
  DEFAULT_DESCRIPTION,
  SITE_NAME,
  getDefaultOgImageUrl,
  getSiteOrigin,
} from '@/seo/siteConfig'
import { SEO_BY_ROUTE_NAME, getDefaultSeo } from '@/seo/presets'
import { buildWebPageGraph } from '@/seo/jsonLd'

export function useRouteHead() {
  const route = useRoute()

  const resolved = computed(() => {
    const fromMeta = route.meta?.seo
    const fromMap = route.name ? SEO_BY_ROUTE_NAME[route.name] : null
    return { ...getDefaultSeo(), ...fromMap, ...fromMeta }
  })

  const origin = computed(() => getSiteOrigin())

  const canonicalPath = computed(() => {
    const p = route.path || '/'
    if (p.length > 1 && p.endsWith('/')) return p.slice(0, -1)
    return p
  })

  const canonicalUrl = computed(() => {
    const o = origin.value
    if (!o) return ''
    const path = canonicalPath.value === '' ? '/' : canonicalPath.value
    return `${o}${path === '/' ? '' : path}`
  })

  const title = computed(() => resolved.value.title || `${SITE_NAME} — Digital Signage`)
  const description = computed(() => resolved.value.description || DEFAULT_DESCRIPTION)
  const robots = computed(() => resolved.value.robots || 'noindex, nofollow')

  const ogImage = computed(() => {
    if (resolved.value.ogImage) return resolved.value.ogImage
    return getDefaultOgImageUrl() || undefined
  })

  useSeoMeta({
    title,
    description,
    robots,
    ogTitle: title,
    ogDescription: description,
    ogUrl: canonicalUrl,
    ogType: 'website',
    ogImage,
    twitterCard: 'summary_large_image',
    twitterTitle: title,
    twitterDescription: description,
    twitterImage: ogImage,
  })

  const jsonLd = computed(() => {
    const o = origin.value
    if (!o) return null
    const path = canonicalPath.value || '/'
    const t = title.value
    const d = description.value
    const name = route.name

    if (robots.value.includes('noindex')) {
      return null
    }

    return buildWebPageGraph(o, {
      path,
      title: t,
      description: d,
      type: 'WebPage',
    })
  })

  useHead({
    link: computed(() => {
      const href = canonicalUrl.value
      if (!href) return []
      return [{ rel: 'canonical', href }]
    }),
    script: computed(() => {
      const data = jsonLd.value
      if (!data) return []
      return [
        {
          key: 'pixelcast-jsonld',
          type: 'application/ld+json',
          children: JSON.stringify(data),
        },
      ]
    }),
  })
}
