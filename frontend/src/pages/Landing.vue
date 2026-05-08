<template>
  <div class="landing-page" :class="{ 'landing-menu-open': sectionMenuOpen }">
    <!-- Scroll Progress Indicator -->
    <div class="fixed top-0 left-0 right-0 h-1 z-50">
      <div 
        class="h-full bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 transition-all duration-150"
        :style="{ width: scrollProgress + '%' }"
      ></div>
    </div>

    <!-- Starfield Background -->
    <div class="fixed inset-0 starfield-background pointer-events-none z-0"></div>

    <!-- Top bar: burger (mobile) + logo + auth -->
    <nav class="landing-nav fixed top-0 left-0 right-0 z-40 backdrop-blur-xl bg-black/20 border-b border-white/10 safe-area-pt">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
        <div class="flex items-center justify-between gap-2 sm:gap-3 min-h-[2.5rem]">
          <div class="flex items-center gap-2 min-w-0 shrink">
          <!-- Wrapper hides entire control on lg+ so .landing-burger display:inline-flex cannot override lg:hidden -->
          <div class="shrink-0 lg:hidden">
            <button
              id="landing-section-menu-trigger"
              type="button"
              class="landing-burger"
              :class="{ 'is-open': sectionMenuOpen }"
              :aria-expanded="sectionMenuOpen"
              aria-controls="landing-section-menu"
              aria-label="Open menu"
              @click="toggleSectionMenu"
            >
              <span class="landing-burger-bar" aria-hidden="true" />
              <span class="landing-burger-bar" aria-hidden="true" />
              <span class="landing-burger-bar" aria-hidden="true" />
            </button>
          </div>
          <router-link
            to="/"
            class="flex items-center gap-2 min-w-0 shrink"
          >
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-purple-600 flex items-center justify-center shrink-0">
              <svg class="w-[1.125rem] h-[1.125rem] text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <span class="text-base sm:text-lg font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent truncate">
              PixelCast
            </span>
          </router-link>
          </div>
          <!-- Desktop / large: full nav (mobile uses burger drawer only) -->
          <div class="hidden lg:flex flex-wrap items-center justify-end gap-x-2 gap-y-1 xl:gap-2.5 shrink-0">
            <a
              :href="productDocsUrl"
              class="px-2 py-1.5 text-xs sm:text-sm text-white/80 hover:text-white transition-colors whitespace-nowrap"
            >
              Docs
            </a>
            <router-link
              to="/data-center"
              class="px-2 py-1.5 text-xs sm:text-sm text-white/80 hover:text-white transition-colors whitespace-nowrap"
            >
              Data Center
            </router-link>
            <template v-if="isInstalled">
              <router-link
                to="/login"
                class="px-2 py-1.5 text-xs sm:text-sm text-white/80 hover:text-white transition-colors"
              >
                Login
              </router-link>
              <router-link
                to="/signup"
                class="neon-button px-3.5 sm:px-5 py-1.5 rounded-lg text-xs sm:text-sm font-semibold text-white transition-all duration-300"
              >
                Get Started
              </router-link>
            </template>
            <template v-else>
              <router-link
                to="/install"
                class="neon-button px-3.5 sm:px-5 py-1.5 rounded-lg text-xs sm:text-sm font-semibold text-white transition-all duration-300"
              >
                Install
              </router-link>
            </template>
          </div>
        </div>
      </div>
    </nav>

    <!-- Mobile / tablet: backdrop + slide-out section menu (burger) -->
    <Transition name="landing-fade">
      <button
        v-if="sectionMenuOpen"
        type="button"
        class="landing-menu-backdrop fixed inset-0 z-[100] bg-black/55 backdrop-blur-[2px] lg:hidden"
        aria-label="Close menu"
        @click="closeSectionMenu"
      />
    </Transition>
    <Transition name="landing-drawer">
      <aside
        v-if="sectionMenuOpen"
        id="landing-section-menu"
        class="landing-section-drawer fixed top-0 right-0 z-[101] h-full w-[min(100%,20rem)] max-w-[100vw] border-l border-white/10 bg-slate-950/92 backdrop-blur-xl shadow-[-8px_0_40px_rgba(0,0,0,0.45)] lg:hidden safe-area-pt flex flex-col"
        role="dialog"
        aria-modal="true"
        aria-labelledby="landing-section-menu-title"
      >
        <div class="flex items-center justify-between gap-2 border-b border-white/10 px-4 py-3">
          <h2 id="landing-section-menu-title" class="text-sm font-semibold uppercase tracking-wider text-white/90">
            Menu
          </h2>
          <button
            type="button"
            class="rounded-lg p-2 text-white/70 hover:bg-white/10 hover:text-white transition-colors"
            aria-label="Close menu"
            @click="closeSectionMenu"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <nav class="flex-1 overflow-y-auto px-3 py-3" aria-label="Home menu">
          <!-- 1) Primary actions: conversion before secondary (Login only after Install / Get Started) -->
          <p class="landing-drawer-section-label">
            {{ isInstalled ? 'Get started' : 'Setup' }}
          </p>
          <ul class="mb-6 space-y-2">
            <template v-if="isInstalled">
              <li>
                <router-link
                  to="/signup"
                  class="landing-drawer-cta"
                  @click="closeSectionMenu"
                >
                  Get Started
                </router-link>
              </li>
              <li>
                <router-link to="/login" class="landing-drawer-quicklink" @click="closeSectionMenu">
                  Log in
                </router-link>
              </li>
            </template>
            <template v-else>
              <li>
                <router-link
                  to="/install"
                  class="landing-drawer-cta"
                  @click="closeSectionMenu"
                >
                  Install
                </router-link>
              </li>
              <li class="px-1 pt-1">
                <p class="text-[11px] leading-relaxed text-white/40">
                  Log in and sign up are available after your installation completes.
                </p>
              </li>
            </template>
          </ul>

          <p class="landing-drawer-section-label">Resources</p>
          <ul class="space-y-1 mb-6">
            <li>
              <a :href="productDocsUrl" class="landing-drawer-quicklink" @click="closeSectionMenu">
                Documentation
              </a>
            </li>
            <li>
              <router-link to="/data-center" class="landing-drawer-quicklink" @click="closeSectionMenu">
                Data Center
              </router-link>
            </li>
          </ul>

          <p class="landing-drawer-section-label">Legal</p>
          <ul class="space-y-1 safe-area-pb pb-2">
            <li>
              <router-link to="/privacy" class="landing-drawer-quicklink" @click="closeSectionMenu">
                Privacy Policy
              </router-link>
            </li>
            <li>
              <router-link to="/terms" class="landing-drawer-quicklink" @click="closeSectionMenu">
                Terms of Service
              </router-link>
            </li>
          </ul>
        </nav>
      </aside>
    </Transition>

    <!-- Scroll Container with Sections -->
    <div class="scroll-container">
      <!-- Hero Section -->
      <section 
        id="hero"
        class="section hero-section"
      >
        <div class="section-content">
          <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <div
              class="hero-align-grid grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-10 lg:gap-12 items-center h-full"
            >
              <div
                class="text-center lg:text-left section-fade-in space-y-5 md:space-y-6 max-w-2xl mx-auto lg:mx-0 lg:max-w-none"
              >
                <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight tracking-tight">
                  <span class="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500 bg-clip-text text-transparent">
                    Command Your Screens
                  </span>
                  <br>
                  <span class="text-white">From Deep Space</span>
                </h1>
                <p class="text-lg md:text-xl text-white/70 leading-relaxed max-w-xl mx-auto lg:mx-0">
                  Cloud and self-hosted digital signage software for commercial displays—LCD and LED screen networks, menu boards, and advertising screens with secure setup, remote control, and fleet monitoring.
                </p>
                <div
                  class="hero-cta-grid grid grid-cols-2 gap-2.5 sm:gap-3 md:gap-4 pt-1 w-full max-w-md sm:max-w-lg md:max-w-xl mx-auto lg:mx-0"
                >
                  <router-link
                    :to="isInstalled ? '/signup' : '/install'"
                    class="hero-cta-btn neon-button-large rounded-xl font-semibold !text-white visited:!text-white hover:!text-white transition-all duration-300 text-center inline-flex items-center justify-center w-full min-w-0 min-h-[3rem] sm:min-h-[3.25rem] px-2.5 sm:px-4 py-2.5 sm:py-3 text-xs sm:text-sm md:text-base leading-tight"
                    @click="trackLandingCta('hero_primary', isInstalled ? 'Start Free Trial' : 'Start Installation')"
                  >
                    {{ isInstalled ? 'Start Free Trial' : 'Start Installation' }}
                  </router-link>
                  <a
                    :href="productDocsUrl"
                    class="hero-cta-btn glass-card rounded-xl font-semibold !text-white visited:!text-white hover:!text-white border border-white/20 hover:border-white/40 transition-all duration-300 text-center inline-flex items-center justify-center w-full min-w-0 min-h-[3rem] sm:min-h-[3.25rem] px-2.5 sm:px-4 py-2.5 sm:py-3 text-xs sm:text-sm md:text-base leading-tight"
                    @click="trackLandingCta('hero_docs', 'Documentation')"
                  >
                    Documentation
                  </a>
                  <router-link
                    to="/data-center"
                    class="hero-cta-btn glass-card rounded-xl font-semibold !text-white visited:!text-white hover:!text-white border border-white/20 hover:border-white/40 transition-all duration-300 text-center inline-flex items-center justify-center w-full min-w-0 min-h-[3rem] sm:min-h-[3.25rem] px-2.5 sm:px-4 py-2.5 sm:py-3 text-xs sm:text-sm md:text-base leading-tight"
                    @click="trackLandingCta('hero_data_center', 'Data Center')"
                  >
                    Data Center
                  </router-link>
                  <button 
                    type="button"
                    @click="scrollToSectionById('features'); trackLandingCta('hero_explore', 'Explore Features')" 
                    class="hero-cta-btn glass-card rounded-xl font-semibold !text-white hover:!text-white border border-white/20 hover:border-white/40 transition-all duration-300 text-center inline-flex items-center justify-center w-full min-w-0 min-h-[3rem] sm:min-h-[3.25rem] px-2.5 sm:px-4 py-2.5 sm:py-3 text-xs sm:text-sm md:text-base leading-tight"
                  >
                    Explore Features
                  </button>
                </div>
                <div class="flex flex-wrap gap-x-6 gap-y-2 justify-center lg:justify-start pt-2 text-white/60 text-sm">
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-cyan-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                    </svg>
                    <span>No Credit Card</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-cyan-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                    </svg>
                    <span>14-Day Trial</span>
                  </div>
                </div>
              </div>
              <div
                class="relative section-fade-in hero-mockup-col hidden sm:block w-full max-w-md sm:max-w-lg md:max-w-xl mx-auto lg:max-w-none lg:mx-0 max-lg:scale-[0.94] max-lg:origin-top lg:scale-100 lg:origin-center"
                style="animation-delay: 0.2s"
              >
                <!-- Single floating device (one glass surface, 3/4 perspective) -->
                <div class="relative perspective-1000 max-w-lg mx-auto lg:max-w-none">
                  <div class="floating-mockup">
                    <div
                      class="hero-device glass-card rounded-2xl p-3 lg:p-4 shadow-2xl transform rotate-y-12 border border-white/15"
                    >
                      <div
                        class="hero-device-display relative overflow-hidden rounded-xl border border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]"
                      >
                        <div
                          class="relative aspect-[4/3] bg-gradient-to-br from-[#0c0828] via-[#1e1b4b] to-[#5b21b6] p-4 lg:p-5"
                        >
                          <div
                            class="pointer-events-none absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.04] to-transparent"
                            aria-hidden="true"
                          ></div>
                          <div
                            class="pointer-events-none absolute inset-0 backdrop-blur-[1px] bg-white/[0.02]"
                            aria-hidden="true"
                          ></div>
                          <div
                            class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/25 via-transparent to-indigo-950/20"
                            aria-hidden="true"
                          ></div>
                          <div class="relative z-10 flex h-full min-h-[11rem] flex-col lg:min-h-[14rem]">
                            <div class="mb-4 flex items-center justify-between">
                              <div class="h-2 w-20 rounded-full bg-white/25 lg:w-28"></div>
                              <div
                                class="h-2.5 w-2.5 animate-pulse rounded-full bg-cyan-400/90 shadow-[0_0_10px_rgba(34,211,238,0.55)]"
                              ></div>
                            </div>
                            <div class="mb-4 grid flex-1 grid-cols-3 gap-2">
                              <div
                                class="rounded-lg border border-white/10 bg-white/[0.06] backdrop-blur-sm"
                              ></div>
                              <div
                                class="rounded-lg border border-white/10 bg-white/[0.06] backdrop-blur-sm"
                              ></div>
                              <div
                                class="rounded-lg border border-white/10 bg-white/[0.06] backdrop-blur-sm"
                              ></div>
                            </div>
                            <div
                              class="h-16 rounded-lg border border-cyan-400/20 bg-gradient-to-r from-cyan-500/15 via-violet-500/10 to-purple-500/20 lg:h-20"
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Features Section -->
      <section 
        id="features"
        class="section features-section"
      >
        <div class="section-content">
          <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <div class="text-center mb-8 lg:mb-12 section-fade-in">
              <h2 class="text-3xl sm:text-3xl md:text-4xl lg:text-4xl font-bold mb-4 text-white">
                Powerful <span class="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">Features</span>
              </h2>
              <p class="text-base sm:text-lg md:text-xl text-white/60 max-w-3xl mx-auto leading-relaxed">
                Template editing, scheduling, remote control, and player pairing—everything you need to run screens at scale from one dashboard.
              </p>
            </div>
            <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
              <div 
                v-for="(feature, index) in features" 
                :key="index"
                class="glass-card p-6 lg:p-8 rounded-xl group feature-card feature-card-interactive"
                :style="{ animationDelay: `${index * 0.1}s` }"
              >
                <div class="w-12 lg:w-14 h-12 lg:h-14 rounded-xl bg-gradient-to-br from-cyan-400/20 to-purple-500/20 flex items-center justify-center mb-4 lg:mb-6 feature-icon-wrap">
                  <svg class="w-6 lg:w-7 h-6 lg:h-7 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="feature.iconPath" />
                  </svg>
                </div>
                <h3 class="text-xl lg:text-2xl font-bold !text-white mb-2 lg:mb-3">{{ feature.title }}</h3>
                <p class="!text-on-starfield leading-relaxed text-sm lg:text-base">{{ feature.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Live Pulse Section -->
      <section 
        id="pulse"
        class="section pulse-section"
      >
        <div class="section-content">
          <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <div class="text-center mb-8 lg:mb-12 section-fade-in">
              <h2 class="text-3xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-4 text-white">
                Live <span class="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">Pulse</span>
              </h2>
              <p class="text-base sm:text-lg md:text-xl text-white/60 max-w-2xl mx-auto leading-relaxed">
                See uptime, last sync, and what is playing—live from your control room, for every screen in your fleet.
              </p>
            </div>
            <div v-if="screensLoading" class="flex justify-center items-center py-12">
              <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-cyan-400"></div>
            </div>
            <div v-else-if="liveScreens.length === 0" class="flex flex-col items-center justify-center py-12 glass-card rounded-xl text-center">
              <svg class="w-12 h-12 text-white/30 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <p class="text-white/80 text-lg sm:text-xl font-medium">You don't have any screens yet. Please add some.</p>
            </div>
            <div v-else class="grid md:grid-cols-3 gap-4 lg:gap-6">
              <div 
                v-for="(screen, index) in liveScreens" 
                :key="index"
                class="glass-card p-5 lg:p-6 rounded-xl section-fade-in"
                :style="{ animationDelay: `${index * 0.15}s` }"
              >
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-lg lg:text-xl font-semibold text-white">{{ screen.name }}</h3>
                  <div class="flex items-center space-x-2">
                    <div 
                      class="w-2.5 lg:w-3 h-2.5 lg:h-3 rounded-full animate-pulse"
                      :class="screen.status === 'Online' ? 'bg-green-400' : 'bg-red-400'"
                    ></div>
                    <span class="text-xs lg:text-sm text-white/60">{{ screen.status }}</span>
                  </div>
                </div>
                <div class="space-y-2 lg:space-y-3">
                  <div class="flex justify-between text-xs lg:text-sm" v-if="screen.uptime !== 'N/A'">
                    <span class="text-white/60">Uptime</span>
                    <span class="text-white font-semibold">{{ screen.uptime }}</span>
                  </div>
                  <div class="flex justify-between text-xs lg:text-sm">
                    <span class="text-white/60">Last Sync</span>
                    <span class="text-white font-semibold">{{ screen.lastSync }}</span>
                  </div>
                  <div class="flex justify-between text-xs lg:text-sm">
                    <span class="text-white/60">Content</span>
                    <span class="text-white font-semibold">{{ screen.content }}</span>
                  </div>
                </div>
                <div class="mt-4 h-2 bg-slate-700/50 rounded-full overflow-hidden">
                  <div 
                    class="h-full bg-gradient-to-r from-cyan-400 to-purple-500 rounded-full transition-all duration-1000"
                    :style="{ width: screen.status === 'Online' ? '100%' : '0%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Industry Use Cases Section -->
      <section 
        id="industries"
        class="section industries-section"
      >
        <div class="section-content">
          <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <div class="text-center mb-8 lg:mb-12 section-fade-in">
              <h2 class="text-3xl sm:text-3xl md:text-3xl lg:text-4xl font-bold mb-4 text-white">
                Built for <span class="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">Every Industry</span>
              </h2>
              <p class="text-base sm:text-lg md:text-xl text-white/60 max-w-2xl mx-auto leading-relaxed">
                From retail menus to hospital signage—one platform for every screen, with content that updates as fast as your business.
              </p>
            </div>
            <div class="glass-card rounded-2xl p-6 lg:p-8 section-fade-in" style="animation-delay: 0.2s">
              <!-- Tabs: horizontal scroll on small screens -->
              <div class="industry-tabs -mx-2 px-2 mb-6 lg:mb-8 border-b border-white/10 pb-4 overflow-x-auto flex flex-nowrap gap-2 lg:gap-4 lg:flex-wrap">
                <button
                  v-for="(industry, index) in industries"
                  :key="index"
                  type="button"
                  @click="activeTab = index"
                  class="shrink-0 px-4 lg:px-6 py-2 lg:py-3 rounded-lg font-semibold text-sm lg:text-base transition-all duration-300 whitespace-nowrap"
                  :class="activeTab === index 
                    ? 'bg-gradient-to-r from-cyan-400 to-purple-500 !text-white shadow-[0_0_16px_rgba(6,182,212,0.25)]' 
                    : '!text-white/80 hover:!text-white hover:bg-white/5'"
                >
                  {{ industry.name }}
                </button>
              </div>
              <!-- Tab Content -->
              <div class="grid md:grid-cols-2 gap-6 lg:gap-8 items-center">
                <div class="text-white">
                  <h3 class="text-2xl lg:text-3xl font-bold !text-white mb-3 lg:mb-4">{{ industries[activeTab].title }}</h3>
                  <p class="!text-on-starfield mb-4 lg:mb-6 leading-relaxed text-sm lg:text-base">{{ industries[activeTab].description }}</p>
                  <ul class="space-y-2 lg:space-y-3">
                    <li 
                      v-for="(benefit, idx) in industries[activeTab].benefits" 
                      :key="idx"
                      class="flex items-start space-x-2 lg:space-x-3"
                    >
                      <svg class="w-5 lg:w-6 h-5 lg:h-6 text-cyan-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                      </svg>
                      <span class="!text-on-starfield text-sm lg:text-base">{{ benefit }}</span>
                    </li>
                  </ul>
                </div>
                <div class="relative">
                  <div class="glass-card p-4 lg:p-6 rounded-xl bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                    <div class="aspect-video rounded-lg overflow-hidden bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center">
                      <div class="text-center">
                        <svg class="w-16 lg:w-24 h-16 lg:h-24 mx-auto text-cyan-400/50 mb-3 lg:mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="industries[activeTab].iconPath" />
                        </svg>
                        <p class="text-white/40 text-xs lg:text-sm">{{ industries[activeTab].name }} Dashboard</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Tech Stack & CTA Section -->
      <section 
        id="cta"
        class="section cta-section"
      >
        <div class="section-content">
          <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <!-- Tech Stack -->
            <div class="glass-card rounded-xl p-5 lg:p-6 text-center mb-6 lg:mb-8 section-fade-in">
              <p class="!text-on-starfield mb-3 lg:mb-4 text-sm lg:text-base">Powered by</p>
              <div class="flex flex-wrap justify-center items-center gap-4 lg:gap-6">
                <div class="flex items-center space-x-2 !text-on-starfield text-sm lg:text-base">
                  <svg class="w-5 lg:w-6 h-5 lg:h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span class="font-semibold">IoT</span>
                </div>
                <div class="flex items-center space-x-2 !text-on-starfield text-sm lg:text-base">
                  <svg class="w-5 lg:w-6 h-5 lg:h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  <span class="font-semibold">Real-time Sync</span>
                </div>
                <div class="flex items-center space-x-2 !text-on-starfield text-sm lg:text-base">
                  <svg class="w-5 lg:w-6 h-5 lg:h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                  </svg>
                  <span class="font-semibold">Cloud Infrastructure</span>
                </div>
                <div class="flex items-center space-x-2 !text-on-starfield text-sm lg:text-base">
                  <svg class="w-5 lg:w-6 h-5 lg:h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                  <span class="font-semibold">Stripe</span>
                </div>
              </div>
            </div>
            <!-- CTA -->
            <div class="glass-card rounded-2xl p-8 lg:p-12 section-fade-in" style="animation-delay: 0.2s">
              <h2 class="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 lg:mb-6 text-white">
                Ready to Launch Your Digital Network?
              </h2>
              <p class="text-lg lg:text-xl text-white/70 mb-6 lg:mb-8 max-w-2xl mx-auto">
                Deploy quickly with guided installation, then manage all screens from one control center.
              </p>
              <div
                class="grid grid-cols-1 min-[420px]:grid-cols-2 xl:grid-cols-4 gap-4 justify-items-stretch max-w-4xl mx-auto w-full"
              >
                <router-link
                  :to="isInstalled ? '/signup' : '/install'"
                  class="neon-button-large px-6 py-4 rounded-lg font-semibold text-base sm:text-lg text-white transition-all duration-300 text-center inline-flex items-center justify-center w-full min-h-[3.25rem]"
                >
                  {{ isInstalled ? 'Start Free Trial' : 'Install Now' }}
                </router-link>
                <a
                  :href="productDocsUrl"
                  class="glass-card px-6 py-4 rounded-lg font-semibold text-base sm:text-lg text-white border border-white/20 hover:border-white/40 transition-all duration-300 text-center inline-flex items-center justify-center w-full min-h-[3.25rem]"
                >
                  View Docs
                </a>
                <router-link
                  to="/data-center"
                  class="glass-card px-6 py-4 rounded-lg font-semibold text-base sm:text-lg text-white border border-white/20 hover:border-white/40 transition-all duration-300 text-center inline-flex items-center justify-center w-full min-h-[3.25rem]"
                >
                  Data Center
                </router-link>
                <router-link
                  v-if="isInstalled"
                  to="/login"
                  class="glass-card px-6 py-4 rounded-lg font-semibold text-base sm:text-lg text-white border border-white/20 hover:border-white/40 transition-all duration-300 text-center inline-flex items-center justify-center w-full min-h-[3.25rem]"
                >
                  Sign In
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Compact footer -->
      <footer class="landing-footer border-t border-white/10 bg-black/20 backdrop-blur-md safe-area-pb">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row flex-wrap items-center justify-between gap-4 text-sm text-white/55">
          <p class="text-center sm:text-left">
            © {{ footerYear }} PixelCast. All rights reserved.
          </p>
          <div class="flex flex-wrap items-center justify-center gap-x-5 gap-y-2">
            <router-link to="/privacy" class="hover:text-white transition-colors">Privacy</router-link>
            <router-link to="/terms" class="hover:text-white transition-colors">Terms</router-link>
            <a :href="productDocsUrl" class="hover:text-white transition-colors">Docs</a>
            <router-link to="/data-center" class="hover:text-white transition-colors">Data Center</router-link>
          </div>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { setupAPI, screensAPI } from '@/services/api'
import { pushCtaClick } from '@/analytics/dataLayer'

function trackLandingCta(ctaId, label) {
  pushCtaClick(ctaId, label, { page: 'landing' })
}

/** Static HTML product docs (Vite `public/documentation/` → `/documentation/index.html`). */
const productDocsUrl = '/documentation/index.html'

const scrollProgress = ref(0)
const activeTab = ref(0)
const isInstalled = ref(true)
const sectionMenuOpen = ref(false)

const footerYear = computed(() => new Date().getFullYear())

const closeSectionMenu = () => {
  sectionMenuOpen.value = false
}

const toggleSectionMenu = () => {
  sectionMenuOpen.value = !sectionMenuOpen.value
}

const liveScreens = ref([])
const screensLoading = ref(true)

const fetchScreens = async () => {
  try {
    screensLoading.value = true
    const response = await screensAPI.list({ limit: 6 })
    let screens = []
    if (response.data?.results && Array.isArray(response.data.results)) {
      screens = response.data.results
    } else if (Array.isArray(response.data)) {
      screens = response.data
    } else if (response.data?.data && Array.isArray(response.data.data)) {
      screens = response.data.data
    }
    
    liveScreens.value = screens.slice(0, 6).map(screen => {
      let lastSyncStr = 'N/A'
      if (screen.last_ping) {
        lastSyncStr = new Date(screen.last_ping).toLocaleTimeString()
      } else if (screen.last_heartbeat) {
        lastSyncStr = new Date(screen.last_heartbeat).toLocaleTimeString()
      }

      return {
        name: screen.name || 'Unnamed Screen',
        status: screen.is_online ? 'Online' : 'Offline',
        uptime: 'N/A',
        lastSync: lastSyncStr,
        content: screen.current_template_name || screen.current_content_name || 'No Active Content'
      }
    })
  } catch (err) {
    console.error("Failed to fetch screens for Live Pulse:", err)
    liveScreens.value = []
  } finally {
    screensLoading.value = false
  }
}

const features = ref([
  {
    title: 'Template editor',
    description:
      'Build layouts with widgets, layers, and precise placement—no code required. Design once, reuse across screens, and keep branding consistent everywhere.',
    iconPath:
      'M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z',
  },
  {
    title: 'Schedules',
    description:
      'Decide what plays when. Tie templates and content to time windows so promotions, menus, and dayparts switch automatically.',
    iconPath: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
  },
  {
    title: 'Remote commands',
    description:
      'Send commands to players from the dashboard—refresh, reboot, clear cache, or trigger updates without visiting the device.',
    iconPath: 'M13 10V3L4 14h7v7l9-11h-7z',
  },
  {
    title: 'Web player & pairing',
    description:
      'Pair browsers and devices with a secure flow, then deliver your templates as a full-screen web player for kiosks and displays.',
    iconPath:
      'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
  },
  {
    title: 'Users & permissions',
    description:
      'Invite teammates and control who can edit templates, manage screens, or view logs—role-based access that matches how you run operations.',
    iconPath:
      'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
  },
  {
    title: 'Logs & monitoring',
    description:
      'Audit activity, diagnose issues, and watch fleet health. Pair Live Pulse with detailed logs for compliance and faster support.',
    iconPath:
      'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  },
])

const industries = ref([
  {
    name: 'Retail',
    title: 'Transform Retail Experiences',
    description:
      'Engage shoppers with dynamic displays, promotions, and wayfinding. Push template updates and pricing to every store from one dashboard.',
    benefits: [
      'Real-time price updates across all stores',
      'Dynamic promotional content scheduling',
      'Customer engagement analytics',
      'Multi-location content management'
    ],
    iconPath: 'M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z'
  },
  {
    name: 'Healthcare',
    title: 'Enhance Patient Communication',
    description:
      'Show wait times, directions, and health messaging on lobby and ward screens. Update content safely when plans or policies change.',
    benefits: [
      'Real-time wait time displays',
      'Appointment scheduling integration',
      'Health information broadcasting',
      'Emergency alert systems'
    ],
    iconPath: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z'
  },
  {
    name: 'F&B',
    title: 'Elevate Dining Experiences',
    description:
      'Showcase menus, dayparts, and specials on every display. Schedule breakfast versus dinner layouts and refresh items in seconds.',
    benefits: [
      'Dynamic menu displays',
      'Promotional content scheduling',
      'Multi-language support',
      'Nutritional information display'
    ],
    iconPath: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253'
  }
])

// Scroll to section (by index — legacy)
const scrollToSection = (index) => {
  const scrollContainer = document.querySelector('.scroll-container')
  if (scrollContainer) {
    const sections = scrollContainer.querySelectorAll(':scope > section')
    if (sections[index]) {
      sections[index].scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }
}

const scrollToSectionById = (id) => {
  const scrollContainer = document.querySelector('.scroll-container')
  const el = document.getElementById(id)
  if (scrollContainer && el && scrollContainer.contains(el)) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } else if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function onLandingKeydown(e) {
  if (e.key === 'Escape') {
    closeSectionMenu()
  }
}

/** Close drawer when viewport crosses to desktop (lg) so scroll-lock is cleared */
let desktopMenuMedia = null
function onDesktopMenuBreakpoint() {
  if (desktopMenuMedia?.matches) closeSectionMenu()
}

function updateScrollProgress() {
  const scrollContainer = document.querySelector('.scroll-container')
  if (!scrollContainer) return
  const scrollTop = scrollContainer.scrollTop
  const totalHeight = scrollContainer.scrollHeight - scrollContainer.clientHeight
  scrollProgress.value = totalHeight > 0 ? (scrollTop / totalHeight) * 100 : 0
}

onMounted(() => {
  window.addEventListener('keydown', onLandingKeydown)
  if (typeof window !== 'undefined' && window.matchMedia) {
    desktopMenuMedia = window.matchMedia('(min-width: 1024px)')
    desktopMenuMedia.addEventListener('change', onDesktopMenuBreakpoint)
  }

  // Enable scrolling
  document.body.style.overflow = 'auto'
  document.body.style.height = 'auto'
  document.documentElement.style.overflow = 'auto'
  document.documentElement.style.height = 'auto'
  
  const appContainer = document.querySelector('#app')
  if (appContainer) {
    appContainer.style.overflow = 'auto'
    appContainer.style.height = 'auto'
  }
  
  const appDiv = document.querySelector('#app > div')
  if (appDiv) {
    appDiv.style.overflow = 'auto'
    appDiv.style.height = 'auto'
  }
  
  const scrollContainer = document.querySelector('.scroll-container')
  if (scrollContainer) {
    scrollContainer.addEventListener('scroll', updateScrollProgress, { passive: true })
    updateScrollProgress()
  }

  // Landing behavior: show Install CTA when setup is not completed.
  setupAPI.status()
    .then((response) => {
      isInstalled.value = Boolean(response?.data?.installed)
      if (isInstalled.value) {
        fetchScreens()
      } else {
        screensLoading.value = false
      }
    })
    .catch(() => {
      // Default to installed mode on network/API issues.
      isInstalled.value = true
      fetchScreens()
    })

})

onUnmounted(() => {
  window.removeEventListener('keydown', onLandingKeydown)
  desktopMenuMedia?.removeEventListener('change', onDesktopMenuBreakpoint)

  const scrollContainer = document.querySelector('.scroll-container')
  if (scrollContainer) {
    scrollContainer.removeEventListener('scroll', updateScrollProgress)
  }
})
</script>

<style scoped>
.landing-page {
  position: relative;
  width: 100%;
  min-height: 100dvh;
  height: 100dvh;
  overflow: hidden;
  /* Always use light copy tokens here — global :root is light-theme when html has no .dark */
  --text-body: #e2e8f0;
  --text-main: #e2e8f0;
  --text-heading: #f8fafc;
  --text-muted: #94a3b8;
  color: var(--text-body);
  color-scheme: dark;
  background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 25%, #0f172a 50%, #1e293b 75%, #0a0e27 100%);
  background-size: 400% 400%;
  animation: gradientShift 20s ease infinite;
}

.safe-area-pt {
  padding-top: max(0.5rem, env(safe-area-inset-top));
}

.safe-area-pb {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}

/* Burger button (mobile / tablet) */
.landing-burger {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.625rem;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.landing-burger:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.28);
}

.landing-burger-bar {
  display: block;
  height: 2px;
  width: 1.125rem;
  border-radius: 1px;
  background: currentColor;
  transition:
    transform 0.25s cubic-bezier(0.4, 0, 0.2, 1),
    opacity 0.2s ease;
  transform-origin: center;
}

.landing-burger.is-open .landing-burger-bar:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}

.landing-burger.is-open .landing-burger-bar:nth-child(2) {
  opacity: 0;
  transform: scaleX(0);
}

.landing-burger.is-open .landing-burger-bar:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

.landing-menu-open .scroll-container {
  overflow: hidden !important;
  touch-action: none;
}

.landing-drawer-section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 0.5rem;
  padding-left: 0.35rem;
}

.landing-drawer-quicklink {
  display: block;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.85);
  transition: background 0.15s ease, color 0.15s ease;
}

