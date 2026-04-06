/**
 * Permission checking utilities for frontend.
 *
 * Note: These are UI-only checks. Backend APIs enforce actual permissions.
 */

/** @type {{ is_client: boolean, deployment_mode: string|null, show_platform_routes: boolean }} */
let deploymentFlags = {
  is_client: false,
  deployment_mode: null,
  show_platform_routes: true,
}

/**
 * Sync from GET /api/public/deployment/ (called at app boot).
 * @param {object} payload
 */
export function setDeploymentFlags(payload) {
  if (!payload || typeof payload !== 'object') {
    return
  }
  const mode = payload.deployment_mode || null
  deploymentFlags = {
    is_client: Boolean(payload.is_client) || mode === 'client',
    deployment_mode: mode,
    show_platform_routes: payload.show_platform_routes !== false,
  }
}

export function isClientDeployment() {
  return deploymentFlags.is_client
}

const RESTRICTED_MODE_ALLOWED_PREFIXES = [
  '/security',
  '/sessions',
  '/login',
  '/logout',
  '/403',
  '/404',
  '/401',
  '/terms',
]

export function isRouteAllowedInRestrictedMode(path) {
  const normalized = (path || '').split('?')[0]
  return RESTRICTED_MODE_ALLOWED_PREFIXES.some(
    (prefix) => normalized === prefix || normalized.startsWith(`${prefix}/`)
  )
}

const ROUTE_PERMISSIONS = {
  '/dashboard': ['view_dashboard'],
  '/screens': ['view_screens'],
  '/templates': ['view_templates'],
  '/contents': ['view_contents'],
  '/schedules': ['view_schedules'],
  '/commands': ['view_commands'],
  '/users': ['view_users'],
  '/logs': ['view_logs'],
  '/analytics': ['view_analytics'],
  '/settings': ['view_settings'],
  '/tickets': ['view_tickets'],
  '/platform/tenants': ['view_platform'],
  '/super-admin': ['view_platform'],
}

/**
 * In SaaS/hybrid, superusers match Developer in the UI (backend is_developer()).
 * In client deployment, superuser is capped to org admin (Manager) — not full platform Developer.
 * @param {Object|null|undefined} user
 * @returns {boolean}
 */
export function isDeveloperOrSuperuser(user) {
  if (!user) return false
  if (deploymentFlags.is_client) {
    return user.role === 'Developer'
  }
  return user.role === 'Developer' || user.is_superuser === true
}

const ROLE_PERMISSIONS = {
  Developer: [
    'view_dashboard',
    'view_screens', 'create_screens', 'edit_screens', 'delete_screens',
    'view_templates', 'create_templates', 'edit_templates', 'delete_templates',
    'view_contents', 'create_contents', 'edit_contents', 'delete_contents',
    'view_schedules', 'create_schedules', 'edit_schedules', 'delete_schedules',
    'view_commands', 'create_commands', 'execute_commands',
    'view_users', 'create_users', 'edit_users', 'delete_users', 'manage_roles',
    'view_logs',
    'view_analytics',
    'view_audit_logs',
    'view_backups', 'manage_backups',
    'view_settings', 'edit_settings',
    'view_errors',
    'view_platform',
    'view_tickets', 'create_tickets',
  ],
  Manager: [
    'view_dashboard',
    'view_screens', 'create_screens', 'edit_screens', 'delete_screens',
    'view_templates', 'create_templates', 'edit_templates', 'delete_templates',
    'view_contents', 'create_contents', 'edit_contents', 'delete_contents',
    'view_schedules', 'create_schedules', 'edit_schedules', 'delete_schedules',
    'view_commands', 'create_commands', 'execute_commands',
    'view_users', 'create_users', 'edit_users', 'delete_users',
    'view_analytics',
    'view_tickets', 'create_tickets',
  ],
  Employee: [
    'view_dashboard',
    'view_screens', 'create_screens', 'edit_screens',
    'view_templates', 'create_templates', 'edit_templates',
    'view_schedules', 'create_schedules', 'edit_schedules', 'delete_schedules',
    'view_contents', 'create_contents', 'edit_contents',
    'view_commands', 'create_commands', 'execute_commands',
    'view_logs',
    'view_analytics',
    'view_settings', 'edit_settings',
    'view_tickets', 'create_tickets',
  ],
  Visitor: [
    'view_dashboard',
    'view_screens',
    'view_templates',
    'view_contents',
    'view_schedules',
    'view_commands',
    'view_logs',
    'view_analytics',
    'view_tickets',
  ],
}

/**
 * @param {Object} user - User object with role property
 * @returns {Set<string>}
 */
export function getUserPermissions(user) {
  if (!user) {
    return new Set()
  }
  if (isDeveloperOrSuperuser(user)) {
    return new Set(ROLE_PERMISSIONS.Developer)
  }
  if (!user.role) {
    return new Set()
  }

  const role = user.role
  const permissions = ROLE_PERMISSIONS[role] || []

  return new Set(permissions)
}

export function hasPermission(user, permission) {
  if (!user) {
    return false
  }
  if (isDeveloperOrSuperuser(user)) {
    return ROLE_PERMISSIONS.Developer.includes(permission)
  }
  if (!user.role) {
    return false
  }
  return getUserPermissions(user).has(permission)
}

/**
 * Match longest registered route prefix (supports nested paths like /screens/:id).
 */
export function canAccessRoute(user, routePath) {
  if (!user) {
    return false
  }

  const pathOnly = routePath.split('?')[0]
  if (deploymentFlags.is_client && (pathOnly === '/super-admin' || pathOnly.startsWith('/super-admin/') || pathOnly.startsWith('/platform/'))) {
    return false
  }

  if (isDeveloperOrSuperuser(user)) {
    return true
  }
  if (!user.role) {
    return false
  }

  const path = routePath.split('?')[0]
  const prefixes = Object.keys(ROUTE_PERMISSIONS).sort((a, b) => b.length - a.length)

  for (const prefix of prefixes) {
    if (path === prefix || path.startsWith(`${prefix}/`)) {
      const required = ROUTE_PERMISSIONS[prefix]
      const userPermissions = getUserPermissions(user)
      return required.some((perm) => userPermissions.has(perm))
    }
  }

  return true
}

export function hasAnyPermission(user, permissions) {
  if (!user || !permissions || permissions.length === 0) {
    return false
  }
  if (isDeveloperOrSuperuser(user)) {
    return permissions.some((perm) => ROLE_PERMISSIONS.Developer.includes(perm))
  }
  if (!user.role) {
    return false
  }

  const userPermissions = getUserPermissions(user)
  return permissions.some((perm) => userPermissions.has(perm))
}

export function hasAllPermissions(user, permissions) {
  if (!user || !permissions || permissions.length === 0) {
    return false
  }
  if (isDeveloperOrSuperuser(user)) {
    return permissions.every((perm) => ROLE_PERMISSIONS.Developer.includes(perm))
  }
  if (!user.role) {
    return false
  }

  const userPermissions = getUserPermissions(user)
  return permissions.every((perm) => userPermissions.has(perm))
}
