/**
 * Short URLs `/docs` → static HTML during Vite dev.
 * Static files are served from `frontend/public/documentation/` (same as production dist).
 * Repo-root `documentation/` is mirrored there so dev works without bind-mounting the monorepo parent.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
}

export function documentationDevPlugin() {
  const frontendDir = path.dirname(fileURLToPath(import.meta.url))
  const docRoot = path.resolve(frontendDir, '..', 'documentation')

  return {
    name: 'pixelcast-documentation-static',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const raw = req.url?.split('?')[0] || ''
        if (raw === '/docs' || raw === '/docs/') {
          res.statusCode = 302
          res.setHeader('Location', '/documentation/index.html')
          res.end()
          return
        }
        if (raw === '/docs/changelog') {
          res.statusCode = 302
          res.setHeader('Location', '/documentation/changelog.html')
          res.end()
          return
        }
        if (!raw.startsWith('/documentation')) {
          return next()
        }
        let rel = raw.slice('/documentation'.length).replace(/^\/+/, '')
        if (!rel || rel.endsWith('/')) {
          rel = path.join(rel, 'index.html')
        }
        const fsPath = path.resolve(docRoot, rel)
        const relSafe = path.relative(docRoot, fsPath)
        if (relSafe.startsWith('..') || path.isAbsolute(relSafe)) {
          res.statusCode = 403
          res.end()
          return
        }
        fs.stat(fsPath, (err, st) => {
          if (err || !st.isFile()) {
            return next()
          }
          const ext = path.extname(fsPath).toLowerCase()
          res.setHeader('Content-Type', MIME[ext] || 'application/octet-stream')
          fs.createReadStream(fsPath).pipe(res)
        })
      })
    },
  }
}
