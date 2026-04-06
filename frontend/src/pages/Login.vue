<template>
  <div class="auth-page cosmic-auth min-h-screen flex">
    <!-- Deep space gradient base -->
    <div class="cosmic-bg" aria-hidden="true" />

    <!-- Animated starfield (CSS-only twinkling stars) -->
    <div class="cosmic-starfield" aria-hidden="true" />

    <!-- Nebula accents (blurred glow in corners) -->
    <div class="nebula nebula--indigo" aria-hidden="true" />
    <div class="nebula nebula--purple" aria-hidden="true" />

    <!-- Left: Brand (visible on lg+) -->
    <div
      class="hidden lg:flex lg:w-1/2 xl:w-[55%] flex-col justify-center px-12 xl:px-20 py-16 relative z-10"
    >
      <div
        v-motion
        :initial="{ opacity: 0, x: -24 }"
        :enter="{ opacity: 1, x: 0 }"
        :transition="{ duration: 500 }"
        class="max-w-md"
      >
        <div class="cosmic-icon-wrap inline-flex items-center justify-center w-14 h-14 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 text-indigo-400 shadow-lg mb-8">
          <svg class="w-7 h-7 cosmic-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.75">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h1 class="cosmic-title text-3xl xl:text-4xl font-bold text-white tracking-wide mb-3">
          PixelCast Signage
        </h1>
        <p class="text-slate-400 text-lg leading-relaxed">
          Secure digital signage management. Sign in to manage screens, content, and schedules.
        </p>
        <div class="mt-12 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 p-8 shadow-xl">
          <div class="flex items-center gap-4 text-slate-500">
            <div class="flex-1 h-2 rounded-full bg-white/20" />
            <div class="flex-1 h-2 rounded-full bg-indigo-500/40" />
            <div class="flex-1 h-2 rounded-full bg-white/20" />
          </div>
          <div class="mt-4 flex gap-3">
            <div class="w-16 h-12 rounded-xl bg-white/10" />
            <div class="w-20 h-12 rounded-xl bg-indigo-500/20" />
            <div class="w-14 h-12 rounded-xl bg-white/10" />
          </div>
        </div>
      </div>
    </div>

    <!-- Right: Form -->
    <div class="w-full lg:w-1/2 xl:w-[45%] flex items-center justify-center px-4 sm:px-6 py-12 lg:py-16 relative z-10">
      <div
        v-motion
        :initial="{ opacity: 0, y: 16 }"
        :enter="{ opacity: 1, y: 0 }"
        :transition="{ duration: 400 }"
        class="w-full max-w-md"
      >
        <div class="lg:hidden text-center mb-8">
          <h1 class="cosmic-title text-2xl font-bold text-white">PixelCast Signage</h1>
          <p class="text-sm text-slate-400 mt-1">Sign in to your account</p>
        </div>

        <!-- Glass-portal card -->
        <div class="glass-portal rounded-2xl overflow-hidden">
          <div class="px-6 sm:px-8 py-8 sm:py-10">
            <h2 class="cosmic-heading text-xl font-bold text-white mb-1">
              {{ needs2fa ? 'Two-factor authentication' : 'Welcome back' }}
            </h2>
            <p class="text-sm text-slate-400 mb-6">
              {{
                needs2fa
                  ? 'Enter the 6-digit code from your authenticator app or a backup code.'
                  : 'Enter your credentials to continue'
              }}
            </p>

            <form v-if="!needs2fa" @submit.prevent="handleLogin" class="space-y-5">
              <!-- Error -->
              <transition
                enter-active-class="transition-all duration-300 ease-out"
                enter-from-class="opacity-0 -translate-y-1"
                enter-to-class="opacity-100 translate-y-0"
                leave-active-class="transition-all duration-200 ease-in"
                leave-from-class="opacity-100 translate-y-0"
                leave-to-class="opacity-0 -translate-y-1"
              >
                <div
                  v-if="authStore.error"
                  class="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300 flex items-start gap-2"
                  role="alert"
                >
                  <ExclamationCircleIcon class="h-5 w-5 flex-shrink-0 mt-0.5 text-red-400 cosmic-icon" />
                  <span class="flex-1">{{ authStore.error }}</span>
                </div>
              </transition>

              <!-- Username / Email (floating label) -->
              <div class="input-wrap">
                <div class="input-group relative group">
                  <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors duration-300 cosmic-icon-wrap">
                    <UserIcon class="h-5 w-5 cosmic-icon" />
                  </div>
                  <input
                    id="login-username"
                    v-model="form.username"
                    type="text"
                    required
                    autocomplete="username"
                    class="auth-input cosmic-input w-full pl-11 pr-4 py-3 rounded-xl border border-white/10 bg-black/40 text-white placeholder-transparent focus:outline-none focus:border-indigo-500 hover:border-white/20 transition-all duration-300"
                    placeholder=" "
                    @focus="focusUsername = true"
                    @blur="focusUsername = false"
                  />
                  <label
                    for="login-username"
                    class="floating-label cosmic-floating-label"
                    :class="{ 'floating-label--active': form.username || focusUsername }"
                  >
                    Username or Email
                  </label>
                </div>
              </div>

              <!-- Password (floating label) -->
              <div class="input-wrap">
                <div class="input-group relative group">
                  <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors duration-300 cosmic-icon-wrap">
                    <LockClosedIcon class="h-5 w-5 cosmic-icon" />
                  </div>
                  <input
                    id="login-password"
                    v-model="form.password"
                    :type="showPassword ? 'text' : 'password'"
                    required
                    autocomplete="current-password"
                    class="auth-input cosmic-input w-full pl-11 pr-12 py-3 rounded-xl border border-white/10 bg-black/40 text-white placeholder-transparent focus:outline-none focus:border-indigo-500 hover:border-white/20 transition-all duration-300"
                    placeholder=" "
                    @focus="focusPassword = true"
                    @blur="focusPassword = false"
                  />
                  <label
                    for="login-password"
                    class="floating-label cosmic-floating-label"
                    :class="{ 'floating-label--active': form.password || focusPassword }"
                  >
                    Password
                  </label>
                  <button
                    type="button"
                    @click="showPassword = !showPassword"
                    class="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-500 hover:text-cyan-400 focus:outline-none transition-colors duration-300 cosmic-icon-wrap"
                    tabindex="-1"
                    :aria-label="showPassword ? 'Hide password' : 'Show password'"
                  >
                    <EyeIcon v-if="!showPassword" class="h-5 w-5 cosmic-icon" />
                    <EyeSlashIcon v-else class="h-5 w-5 cosmic-icon" />
                  </button>
                </div>
              </div>

              <!-- Submit -->
              <div class="pt-1">
                <button
                  type="submit"
                  :disabled="authStore.loading"
                  class="cosmic-btn auth-btn w-full py-3.5 px-4 rounded-xl font-semibold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-[#0B0E14] disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:bg-indigo-600 transition-all duration-300 flex items-center justify-center gap-2 min-h-[48px] shadow-lg hover:shadow-indigo-500/40 hover:shadow-xl active:scale-95"
                >
                  <template v-if="authStore.loading">
                    <svg
                      class="animate-spin h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Signing in…</span>
                  </template>
                  <template v-else>
                    <span>Sign in</span>
                    <ArrowRightIcon class="h-5 w-5" />
                  </template>
                </button>
              </div>

              <p class="text-right text-xs">
                <router-link to="/forgot-password" class="text-indigo-400 hover:text-indigo-300">
                  Forgot password?
                </router-link>
              </p>
            </form>

            <form v-else @submit.prevent="handle2fa" class="space-y-5">
              <div class="input-wrap">
                <label class="block text-sm text-slate-400 mb-2">Authenticator code</label>
                <input
                  v-model="code2fa"
                  type="text"
                  inputmode="numeric"
                  autocomplete="one-time-code"
                  maxlength="12"
                  class="auth-input cosmic-input w-full px-4 py-3 rounded-xl border border-white/10 bg-black/40 text-white focus:outline-none focus:border-indigo-500"
                  placeholder="123456"
                />
              </div>
              <button
                type="submit"
                :disabled="authStore.loading"
                class="cosmic-btn auth-btn w-full py-3.5 px-4 rounded-xl font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60"
              >
                {{ authStore.loading ? 'Verifying…' : 'Verify & continue' }}
              </button>
              <button type="button" class="text-sm text-slate-400 hover:text-white" @click="cancel2fa">
                Back to login
              </button>
            </form>

            <!-- Secondary action: Sign up -->
            <div class="mt-6 text-center">
              <p class="text-sm text-slate-400 mb-3">Don't have an account?</p>
              <router-link
                to="/signup"
                class="cosmic-secondary-link inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl border border-white/20 text-slate-300 font-medium text-sm hover:border-cyan-400/60 hover:text-cyan-400 hover:bg-cyan-400/10 focus:outline-none focus:ring-2 focus:ring-cyan-400/30 focus:ring-offset-2 focus:ring-offset-[#0B0E14] transition-all duration-300"
              >
                Sign up
              </router-link>
            </div>
          </div>
        </div>

        <router-link
          to="/"
          class="mt-6 flex items-center justify-center gap-2 text-sm text-slate-500 hover:text-slate-300 focus:outline-none focus:underline transition-colors duration-300"
        >
          <ArrowLeftIcon class="h-4 w-4" />
          Back to home
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotification } from '@/composables/useNotification'
import { normalizeApiError } from '@/utils/apiError'
import { pushLogin } from '@/analytics/dataLayer'
import {
  UserIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  ExclamationCircleIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const notify = useNotification()

const form = ref({
  username: '',
  password: '',
})
const showPassword = ref(false)
const focusUsername = ref(false)
const focusPassword = ref(false)
const needs2fa = ref(false)
const twoFactorToken = ref('')
const code2fa = ref('')

async function handleLogin() {
  try {
    authStore.error = null
    const credentials = {
      username: form.value.username.trim().toLowerCase(),
      password: form.value.password,
    }
    const result = await authStore.login(credentials)
    if (result?.needs2fa) {
      needs2fa.value = true
      twoFactorToken.value = result.twoFactorToken
      return
    }
    notify.success('Login successful!')
    pushLogin('password')
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    authStore.error = parsed.userMessage || 'Login failed. Please check your credentials.'
    // Inline alert above the form is enough; avoid duplicate toasts (interceptor + here).
  }
}

async function handle2fa() {
  try {
    authStore.error = null
    await authStore.complete2fa({
      twoFactorToken: twoFactorToken.value,
      code: code2fa.value,
    })
    notify.success('Login successful!')
    pushLogin('2fa')
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    authStore.error = parsed.userMessage || 'Invalid code.'
  }
}

function cancel2fa() {
  needs2fa.value = false
  twoFactorToken.value = ''
  code2fa.value = ''
  authStore.error = null
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push(route.query.redirect || '/dashboard')
  }
})
</script>