.landing-drawer-quicklink:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.landing-drawer-cta {
  display: block;
  text-align: center;
  padding: 0.65rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #fff !important;
  background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
  box-shadow: 0 0 18px rgba(6, 182, 212, 0.28);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

@media (hover: hover) and (pointer: fine) {
  .landing-drawer-cta:hover {
    box-shadow: 0 0 26px rgba(6, 182, 212, 0.45);
  }
}

.landing-fade-enter-active,
.landing-fade-leave-active {
  transition: opacity 0.2s ease;
}

.landing-fade-enter-from,
.landing-fade-leave-to {
  opacity: 0;
}

.landing-drawer-enter-active,
.landing-drawer-leave-active {
  transition:
    transform 0.28s cubic-bezier(0.4, 0, 0.2, 1),
    opacity 0.2s ease;
}

.landing-drawer-enter-from,
.landing-drawer-leave-to {
  transform: translateX(100%);
  opacity: 0.96;
}

.scroll-container {
  height: 100dvh;
  max-height: 100dvh;
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth;
  scroll-padding-top: 5.75rem;
  -ms-overflow-style: none;
  scrollbar-width: none;
  position: relative;
}

@media (min-width: 1024px) {
  .scroll-container {
    scroll-padding-top: 5.5rem;
  }
}

.scroll-container::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
}

