/// <reference types="vitest/config" />
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'

const DATA_DIR = resolve(__dirname, '../data')

// Serves ../data at /data in dev and copies it into the build, so the scanner output stays in one place.
function scanData(): Plugin {
  const serve = (req: { url?: string }, res: { setHeader: (k: string, v: string) => void; end: (b: Buffer) => void }, next: () => void) => {
    const name = req.url?.match(/^\/data\/([\w-]+\.json)/)?.[1]
    const file = name && resolve(DATA_DIR, name)
    if (!file || !existsSync(file)) return next()
    res.setHeader('Content-Type', 'application/json')
    res.end(readFileSync(file))
  }
  return {
    name: 'scan-data',
    configureServer: (server) => void server.middlewares.use(serve),
    configurePreviewServer: (server) => void server.middlewares.use(serve),
    writeBundle(options) {
      if (!existsSync(DATA_DIR) || !options.dir) return
      const out = resolve(options.dir, 'data')
      mkdirSync(out, { recursive: true })
      for (const f of readdirSync(DATA_DIR).filter((f) => f.endsWith('.json'))) {
        copyFileSync(resolve(DATA_DIR, f), resolve(out, f))
      }
    },
  }
}

export default defineConfig({
  base: './',
  plugins: [react(), scanData()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