<style scoped>
.auth-page {
  position: relative;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Deep space gradient */
.cosmic-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(to bottom right, #0B0E14, #161B22, #0B0E14);
  pointer-events: none;
}

/* Animated starfield (CSS-only twinkling stars via box-shadow) */
.cosmic-starfield {
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  opacity: 0.6;
  animation: cosmicTwinkle 6s ease-in-out infinite;
}

.cosmic-starfield::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(1.5px 1.5px at 15% 25%, rgba(255,255,255,0.9), transparent),
    radial-gradient(1px 1px at 25% 15%, rgba(255,255,255,0.7), transparent),
    radial-gradient(1.5px 1.5px at 75% 30%, rgba(255,255,255,0.8), transparent),
    radial-gradient(1px 1px at 85% 20%, rgba(255,255,255,0.6), transparent),
    radial-gradient(1.5px 1.5px at 10% 60%, rgba(255,255,255,0.7), transparent),
    radial-gradient(1px 1px at 30% 70%, rgba(255,255,255,0.8), transparent),
    radial-gradient(1.5px 1.5px at 60% 80%, rgba(255,255,255,0.6), transparent),
    radial-gradient(1px 1px at 80% 55%, rgba(255,255,255,0.9), transparent),
    radial-gradient(1.5px 1.5px at 45% 35%, rgba(255,255,255,0.5), transparent),
    radial-gradient(1px 1px at 55% 45%, rgba(255,255,255,0.7), transparent),
    radial-gradient(1.5px 1.5px at 20% 85%, rgba(255,255,255,0.6), transparent),
    radial-gradient(1px 1px at 90% 75%, rgba(255,255,255,0.5), transparent),
    radial-gradient(1.5px 1.5px at 5% 40%, rgba(255,255,255,0.8), transparent),
    radial-gradient(1px 1px at 95% 50%, rgba(255,255,255,0.6), transparent),
    radial-gradient(1.5px 1.5px at 40% 10%, rgba(255,255,255,0.7), transparent),
    radial-gradient(1px 1px at 70% 65%, rgba(255,255,255,0.8), transparent);
  background-size: 100% 100%;
  background-repeat: repeat;
}

