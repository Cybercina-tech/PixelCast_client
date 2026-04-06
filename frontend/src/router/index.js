import { nextTick } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { canAccessRoute, isClientDeployment, isDeveloperOrSuperuser } from '@/utils/permissions'
import { pushVirtualPageView } from '@/analytics/dataLayer'

// Public pages
import Landing from '../pages/Landing.vue'
import Login from '../pages/Login.vue'
import Signup from '../pages/Signup.vue'

// Dashboard
import Dashboard from '../pages/Dashboard.vue'

// Screens
import ScreensList from '../pages/screens/ScreensList.vue'
import ScreenDetails from '../pages/screens/ScreenDetails.vue'

// Templates
import TemplatesList from '../pages/templates/TemplatesList.vue'
import TemplateDetails from '../pages/templates/TemplateDetails.vue'
import TemplateEditor from '../pages/templates/TemplateEditor.vue'

// Contents
import ContentsList from '../pages/contents/ContentsList.vue'
import ContentDetails from '../pages/contents/ContentDetails.vue'

// Schedules
import SchedulesList from '../pages/schedules/SchedulesList.vue'
import ScheduleDetails from '../pages/schedules/ScheduleDetails.vue'

// Commands
import CommandsList from '../pages/commands/CommandsList.vue'
import CommandDetails from '../pages/commands/CommandDetails.vue'

// Users
import UsersList from '../pages/users/UsersList.vue'
import UserDetails from '../pages/users/UserDetails.vue'

// Logs
import LogsReports from '../pages/logs/LogsReports.vue'

// Tickets (requester)
import TicketsList from '../pages/tickets/TicketsList.vue'
import TicketDetail from '../pages/tickets/TicketDetail.vue'

// Analytics
import AnalyticsDashboard from '../pages/analytics/AnalyticsDashboard.vue'

// Core Infrastructure
import AuditLogs from '../pages/core/AuditLogs.vue'
import Backups from '../pages/core/Backups.vue'
import SystemEmailSettings from '../pages/core/SystemEmailSettings.vue'

// Settings
import Settings from '../pages/Settings.vue'

// Platform (SaaS super-admin) — minimal: tickets + self-hosted licenses
import SuperAdminShell from '../layouts/SuperAdminShell.vue'
import SuperAdminHome from '../pages/super-admin/SuperAdminHome.vue'
import SuperAdminLicenses from '../pages/super-admin/SuperAdminLicenses.vue'
import SuperAdminTicketQueue from '../pages/super-admin/SuperAdminTicketQueue.vue'
import SuperAdminTicketDetail from '../pages/super-admin/SuperAdminTicketDetail.vue'

// User Management
import Profile from '../pages/Profile.vue'
import Security from '../pages/Security.vue'
import Sessions from '../pages/Sessions.vue'

// Legal Pages
import PrivacyPolicy from '../pages/PrivacyPolicy.vue'
import TermsOfService from '../pages/TermsOfService.vue'
import DataCenter from '../pages/DataCenter.vue'
// Error Pages
import NotFound from '../pages/errors/NotFound.vue'
import Unauthorized from '../pages/errors/Unauthorized.vue'
import Forbidden from '../pages/errors/Forbidden.vue'
import ServerError from '../pages/errors/ServerError.vue'

// Web Player
import WebPlayer from '../pages/player/WebPlayer.vue'

