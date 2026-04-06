import { expect } from '@playwright/test'

export async function login(page) {
  const username = process.env.E2E_USERNAME
  const password = process.env.E2E_PASSWORD

  if (!username || !password) {
    throw new Error('E2E_USERNAME and E2E_PASSWORD must be provided')
  }

  await page.goto('/login')
  await page.fill('#login-username', username)
  await page.fill('#login-password', password)
  await page.getByRole('button', { name: /sign in/i }).click()

  await expect(page).not.toHaveURL(/\/login/)
}