@keyframes cosmicTwinkle {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.9; }
}

/* Nebula accents */
.nebula {
  position: fixed;
  border-radius: 50%;
  filter: blur(100px);
  pointer-events: none;
  z-index: 1;
  opacity: 0.25;
}
.nebula--indigo {
  width: 400px;
  height: 400px;
  background: rgba(99, 102, 241, 0.4);
  top: -100px;
  right: -100px;
}
.nebula--purple {
  width: 350px;
  height: 350px;
  background: rgba(139, 92, 246, 0.35);
  bottom: -80px;
  left: -80px;
}

/* Glass-portal card */
.glass-portal {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* Galactic typography */
.cosmic-title,
.cosmic-heading {
  letter-spacing: 0.05em;
  text-shadow: 0 0 30px rgba(99, 102, 241, 0.2);
}

/* Input: dark sleek, power-up glow on focus */
.cosmic-input {
  border-color: rgba(255, 255, 255, 0.1);
}
.cosmic-input:focus {
  border-color: #6366F1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25), 0 0 20px rgba(99, 102, 241, 0.15);
}

/* Neon icon glow */
.cosmic-icon {
  filter: drop-shadow(0 0 4px rgba(99, 102, 241, 0.4));
}
.group-focus-within .cosmic-icon {
  filter: drop-shadow(0 0 6px rgba(99, 102, 241, 0.6));
}

/* Primary button: Electric Indigo + Cyan accent */
.cosmic-btn {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35);
}
.cosmic-btn:hover:not(:disabled) {
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.45), 0 0 40px rgba(34, 211, 238, 0.15);
}
.cosmic-btn:focus:not(:disabled) {
  box-shadow: 0 0 0 2px #0B0E14, 0 0 0 4px rgba(99, 102, 241, 0.5), 0 0 30px rgba(99, 102, 241, 0.3);
}

