import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import path from 'node:path'
import { writeFileSync } from 'node:fs'
import { execSync } from 'child_process'
import fs from 'node:fs'
import { documentationDevPlugin } from './vite-documentation-plugin.js'

/**
 * Vite proxy must reach Django. Inside Docker, 127.0.0.1:8000 is wrong (backend is another container).
 * Prefer VITE_PROXY_TARGET; else if /.dockerenv exists use service hostname; else local dev on host.
 */
function getBackendProxyTarget() {
  if (process.env.VITE_PROXY_TARGET) {
    return process.env.VITE_PROXY_TARGET
  }
  try {
    if (fs.existsSync('/.dockerenv')) {
      return 'http://backend:8000'
    }
  } catch {
    /* non-blocking */
  }
  return 'http://127.0.0.1:8000'
}

const backendProxyTarget = getBackendProxyTarget()

// Get Git info at build time
function getGitVersion() {
  try {
    const commitHash = execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim()
    // Return just the commit hash (e.g., "e994370")
    // Or use format: "v1.0.0-e994370" if you have a version number
    return commitHash
  } catch (error) {
    console.warn('Git info not available, using fallback version')
    return 'dev'
  }
}

const gitVersion = getGitVersion()

/** Emit robots.txt + sitemap.xml into dist using VITE_PUBLIC_SITE_ORIGIN (fallback for local preview). */
function seoStaticFilesPlugin() {
  let outDir = 'dist'
  return {
    name: 'seo-static-files',
    apply: 'build',
    configResolved(config) {
      outDir = config.build.outDir
    },
    writeBundle() {
      const raw = process.env.VITE_PUBLIC_SITE_ORIGIN || 'https://pixelcast.cybercina.co.uk'
      const origin = String(raw).trim().replace(/\/$/, '')
      const indexablePaths = [
        '/',
        '/login',
        '/signup',
        '/install',
        '/privacy',
        '/terms',
        '/data-center',
        '/docs',
        '/docs/changelog',
      ]
      const urlset = indexablePaths
        .map((p) => {
          const loc = p === '/' ? `${origin}/` : `${origin}${p}`
          const priority = p === '/' ? '1.0' : '0.8'
          return `  <url>
    <loc>${loc}</loc>
    <changefreq>weekly</changefreq>
    <priority>${priority}</priority>
  </url>`
        })
        .join('\n')
      const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urlset}
</urlset>
`
      const robots = `User-agent: *
Allow: /

Disallow: /api/
Disallow: /admin/
Disallow: /player/
Disallow: /iot/
Disallow: /public-iot/
Disallow: /ws/

Sitemap: ${origin}/sitemap.xml
`
      const outAbs = path.resolve(process.cwd(), outDir)
      writeFileSync(path.join(outAbs, 'sitemap.xml'), sitemap)
      writeFileSync(path.join(outAbs, 'robots.txt'), robots)
    },
  }
}

/**
 * Vite HMR behind HTTPS reverse proxy (Traefik / Dokploy):
 * HTTPS pages cannot use ws:// (mixed content). Use wss:// on the public port (443).
 *
 * Options (any one is enough):
 * - VITE_BEHIND_HTTPS_PROXY=1  → wss + clientPort 443
 * - VITE_HMR_PROTOCOL=wss and VITE_HMR_CLIENT_PORT=443
 */
function getHmrConfig() {
  const behindHttps =
    process.env.VITE_BEHIND_HTTPS_PROXY === '1' ||
    process.env.VITE_BEHIND_HTTPS_PROXY === 'true'
  const useWss =
    behindHttps ||
    process.env.VITE_HMR_PROTOCOL === 'wss' ||
    process.env.VITE_HMR_CLIENT_PORT === '443'
  const clientPort = Number(
    process.env.VITE_HMR_CLIENT_PORT || (useWss ? 443 : 5173)
  )
  const protocol = useWss ? 'wss' : 'ws'
  const cfg = {
    path: '/vite-hmr',
    protocol,
    clientPort,
  }
  if (process.env.VITE_HMR_HOST) {
    cfg.host = process.env.VITE_HMR_HOST
  }
  return cfg
}

/** Warn when .env sets a browser-unreachable Docker service URL for the API base (see .env.development.example). */
function warnIfDockerInternalViteApiBase(mode) {
  const fromFile = loadEnv(mode, process.cwd(), '')
  const candidates = [process.env.VITE_API_BASE_URL, fromFile.VITE_API_BASE_URL].filter(Boolean)
  const dockerHostPattern =
    /:\/\/backend(?::|$|\/)|backend:8000|:\/\/django(?::|$|\/)|:\/\/web(?::|$|\/)|:\/\/api(?::|$|\/)/
  for (const v of candidates) {
    if (dockerHostPattern.test(String(v))) {
      console.warn(
        '[vite] VITE_API_BASE_URL must not use Docker-only hostnames (e.g. backend:8000) in values baked into the browser. Use /api and VITE_PROXY_TARGET for the dev server (see frontend/.env.development.example).'
      )
      break
    }
  }
}

export default defineConfig(({ mode }) => {
  warnIfDockerInternalViteApiBase(mode)
  return {
    plugins: [documentationDevPlugin(), vue(), seoStaticFilesPlugin()],
    server: {
      host: true,
      port: 5173,
      strictPort: true,
      // Dokploy/Traefik and other reverse proxies use dynamic hostnames (*.traefik.me, etc.)
      allowedHosts: process.env.VITE_ALLOWED_HOSTS
        ? process.env.VITE_ALLOWED_HOSTS.split(',').map((h) => h.trim()).filter(Boolean)
        : true,
      watch: {
        usePolling: true,
      },
      hmr: getHmrConfig(),
      proxy: {
        '/api': {
          target: backendProxyTarget,
          changeOrigin: true,
          secure: false,
          timeout: 120_000,
        },
        '/admin': {
          target: backendProxyTarget,
          changeOrigin: true,
        },
        '/media': {
          target: backendProxyTarget,
          changeOrigin: true,
        },
        '/ws': {
          target: backendProxyTarget,
          changeOrigin: true,
          ws: true,
        },
        // Player IoT traffic (template, heartbeat, commands) — same issue as /api when backend
        // is only reachable as backend:8000 inside Docker; browser must use same-origin /iot.
        '/iot': {
          target: backendProxyTarget,
          changeOrigin: true,
        },
        '/public-iot': {
          target: backendProxyTarget,
          changeOrigin: true,
        },
      },
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    define: {
      __APP_VERSION__: JSON.stringify(gitVersion)
    },
    optimizeDeps: {
      include: ['qrcode', 'jsqr', 'marked', 'dompurify'],
    },
    test: {
      environment: 'happy-dom',
      environmentOptions: {
        happyDOM: {
          url: 'http://localhost:5173/',
        },
      },
      include: ['src/**/*.test.js'],
    },
  }
})
