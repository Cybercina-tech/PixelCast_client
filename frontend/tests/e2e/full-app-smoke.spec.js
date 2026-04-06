import { expect, test } from '@playwright/test'
import { login } from './helpers/auth'

const appRoutes = [
  '/dashboard',
  '/screens',
  '/templates',
  '/contents',
  '/schedules',
  '/commands',
  '/users',
  '/logs',
  '/analytics',
  '/settings',
  '/profile',
  '/security',
  '/sessions',
]

test('full app smoke and theme parity', async ({ page }) => {
  test.setTimeout(120000)
  await login(page)

  for (const route of appRoutes) {
    await page.goto(route)
    await expect(page.locator('body')).toBeVisible()
    await expect(page.locator('#app')).toBeVisible()
  }

  await page.goto('/settings')
  await page.getByRole('button', { name: /^display$/i }).click()

  // Switch to light and verify DOM theme state.
  await page.getByRole('button', { name: /light/i }).first().click()
  await page.getByRole('button', { name: /save changes/i }).click()
  await expect.poll(async () => page.evaluate(() => document.documentElement.classList.contains('dark'))).toBe(false)

  // Switch back to dark and verify DOM theme state.
  await page.getByRole('button', { name: /deep space/i }).first().click()
  await page.getByRole('button', { name: /save changes/i }).click()
  await expect.poll(async () => page.evaluate(() => document.documentElement.classList.contains('dark'))).toBe(true)
})
