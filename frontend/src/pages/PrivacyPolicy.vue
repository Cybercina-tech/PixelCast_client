<template>
  <div class="terms-page min-h-screen text-slate-200">
    <div class="terms-starfield pointer-events-none fixed inset-0 z-0" aria-hidden="true" />
    <div class="terms-animated-bg fixed inset-0 z-0 opacity-90" aria-hidden="true" />

    <header
      class="sticky top-0 z-50 border-b border-white/10 bg-slate-950/75 backdrop-blur-xl safe-area-pt"
    >
      <div class="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <router-link
          :to="backRoute"
          class="group inline-flex items-center gap-2 text-sm font-medium text-white/80 transition-colors hover:text-cyan-300"
        >
          <ArrowLeftIcon class="h-5 w-5 shrink-0 transition-transform group-hover:-translate-x-0.5" />
          <span>{{ backText }}</span>
        </router-link>
        <router-link
          to="/terms"
          class="hidden text-xs font-medium text-white/55 hover:text-cyan-300 sm:inline sm:text-sm"
        >
          Terms of Service
        </router-link>
      </div>
    </header>

    <main class="relative z-10 mx-auto max-w-4xl px-4 pb-20 pt-10 sm:px-6 lg:px-8">
      <div class="mb-12 text-center sm:mb-14">
        <div
          class="mx-auto mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-400/25 bg-gradient-to-br from-cyan-500/20 to-purple-600/25 shadow-[0_0_40px_rgba(34,211,238,0.15)]"
        >
          <ShieldCheckIcon class="h-8 w-8 text-cyan-300" />
        </div>
        <p class="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400/90">
          Privacy &amp; data
        </p>
        <h1 class="mb-4 text-3xl font-bold tracking-tight text-white sm:text-4xl md:text-5xl">
          <span
            class="bg-gradient-to-r from-cyan-300 via-blue-300 to-purple-400 bg-clip-text text-transparent"
          >
            Privacy Policy
          </span>
        </h1>
        <p class="flex flex-wrap items-center justify-center gap-2 text-sm text-white/55">
          <ClockIcon class="h-4 w-4 text-cyan-400/80" />
          <span>Last updated <strong class="font-semibold text-white/80">{{ lastUpdated }}</strong></span>
        </p>
        <p class="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-slate-400">
          This Policy explains what personal data we process, why, and your rights—especially if you are in the EEA, UK,
          or other regions with privacy laws such as the GDPR. Read it together with our
          <router-link class="terms-link" to="/terms">Terms of Service</router-link>.
        </p>
      </div>

      <div class="space-y-8 md:space-y-10">
        <!-- 1 -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">1</span>
            Scope &amp; agreement
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              This Privacy Policy (“<strong>Policy</strong>”) describes how the operator of PixelCast
              (“<strong>PixelCast</strong>,” “<strong>we</strong>,” “<strong>us</strong>,” or “<strong>our</strong>”)
              processes <strong>personal data</strong> when you use our websites, applications, APIs, and related services
              (collectively, the “<strong>Service</strong>”).
            </p>
            <p>
              By using the Service, you acknowledge this Policy. If you use the Service on behalf of an organization, you
              represent that you are authorized to bind it. If you do not agree, do not use the Service.
            </p>
          </div>
        </section>

        <!-- 2 Dual deployment - KEY -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">2</span>
            SaaS vs Self-Hosted: where your data lives
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              PixelCast can be used as a <strong>hosted cloud product (SaaS)</strong> or as <strong>software you install on
              your own servers (Self-Hosted)</strong>. Your role, our role, and the location of databases differ materially
              between these models.
            </p>
            <h3 class="terms-h3">SaaS (we host the application)</h3>
            <p>
              We host the application and, in the ordinary course, <strong>store and process Customer Content and account
              data on infrastructure we operate or procure</strong> (for example cloud hosting providers). For personal
              data relating to your users and your signage operations in that environment, you are typically the
              <strong>data controller</strong> (or business) for your organization’s decisions about what to process, and we
              act as a <strong>data processor</strong> or service provider for the processing we perform on your
              instructions to run the Service—subject to your agreement and applicable law.
            </p>
            <p>
              <strong>Security of the hosted stack</strong> (patching our managed components, logical access controls on
              systems we operate, and subprocessors we engage subject to contract) is our responsibility within the scope
              of the Service as offered, alongside your obligation to protect credentials and configure your tenant
              appropriately.
            </p>
            <h3 class="terms-h3">Self-Hosted (you host the application)</h3>
            <p>
              When you run PixelCast on infrastructure you control, <strong>your databases and the majority of Content and
              end-user personal data you collect typically reside on your systems</strong>. We do <strong>not</strong> have
              routine access to your production database merely because you use Self-Hosted software.
            </p>
            <p>
              We may still process limited personal data for <strong>billing, licensing, marketplace, support, or
              compliance</strong> when you interact with us directly (for example your name, email, company, payment
              references, support tickets). Separately, if you enable <strong>optional license validation, registry, or
              telemetry</strong> features in your deployment, limited technical or license-related data may be
              transmitted to us or to services we operate—see Section 7.
            </p>
            <p>
              <strong>Your responsibilities (Self-Hosted).</strong> You are responsible for lawful processing on your
              systems, backups, retention, breach notification to your users or regulators where required, and securing your
              servers, networks, and configuration.
            </p>
          </div>
        </section>

        <!-- 3 Data collected -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">3</span>
            Personal data we collect
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              Categories below may not all apply to every customer. Self-Hosted deployments often process the bulk of
              operational and end-user data locally; we still collect the categories needed to provide licenses, support,
              and our websites as described.
            </p>
            <h3 class="terms-h3">Data you provide directly</h3>
            <ul class="terms-list">
              <li v-for="(d, i) in directData" :key="i">{{ d }}</li>
            </ul>
            <h3 class="terms-h3">Data collected automatically</h3>
            <ul class="terms-list">
              <li v-for="(d, i) in automaticData" :key="'a' + i">{{ d }}</li>
            </ul>
            <h3 class="terms-h3">Content and configuration</h3>
            <p>
              Templates, media, schedules, device metadata, audit entries, and similar items may contain personal data if
              you choose to include it. In SaaS, we process such data to operate the Service; in Self-Hosted, you process
              it on your infrastructure.
            </p>
            <h3 class="terms-h3">Billing (paid offerings)</h3>
            <p>
              Payment processors may collect billing address, payment method details, and transaction history. We receive
              limited billing records needed to administer your account.
            </p>
          </div>
        </section>

        <!-- 4 Purposes -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">4</span>
            Why we use personal data
          </h2>
          <div class="terms-prose space-y-4">
            <p>We use personal data for purposes such as:</p>
            <ul class="terms-list">
              <li v-for="(item, i) in usagePurposes" :key="i">{{ item }}</li>
            </ul>
            <p>
              We do not sell your personal data. We may use aggregated or de-identified information that does not identify
              you for analytics or product improvement where permitted by law.
            </p>
          </div>
        </section>

        <!-- 5 Legal bases -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">5</span>
            Legal bases (EEA, UK, and similar laws)
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              Where GDPR, UK GDPR, or similar laws apply, we rely on appropriate bases such as: performance of a contract;
              legitimate interests (securing the Service, preventing abuse, improving reliability) where not overridden by
              your rights; consent where we request it; legal obligation; and, rarely, vital interests.
            </p>
            <p>This summary is for transparency and is not legal advice. Contact us (Section 17) for questions.</p>
          </div>
        </section>

        <!-- 6 Sharing -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">6</span>
            Sharing with third parties
          </h2>
          <div class="terms-prose space-y-4">
            <p>We may disclose personal data as follows:</p>
            <ul class="terms-list">
              <li v-for="(item, i) in sharingItems" :key="i">{{ item }}</li>
            </ul>
            <p>
              <strong>Examples of categories of recipients</strong> depending on features you use: payment processors
              (e.g. Stripe), cloud hosting and infrastructure providers, email and SMS delivery (e.g. SMTP or Twilio),
              authentication or security vendors, analytics subprocessors, and professional advisers where required.
            </p>
            <p>
              We require service providers to protect personal data and use it only for the purposes we specify, subject to
              contract and law.
            </p>
          </div>
        </section>

        <!-- 7 Telemetry -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">7</span>
            License validation &amp; telemetry (Self-Hosted)
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              Self-Hosted builds may include <strong>optional</strong> features that contact PixelCast or a license
              gateway (for example to validate a license key, report deployment metadata, or support registry/heartbeat
              functionality when enabled in your configuration). If active, such features may transmit limited technical
              or administrative data (for example license identifiers, version strings, timestamps, or error diagnostics).
            </p>
            <p>
              <strong>You must disclose such processing to your own users and administrators</strong> where your local
              law requires transparency, and configure or disable features in line with your compliance obligations. See
              your deployment documentation and environment variables for what is enabled in your build.
            </p>
          </div>
        </section>

        <!-- 8 International -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">8</span>
            International transfers
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              We may process and store personal data in countries other than where you live. When transferring from the
              EEA, UK, or Switzerland, we use appropriate safeguards where required, such as standard contractual clauses
              or other lawful mechanisms.
            </p>
          </div>
        </section>

        <!-- 9 Retention -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">9</span>
            Retention
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              We retain personal data as long as needed to provide the Service, comply with law, resolve disputes, and
              enforce agreements. Periods vary by data type and legal requirements. When no longer needed, we delete or
              de-identify data subject to backup and disaster-recovery constraints.
            </p>
          </div>
        </section>

        <!-- 10 Security -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">10</span>
            Security
          </h2>
          <div class="terms-prose space-y-4">
            <p>We implement technical and organizational measures designed to protect personal data, including:</p>
            <ul class="terms-list">
              <li v-for="(m, i) in securityMeasures" :key="i">
                <strong>{{ m.title }}.</strong> {{ m.description }}
              </li>
            </ul>
            <p>
              No method of transmission or storage is completely secure. Where notification is required by law, we will
              follow applicable breach notification rules for personal data we control.
            </p>
          </div>
        </section>

        <!-- 11 Rights -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">11</span>
            Your privacy rights
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              Depending on your location, you may have rights to <strong>access</strong> your personal data,
              <strong>correct</strong> inaccuracies, <strong>delete</strong> data (“right to be forgotten” where
              applicable), <strong>restrict</strong> or <strong>object</strong> to certain processing,
              <strong>port</strong> data to another service, and <strong>withdraw consent</strong> where processing was
              based on consent.
            </p>
            <p>
              To exercise rights that apply to you, contact us using Section 17. We may need to verify your identity. If
              you are a Self-Hosted customer and ask us to delete data we hold about <em>your</em> account or license, we
              will respond subject to law; requests about end-users whose data sits on <em>your</em> servers must usually
              be handled by your organization as controller.
            </p>
            <p>
              You may lodge a complaint with a supervisory authority. California and other U.S. state residents may have
              additional rights; contact us for applicable disclosures.
            </p>
          </div>
        </section>

        <!-- 12 Cookies -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">12</span>
            Cookies &amp; similar technologies
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              We use cookies, local storage, and similar technologies to operate the Service, maintain sessions, remember
              preferences, protect against fraud, and understand usage. Some are strictly necessary; others may require
              consent depending on region.
            </p>
            <p>
              You can control cookies through browser settings. Blocking some cookies may affect functionality (for example
              staying signed in).
            </p>
          </div>
        </section>

        <!-- 13 Children -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">13</span>
            Children’s privacy
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              The Service is not directed to children under the minimum age required in your jurisdiction (often 16). We
              do not knowingly collect personal data from children for marketing. Contact us if you believe we have done
              so in error.
            </p>
          </div>
        </section>

        <!-- 14 Third party -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">14</span>
            Third-party links &amp; services
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              The Service may link to or integrate third-party sites or services. Their privacy practices govern data they
              collect. We are not responsible for their content or security.
            </p>
          </div>
        </section>

        <!-- 15 Table -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">15</span>
            SaaS vs Self-Hosted at a glance
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              The following summary highlights structural differences. It does not replace the full Policy or your
              agreements.
            </p>
            <div class="terms-table-wrap">
              <table class="terms-table">
                <thead>
                  <tr>
                    <th scope="col">Topic</th>
                    <th scope="col">SaaS (cloud)</th>
                    <th scope="col">Self-Hosted</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in comparisonRows" :key="i">
                    <th scope="row">{{ row.topic }}</th>
                    <td>{{ row.saas }}</td>
                    <td>{{ row.selfHosted }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- 16 Changes -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">16</span>
            Changes to this Policy
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              We may update this Policy. We will post the revised version and update the “Last updated” date. Where
              required by law, we will provide additional notice. Continued use where permitted constitutes acceptance of
              the revised Policy.
            </p>
          </div>
        </section>

        <!-- 17 Contact -->
        <section
          class="rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-slate-900/90 to-slate-950/95 p-6 shadow-[0_0_48px_rgba(34,211,238,0.08)] sm:p-8"
        >
          <h2 class="terms-h2 border-0 pb-0">
            <span class="terms-section-num border-cyan-400/35 bg-cyan-500/15 text-cyan-200">17</span>
            Contact
          </h2>
          <div class="terms-prose mt-4 space-y-4">
            <p>Questions about this Policy or requests regarding personal data:</p>
            <ul class="space-y-2 text-sm">
              <li class="flex flex-wrap items-center gap-2">
                <EnvelopeIcon class="h-5 w-5 shrink-0 text-cyan-400/90" />
                <span class="text-white/70">Privacy:</span>
                <a class="terms-link font-medium" href="mailto:privacy@pixelcastsignage.com">privacy@pixelcastsignage.com</a>
              </li>
              <li class="flex flex-wrap items-center gap-2">
                <EnvelopeIcon class="h-5 w-5 shrink-0 text-purple-400/90" />
                <span class="text-white/70">Legal:</span>
                <a class="terms-link font-medium" href="mailto:legal@pixelcastsignage.com">legal@pixelcastsignage.com</a>
              </li>
              <li class="flex flex-wrap items-center gap-2">
                <EnvelopeIcon class="h-5 w-5 shrink-0 text-cyan-400/80" />
                <span class="text-white/70">Support:</span>
                <a class="terms-link font-medium" href="mailto:support@pixelcastsignage.com">support@pixelcastsignage.com</a>
              </li>
            </ul>
            <p class="text-xs text-white/45">
              Self-Hosted: for data stored on your servers, your organization’s administrator is usually the first point
              of contact for end-user requests; contact us for data PixelCast holds about your account or licensing
              relationship.
            </p>
          </div>
        </section>
      </div>
    </main>

    <footer class="relative z-10 border-t border-white/10 bg-slate-950/60 py-8 backdrop-blur-md">
      <div class="mx-auto flex max-w-4xl flex-col items-center justify-between gap-4 px-4 text-center text-xs text-white/45 sm:flex-row sm:text-left sm:text-sm">
        <p>© {{ currentYear }} PixelCast. All rights reserved.</p>
        <div class="flex flex-wrap items-center justify-center gap-x-4 gap-y-2">
          <router-link class="hover:text-cyan-300" to="/privacy">Privacy</router-link>
          <span class="text-white/20" aria-hidden="true">·</span>
          <router-link class="hover:text-cyan-300" to="/terms">Terms</router-link>
          <span class="text-white/20" aria-hidden="true">·</span>
          <router-link class="hover:text-cyan-300" to="/data-center">Data Center</router-link>
          <span class="text-white/20" aria-hidden="true">·</span>
          <router-link class="hover:text-cyan-300" to="/docs">Docs</router-link>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  ArrowLeftIcon,
  ClockIcon,
  ShieldCheckIcon,
  EnvelopeIcon,
} from '@heroicons/vue/24/outline'