/* Floating label (cosmic): when active, label sits above input so it never overlaps typed text */
.cosmic-floating-label {
  color: rgb(148 163 184);
}
.floating-label--active.cosmic-floating-label {
  color: rgb(148 163 184);
}
.input-wrap {
  position: relative;
}
.input-wrap .input-group {
  margin-top: 0;
}
.floating-label {
  position: absolute;
  left: 0.75rem;
  top: -0.55rem;
  transform: none;
  font-size: 0.72rem;
  font-weight: 600;
  pointer-events: none;
  transition: color 0.2s ease;
  z-index: 2;
  padding: 0 0.35rem;
  border-radius: 999px;
  background: rgba(11, 14, 20, 0.92);
  line-height: 1.2;
}
.floating-label--active {
  top: -0.55rem;
}

.floating-label--active.cosmic-floating-label {
  color: rgb(165 180 252);
}

.cosmic-input:-webkit-autofill,
.cosmic-input:-webkit-autofill:hover,
.cosmic-input:-webkit-autofill:focus,
.cosmic-input:-webkit-autofill:active {
  -webkit-text-fill-color: #e2e8f0 !important;
  box-shadow: 0 0 0 1000px rgba(2, 6, 23, 0.55) inset !important;
  -webkit-box-shadow: 0 0 0 1000px rgba(2, 6, 23, 0.55) inset !important;
  caret-color: #e2e8f0 !important;
  transition: background-color 9999s ease-in-out 0s;
}
</style>