.section {
  min-height: 100dvh;
  height: auto;
  width: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding-top: max(5.75rem, calc(env(safe-area-inset-top) + 4.5rem));
  padding-bottom: max(2rem, env(safe-area-inset-bottom));
}

@media (min-width: 1024px) {
  .section {
    /* min-height only: tall sections (e.g. features) grow with content; scroll stays on .scroll-container */
    min-height: 100dvh;
    height: auto;
    padding-top: max(5rem, env(safe-area-inset-top));
    padding-bottom: 40px;
  }
}

.section-content {
  width: 100%;
  min-height: 0;
  height: auto;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-height: none;
  overflow-y: visible;
  overflow-x: hidden;
}

/* Background gradient animation */

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* Starfield Background */
.starfield-background {
  background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
  overflow: hidden;
}

.starfield-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(2px 2px at 20% 30%, white, transparent),
    radial-gradient(2px 2px at 60% 70%, white, transparent),
    radial-gradient(1px 1px at 50% 50%, white, transparent),
    radial-gradient(1px 1px at 80% 10%, white, transparent),
    radial-gradient(2px 2px at 30% 80%, white, transparent),
    radial-gradient(1px 1px at 90% 40%, white, transparent);
  background-repeat: repeat;
  background-size: 200% 200%;
  animation: starfield 20s linear infinite;
  opacity: 0.6;
}