const authStore = useAuthStore()

const lastUpdated = ref('April 4, 2026')
const currentYear = ref(new Date().getFullYear())

const backRoute = computed(() => (authStore.isAuthenticated ? '/dashboard' : '/'))
const backText = computed(() => (authStore.isAuthenticated ? 'Back to Dashboard' : 'Back to Home'))

const directData = [
  'Account and profile: name, email, organization, role, and credentials you provide',
  'Billing and licensing: contact and transaction details needed to sell or support Self-Hosted licenses',
  'Support: information you include in tickets, emails, or chat when you contact us',
]

const automaticData = [
  'Technical: IP address, device and browser type, approximate location from IP, timestamps',
  'Service diagnostics: performance, error, and security logs tied to your workspace in SaaS',
  'Usage: features accessed, API traffic patterns, and aggregated analytics where collected',
]

const usagePurposes = [
  'Providing, operating, securing, and improving the Service',
  'Authenticating users, enforcing roles, and preventing fraud or abuse',
  'Communicating about the Service, security, and billing',
  'Complying with law and responding to lawful requests',
  'Supporting you and resolving incidents',
  'Managing licenses, marketplace purchases, and optional registry or telemetry where enabled',
]

const sharingItems = [
  'With subprocessors and vendors who assist us (hosting, payments, email/SMS, security, analytics), under contract',
  'With payment processors for paid offerings; their notices govern payment data',
  'When required by law, regulation, or competent authority, or to protect rights, safety, and security',
  'In connection with a merger, acquisition, or asset sale, subject to safeguards and notices where required',
  'With your direction or consent, including integrations you enable',
]

