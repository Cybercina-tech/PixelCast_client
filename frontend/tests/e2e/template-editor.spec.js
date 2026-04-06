import { expect, test } from '@playwright/test'
import { login } from './helpers/auth'

test('template editor balanced layout and basic interactions', async ({ page }) => {
  test.setTimeout(120000)
  await login(page)

  await page.goto('/templates/new/edit?name=E2E%20Template&width=1280&height=720')
  await expect(page.getByText('Widget Library')).toBeVisible()
  await expect(page.getByRole('button', { name: /^save$/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /export json/i })).toBeVisible()

  await page.getByRole('button', { name: /add text/i }).click()
  await expect(page.locator('.widget-element').first()).toBeVisible()

  await page.getByRole('button', { name: /layers/i }).click()
  await expect(page.getByText(/layers/i).first()).toBeVisible()

  await page.getByRole('button', { name: /properties/i }).click()
  await expect(page.getByText(/position & size/i)).toBeVisible()
})

test('template editor keyboard shortcuts do not interfere with input editing', async ({ page }) => {
  test.setTimeout(120000)
  await login(page)

  await page.goto('/templates/new/edit?name=Keyboard%20Safety&width=1280&height=720')
  await page.getByRole('button', { name: /add text/i }).click()

  const xInput = page.locator('input[type="number"]').first()
  const before = await xInput.inputValue()

  const textArea = page.locator('textarea').first()
  await textArea.click()
  await page.keyboard.press('ArrowRight')
  await page.keyboard.press('Delete')

  const after = await xInput.inputValue()
  expect(after).toBe(before)
})

test('template editor can configure qr action widget fields', async ({ page }) => {
  test.setTimeout(120000)
  await login(page)

  await page.goto('/templates/new/edit?name=QR%20Widget%20E2E&width=1280&height=720')
  await page.getByRole('button', { name: /add qr action/i }).click()

  await expect(page.getByText('QR Action Properties')).toBeVisible()
  await page.getByPlaceholder('Scan for discount').fill('Scan for discount')
  await page.getByPlaceholder('branch-x-morning').fill('branch-x-morning')
  await page.getByPlaceholder('https://example.com/menu').fill('https://example.com/morning-menu')

  await expect(page.getByText(/Readable contrast|Low contrast|Quiet zone/i)).toBeVisible()
})

test('template editor mobile: library, widget, inspector', async ({ page }) => {
  test.setTimeout(120000)
  await page.setViewportSize({ width: 390, height: 844 })
  await login(page)

  await page.goto('/templates/new/edit?name=Mobile%20E2E&width=1280&height=720')
  await expect(page.getByRole('button', { name: /^widgets$/i })).toBeVisible()
  await page.getByRole('button', { name: /^widgets$/i }).click()
  await expect(page.getByRole('dialog', { name: /widget library/i })).toBeVisible()
  await page.getByRole('button', { name: /add text/i }).click()
  await expect(page.locator('.widget-element').first()).toBeVisible()

  await page.getByRole('button', { name: /^inspector$/i }).click()
  await expect(page.getByRole('dialog', { name: /^inspector$/i })).toBeVisible()
  await expect(page.getByText(/position & size/i)).toBeVisible()
  await page.getByRole('button', { name: /^close$/i }).click()
})