@keyframes starfield {
  from { transform: translateY(0); }
  to { transform: translateY(-2000px); }
}

/*
 * Solid frosted surface (no backdrop-filter): matches app card-base stability note in style.css —
 * blur + global light theme caused body/heading tokens to composite as dark text until repaint
 * (e.g. full viewport vs DevTools docked).
 */
.glass-card {
  background: rgba(15, 23, 42, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}

/* Neon Buttons */
.neon-button {
  background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
  transition: all 0.3s ease;
}

@media (hover: hover) and (pointer: fine) {
  .neon-button:hover {
    box-shadow: 0 0 30px rgba(6, 182, 212, 0.6), 0 0 50px rgba(139, 92, 246, 0.4);
    transform: translateY(-2px);
  }
}

.neon-button-large {
  background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
  box-shadow: 0 0 25px rgba(6, 182, 212, 0.4);
  transition: all 0.3s ease;
}

@media (hover: hover) and (pointer: fine) {
  .neon-button-large:hover {
    box-shadow: 0 0 40px rgba(6, 182, 212, 0.7), 0 0 60px rgba(139, 92, 246, 0.5);
    transform: translateY(-3px) scale(1.02);
  }
}

/* Hero CTAs: body/link inherit would otherwise use --text-body (dark in light mode). */
.hero-cta-grid .hero-cta-btn {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff;
}

.hero-cta-grid .hero-cta-btn:hover,
.hero-cta-grid .hero-cta-btn:visited,
.hero-cta-grid .hero-cta-btn:active {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff;
}

/* Floating 3D Mockup */
.perspective-1000 {
  perspective: 1000px;
}

.floating-mockup {
  animation: float 6s ease-in-out infinite;
  transform-style: preserve-3d;
  will-change: transform;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotateX(0deg) rotateY(0deg);
  }
  50% {
    transform: translateY(-20px) rotateX(5deg) rotateY(5deg);
  }
}

