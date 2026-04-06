/**
 * Central SEO presets keyed by Vue Router route `name`.
 * Override via route.meta.seo when needed.
 */
import { DEFAULT_DESCRIPTION, SITE_NAME } from './siteConfig'

const UK = ' For UK teams and international deployments.'

function publicSeo(title, description, opts = {}) {
  return {
    title,
    description,
    robots: opts.robots || 'index, follow',
    ...opts,
  }
}

function noindex(title, description = 'PixelCast digital signage platform.') {
  return {
    title: `${title} — ${SITE_NAME}`,
    description,
    robots: 'noindex, nofollow',
  }
}

function appPage(title) {
  return {
    title: `${title} — ${SITE_NAME}`,
    description:
      'Signed-in area: manage digital signage screens, templates, content, and schedules in PixelCast.',
    robots: 'noindex, nofollow',
  }
}

/** @type {Record<string, Record<string, unknown>>} */
export const SEO_BY_ROUTE_NAME = {
  landing: publicSeo(
    `${SITE_NAME} — Digital Signage Software & Display Management`,
    `Commercial digital signage solutions for retail, restaurants, corporate offices, and screen networks.${UK} Templates, scheduling, remote players, and fleet monitoring in one platform.`
  ),
  install: publicSeo(
    `Install ${SITE_NAME} — Digital Signage Setup Wizard`,
    'Self-hosted digital signage installation: configure your environment, admin account, and get your screen network online with guided setup.'
  ),
  login: publicSeo(
    `Sign In — ${SITE_NAME} Digital Signage`,
    'Sign in to manage digital signage displays, menu boards, templates, schedules, and remote device commands from your PixelCast dashboard.'
  ),
  signup: publicSeo(
    `Start Free Trial — Digital Signage Software | ${SITE_NAME}`,
    'Create your account and start managing commercial digital signage: template editor, content library, schedules, and secure web players for business displays.'
  ),
  'forgot-password': publicSeo(
    `Reset Password — ${SITE_NAME}`,
    'Request a secure link to reset your PixelCast account password.',
    { robots: 'noindex, nofollow' }
  ),
  'reset-password': publicSeo(
    `Set New Password — ${SITE_NAME}`,
    'Choose a new password to access your digital signage management account.',
    { robots: 'noindex, nofollow' }
  ),
  privacy: publicSeo(
    `Privacy Policy — ${SITE_NAME}`,
    'How PixelCast collects, uses, and protects personal data when you use our digital signage management platform.'
  ),
  terms: publicSeo(
    `Terms of Service — ${SITE_NAME}`,
    'Terms governing use of PixelCast digital signage software, accounts, and related services.'
  ),
  'data-center': publicSeo(
    `Data Center & Downloads — ${SITE_NAME} Digital Signage`,
    'Download player apps and resources to deploy commercial digital signage players and keep displays updated.'
  ),
  docs: publicSeo(
    `Documentation — ${SITE_NAME} Digital Signage Platform`,
    'Product documentation for digital signage setup, templates, screens, content, schedules, and operations.'
  ),
  'docs-changelog': publicSeo(
    `Changelog — ${SITE_NAME} Digital Signage`,
    'Release notes and product updates for the PixelCast digital signage platform.'
  ),
  player: noindex('Player redirect', 'Web player entry.'),
  'player-connect': noindex(
    'Web player pairing',
    'Pair a browser or device to your PixelCast digital signage screen.'
  ),
  'player-screen': noindex(
    'Web player',
    'Full-screen digital signage playback for paired displays.'
  ),
  dashboard: appPage('Dashboard'),
  screens: appPage('Screens'),
  'add-screen': appPage('Add screen'),
  'screen-details': appPage('Screen details'),
  templates: appPage('Templates'),
  'template-details': appPage('Template'),
  'template-editor': appPage('Template editor'),
  'template-editor-new': appPage('New template'),
  contents: appPage('Content'),
  'content-details': appPage('Content'),
  schedules: appPage('Schedules'),
  'schedule-details': appPage('Schedule'),
  commands: appPage('Commands'),
  'command-details': appPage('Command'),
  users: appPage('Users'),
  'user-details': appPage('User'),
  tickets: appPage('Tickets'),
  'ticket-detail': appPage('Ticket'),
  logs: appPage('Logs'),
  analytics: appPage('Analytics'),
  'audit-logs': appPage('Audit logs'),
  backups: appPage('Backups'),
  'system-email-settings': appPage('Email settings'),
  settings: appPage('Settings'),
  profile: appPage('Profile'),
  security: appPage('Security'),
  sessions: appPage('Sessions'),
  unauthorized: noindex('Unauthorized', 'Authentication required.'),
  forbidden: publicSeo(
    `Access denied — ${SITE_NAME}`,
    'You do not have permission to view this page.',
    { robots: 'noindex, nofollow' }
  ),
  'server-error': noindex('Server error', 'Something went wrong.'),
  'not-found': noindex('Page not found', 'The page you requested does not exist.'),
  'catch-all': noindex('Page not found', 'The page you requested does not exist.'),
  'super-admin-home': appPage('Super Admin'),
  'super-admin-self-hosted-licenses': appPage('Self-hosted licenses'),
  'super-admin-tickets': appPage('Tickets'),
  'super-admin-ticket-detail': appPage('Ticket'),
}

export function getDefaultSeo() {
  return {
    title: SITE_NAME,
    description: DEFAULT_DESCRIPTION,
    robots: 'noindex, nofollow',
  }
}