const securityMeasures = [
  { title: 'Encryption', description: 'TLS in transit; encryption at rest where appropriate for systems we operate' },
  { title: 'Access controls', description: 'Role-based access and least privilege for our personnel and systems' },
  { title: 'Authentication', description: 'Secure credential handling and optional strong authentication where offered' },
  { title: 'Monitoring', description: 'Logging and monitoring to detect and respond to incidents' },
  { title: 'Backups', description: 'Backup practices supporting continuity for hosted environments we control' },
]

const comparisonRows = [
  {
    topic: 'Ownership of operational data',
    saas: 'Typically stored on infrastructure we or our subprocessors operate; you choose what to upload.',
    selfHosted: 'Typically stored on your servers; you are responsible for backups and retention policies.',
  },
  {
    topic: 'Updates',
    saas: 'We deploy application updates to the hosted environment according to our release process.',
    selfHosted: 'You apply upgrades to your installation on your schedule (subject to license terms).',
  },
  {
    topic: 'Security split',
    saas: 'We secure the hosted application stack we provide; you secure credentials and tenant configuration.',
    selfHosted: 'We provide the software; you secure the host OS, network, database, and configuration.',
  },
  {
    topic: 'Privacy posture',
    saas: 'We process personal data as described here and may list cloud subprocessors; DPA terms may apply.',
    selfHosted: 'We generally do not access your production database; optional license/telemetry may still reach us—see Section 7.',
  },
]
</script>