const routes = [
  {
    path: '/',
    name: 'landing',
    component: Landing,
    meta: { public: true },
  },
  {
    path: '/install',
    name: 'install',
    component: () => import('../pages/SetupWizard.vue'),
    meta: { public: true },
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { public: true },
  },
  {
    path: '/signup',
    name: 'signup',
    component: Signup,
    meta: { public: true },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('../pages/ForgotPassword.vue'),
    meta: { public: true },
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: () => import('../pages/ResetPassword.vue'),
    meta: { public: true },
  },
  {
    path: '/privacy',
    name: 'privacy',
    component: PrivacyPolicy,
    meta: { public: true },
  },
  {
    path: '/terms',
    name: 'terms',
    component: TermsOfService,
    meta: { public: true },
  },
  {
    path: '/data-center',
    name: 'data-center',
    component: DataCenter,
    meta: { public: true },
  },
  {
    path: '/docs',
    name: 'docs',
    meta: { public: true },
    beforeEnter() {
      window.location.replace(`${window.location.origin}/documentation/index.html`)
      return false
    },
    component: { template: '<div />' },
  },
  {
    path: '/docs/changelog',
    name: 'docs-changelog',
    meta: { public: true },
    beforeEnter() {
      window.location.replace(`${window.location.origin}/documentation/changelog.html`)
      return false
    },
    component: { template: '<div />' },
  },
  {
    path: '/player',
    name: 'player',
    redirect: (to) => {
      const screenId = to.query.screenId || to.query.screen_id
      if (screenId) {
        return { name: 'player-screen', params: { screenId: String(screenId) } }
      }
      return { name: 'player-connect' }
    },
    meta: { public: true }, // Player uses its own authentication via URL params
  },
  {
    path: '/player/connect',
    name: 'player-connect',
    component: WebPlayer,
    meta: { public: true }, // Public pairing route
  },
  {
    path: '/player/:screenId',
    name: 'player-screen',
    component: WebPlayer,
    beforeEnter: (to) => {
      if (to.query.pair === '1') {
        return { name: 'player-screen', params: to.params }
      }
      return true
    },
    meta: { public: true },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
  },
  {
    path: '/super-admin',
    component: SuperAdminShell,
    meta: { requiresAuth: true, requiresRole: ['Developer'] },
    children: [
      {
        path: '',
        name: 'super-admin-home',
        component: SuperAdminHome,
        meta: { requiresAuth: true, requiresRole: ['Developer'] },
      },
      {
        path: 'self-hosted-licenses',
        name: 'super-admin-self-hosted-licenses',
        component: SuperAdminLicenses,
        meta: { requiresAuth: true, requiresRole: ['Developer'] },
      },
      {
        path: 'tickets',
        name: 'super-admin-tickets',
        component: SuperAdminTicketQueue,
        meta: { requiresAuth: true, requiresRole: ['Developer'] },
      },
      {
        path: 'tickets/:id',
        name: 'super-admin-ticket-detail',
        component: SuperAdminTicketDetail,
        meta: { requiresAuth: true, requiresRole: ['Developer'] },
      },
    ],
  },
  {
    path: '/platform/tenants',
    redirect: '/super-admin',
  },
  {
    path: '/platform/tenants/:id',
    redirect: '/super-admin',
  },
  {
    path: '/screens',
    name: 'screens',
    component: ScreensList,
    meta: { requiresAuth: true },
  },
  {
    path: '/screens/add',
    name: 'add-screen',
    component: () => import('../pages/screens/AddScreen.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/screens/:id',
    name: 'screen-details',
    component: ScreenDetails,
    meta: { requiresAuth: true },
  },
  {
    path: '/templates',
    name: 'templates',
    component: TemplatesList,
    meta: { requiresAuth: true },
  },
  {
    path: '/templates/:id',
    name: 'template-details',
    component: TemplateDetails,
    meta: { requiresAuth: true },
  },
  {
    path: '/templates/:id/edit',
    name: 'template-editor',
    component: TemplateEditor,
    meta: { requiresAuth: true },
  },
  {
    path: '/templates/new/edit',
    name: 'template-editor-new',
    component: TemplateEditor,
    meta: { requiresAuth: true },
  },
  {
    path: '/contents',
    name: 'contents',
    component: ContentsList,
    meta: { requiresAuth: true },
  },
  {
    path: '/contents/:id',
    name: 'content-details',
    component: ContentDetails,
    meta: { requiresAuth: true },
  },
  {
    path: '/schedules',
    name: 'schedules',
    component: SchedulesList,
    meta: { requiresAuth: true },
  },
  {
    path: '/schedules/:id',
    name: 'schedule-details',
    component: ScheduleDetails,
    meta: { requiresAuth: true },
  },
  {
    path: '/commands',
    name: 'commands',
    component: CommandsList,
    meta: { requiresAuth: true },
  },
  {
    path: '/commands/:id',
    name: 'command-details',
    component: CommandDetails,
    meta: { requiresAuth: true },
  },
  {
    path: '/users',
    name: 'users',
    component: UsersList,
    meta: { requiresAuth: true },
  },
  {
    path: '/users/:id',
    name: 'user-details',
    component: UserDetails,
    meta: { requiresAuth: true },
  },
  {
    path: '/tickets',
    name: 'tickets',
    component: TicketsList,
    meta: { requiresAuth: true },
  },
  {
    path: '/tickets/:id',
    name: 'ticket-detail',
    component: TicketDetail,
    meta: { requiresAuth: true },
  },
  {
    path: '/logs',
    name: 'logs',
    component: LogsReports,
    meta: { requiresAuth: true },
  },
  {
    path: '/analytics',
    name: 'analytics',
    component: AnalyticsDashboard,
    meta: { requiresAuth: true },
  },
  {
    path: '/core/audit-logs',
    name: 'audit-logs',
    component: AuditLogs,
    meta: { requiresAuth: true, requiresRole: ['Developer'] },
  },
  {
    path: '/core/backups',
    name: 'backups',
    component: Backups,
    meta: { requiresAuth: true, requiresRole: ['Developer'] },
  },
  {
    path: '/core/email',
    name: 'system-email-settings',
    component: SystemEmailSettings,
    meta: { requiresAuth: true, requiresRole: ['Developer'] },
  },
  {
    path: '/settings',
    name: 'settings',
    component: Settings,
    meta: { requiresAuth: true },
  },
  {
    path: '/settings/license',
    redirect: { path: '/settings', query: { tab: 'license' } },
  },
  {
    path: '/profile',
    name: 'profile',
    component: Profile,
    meta: { requiresAuth: true },
  },
  {
    path: '/security',
    name: 'security',
    component: Security,
    meta: { requiresAuth: true },
  },
  {
    path: '/sessions',
    name: 'sessions',
    component: Sessions,
    meta: { requiresAuth: true },
  },
  // Error pages
  {
    path: '/401',
    name: 'unauthorized',
    component: Unauthorized,
    meta: { requiresAuth: false },
  },
  {
    path: '/403',
    name: 'forbidden',
    component: Forbidden,
    meta: { public: true },
  },
  {
    path: '/500',
    name: 'server-error',
    component: ServerError,
    meta: { requiresAuth: false },
  },
  {
    path: '/404',
    name: 'not-found',
    component: NotFound,
    meta: { requiresAuth: false },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'catch-all',
    component: NotFound,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * Navigation Guard - Backend-Driven Authentication
 * 
 * IMPORTANT: This guard validates authentication with backend API.
 * Frontend role checks are for UX only - backend APIs enforce actual permissions.
 * 
 * Flow:
 * 1. Public routes: Allow access immediately
 * 2. Protected routes: Validate token with backend via fetchMe()
 * 3. Role-based routes: Check role from backend user data (backend API will also enforce)
 * 4. Invalid token: Clear auth state and redirect to login
 */
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const pathOnly = to.path.split('?')[0]
  if (isClientDeployment()) {
    if (pathOnly.startsWith('/super-admin') || pathOnly.startsWith('/platform')) {
      next({ name: 'dashboard' })
      return
    }
    if (pathOnly === '/pricing') {
      next({ name: 'landing' })
      return
    }
  }

  // Allow public routes to load immediately
  if (to.meta.public) {
    // If user is authenticated and trying to access public pages like login/signup
    if (authStore.isAuthenticated && (to.name === 'login' || to.name === 'signup')) {
      next({ name: 'dashboard' })
      return
    }
    next()
    return
  }
  
  // If route requires auth and user is not authenticated
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Try to validate token with backend (in case token exists but user state is not set)
    if (authStore.token) {
      try {
        // Validate token by fetching user from backend
        // Set timeout to prevent hanging if API is not available
        const fetchPromise = authStore.fetchMe() // Calls GET /api/users/me/
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout')), 2000)
        )
        
        await Promise.race([fetchPromise, timeoutPromise])
        
        // Backend validated token successfully
        if (authStore.isAuthenticated && authStore.user) {
          // UI-only role check for route guard (backend API will also enforce)
            if (to.meta.requiresRole) {
              const userRole = authStore.user?.role
              if (
                !isDeveloperOrSuperuser(authStore.user) &&
                !to.meta.requiresRole.includes(userRole)
              ) {
                next({ name: 'forbidden' })
                return
              }
            }
          next()
          return
        }
      } catch (error) {
        // Backend rejected token (401/403) or timeout - clear auth state
        authStore.token = null
        authStore.refreshToken = null
        authStore.isAuthenticated = false
        authStore.user = null
        localStorage.removeItem('auth_token')
        localStorage.removeItem('refresh_token')
      }
    }
    // No valid token or backend validation failed - redirect to login
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  // Check role requirements for authenticated users (UI-only check)
  // Backend API will enforce actual permissions
  if (to.meta.requiresRole && authStore.isAuthenticated && authStore.user) {
    const userRole = authStore.user?.role
    if (
      !isDeveloperOrSuperuser(authStore.user) &&
      !to.meta.requiresRole.includes(userRole)
    ) {
      next({ name: 'forbidden' })
      return
    }
  }
  
  // Check permissions for authenticated users (UI-only check)
  // Backend API will enforce actual permissions
  if (to.meta.requiresAuth && authStore.isAuthenticated && authStore.user) {
    if (!canAccessRoute(authStore.user, to.path)) {
      next({ name: 'forbidden' })
      return
    }
  }

  next()
})

router.afterEach((to) => {
  nextTick(() => pushVirtualPageView(to))
})

export default router
