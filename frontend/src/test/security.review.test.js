import { readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const frontendRoot = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
const srcRoot = join(frontendRoot, 'src')

const FORBIDDEN = [
  'AI_API_KEY',
  'JWT_SECRET',
  'DATABASE_URL',
  'REDIS_URL',
  'generativelanguage.googleapis.com',
  '@google/genai',
  'google-generativeai',
]

function walk(dir) {
  const files = []
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) {
      files.push(...walk(path))
    } else if (/\.(js|jsx|css|html|json)$/.test(name) && !path.includes(`${sep}test${sep}security.review.test.js`)) {
      files.push(path)
    }
  }
  return files
}

describe('frontend secret handling', () => {
  it('does not embed backend secrets or call Gemini directly', () => {
    const files = [
      ...walk(srcRoot),
      join(frontendRoot, '.env.example'),
      join(frontendRoot, 'package.json'),
    ]

    for (const file of files) {
      const text = readFileSync(file, 'utf8')
      for (const token of FORBIDDEN) {
        expect(text, `${token} found in ${file}`).not.toContain(token)
      }
    }
  })

  it('only exposes VITE_API_BASE_URL as public env', () => {
    const example = readFileSync(join(frontendRoot, '.env.example'), 'utf8')
    const viteKeys = example
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.startsWith('VITE_'))
    expect(viteKeys).toEqual(['VITE_API_BASE_URL=http://localhost:8000'])
  })
})
