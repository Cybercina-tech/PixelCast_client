import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { expect, test } from '@playwright/test'
import { login } from './helpers/auth'

function createPngFixture(fileName) {
  const fixturePath = path.join(os.tmpdir(), fileName)
  // 1x1 transparent PNG
  const pngBase64 =
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlAbYkAAAAASUVORK5CYII='
  fs.writeFileSync(fixturePath, Buffer.from(pngBase64, 'base64'))
  return fixturePath
}

test('real upload and preview flow', async ({ page }) => {
  await login(page)
  await page.goto('/contents')

  const uniqueName = `e2e-upload-${Date.now()}`
  const uploadPath = createPngFixture(`${uniqueName}.png`)

  await page.getByRole('button', { name: /upload media/i }).click()
  await page.getByRole('button', { name: /^upload$/i }).click()
  await page.locator('input[type="file"]').setInputFiles(uploadPath)
  await page.getByPlaceholder('Enter a name for the content').fill(uniqueName)
  await page.getByRole('button', { name: /upload 1 file/i }).click()

  await expect(page.getByRole('button', { name: /done|cancel/i })).toBeVisible({ timeout: 30000 })
  await page.getByRole('button', { name: /done|cancel/i }).click()

  const cardTitle = page.getByText(uniqueName, { exact: false }).first()
  await expect(cardTitle).toBeVisible({ timeout: 30000 })

  const mediaCard = cardTitle.locator('xpath=ancestor::*[contains(@class,"group")][1]')
  await mediaCard.hover()
  await mediaCard.getByRole('button', { name: /preview/i }).click()

  await expect(page.getByText(uniqueName).first()).toBeVisible()
  await expect(page.locator('img, video').first()).toBeVisible()
})