.rotate-y-12 {
  transform: rotateY(12deg);
}

.hero-device {
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.09) 0%,
    rgba(255, 255, 255, 0.04) 50%,
    rgba(255, 255, 255, 0.07) 100%
  );
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.06) inset;
}

/* Fade-in animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-fade-in {
  opacity: 0;
  animation: fadeInUp 0.8s ease-out forwards;
}

.feature-card {
  opacity: 0;
  animation: fadeInUp 0.6s ease-out forwards;
}

/* Fullscreen stability:
   Features/Industries are content-heavy; top-align them on large screens
   to prevent heading clipping with fixed nav + full-height sections. */
.features-section .section-content,
.industries-section .section-content {
  justify-content: flex-start;
  padding-top: 1rem;
}

@media (max-width: 1023px) {
  .features-section .section-content,
  .industries-section .section-content,
  .pulse-section .section-content,
  .cta-section .section-content {
    justify-content: flex-start;
    padding-top: 0.5rem;
    padding-bottom: 1rem;
  }
}

.industry-tabs {
  -ms-overflow-style: none;
  scrollbar-width: thin;
}

.industry-tabs::-webkit-scrollbar {
  height: 4px;
}

.industry-tabs::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

@media (hover: hover) and (pointer: fine) {
  .feature-card-interactive {
    transition: transform 0.3s ease;
  }

  .feature-card-interactive:hover {
    transform: scale(1.03);
  }

  .feature-card-interactive:hover .feature-icon-wrap {
    transform: scale(1.1);
  }
}

.feature-icon-wrap {
  transition: transform 0.3s ease;
}

/* Accessibility - Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  .landing-page,
  .starfield-background::before,
  .floating-mockup,
  .feature-card,
  .section-fade-in {
    animation: none !important;
  }
  
  .scroll-container {
    scroll-behavior: auto;
  }
  
  .neon-button:hover,
  .neon-button-large:hover {
    transform: none !important;
  }
}

/* Mobile Optimizations */
@media (max-width: 1023px) {
  .section-content {
    padding: 12px 0 20px;
  }
}

@media (max-width: 768px) {
  .glass-card {
    padding: 1rem;
  }

  /* Hero CTA grid: keep compact padding (global .glass-card rule above uses padding shorthand). */
  .hero-cta-grid .hero-cta-btn {
    padding: 0.625rem 0.5rem;
  }

  @media (min-width: 480px) {
    .hero-cta-grid .hero-cta-btn {
      padding: 0.75rem 0.875rem;
    }
  }
}

</style>
