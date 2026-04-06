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
          to="/privacy"
          class="hidden text-xs font-medium text-white/55 hover:text-cyan-300 sm:inline sm:text-sm"
        >
          Privacy Policy
        </router-link>
      </div>
    </header>

    <main class="relative z-10 mx-auto max-w-4xl px-4 pb-20 pt-10 sm:px-6 lg:px-8">
      <div class="mb-12 text-center sm:mb-14">
        <div
          class="mx-auto mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-400/25 bg-gradient-to-br from-cyan-500/20 to-purple-600/25 shadow-[0_0_40px_rgba(34,211,238,0.15)]"
        >
          <DocumentTextIcon class="h-8 w-8 text-cyan-300" />
        </div>
        <p class="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400/90">
          Legal
        </p>
        <h1
          class="mb-4 text-3xl font-bold tracking-tight text-white sm:text-4xl md:text-5xl"
        >
          <span
            class="bg-gradient-to-r from-cyan-300 via-blue-300 to-purple-400 bg-clip-text text-transparent"
          >
            Terms of Service
          </span>
        </h1>
        <p class="flex flex-wrap items-center justify-center gap-2 text-sm text-white/55">
          <ClockIcon class="h-4 w-4 text-cyan-400/80" />
          <span>Last updated <strong class="font-semibold text-white/80">{{ lastUpdated }}</strong></span>
        </p>
        <p class="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-slate-400">
          These Terms are a binding contract between you and PixelCast. They set out what you may and may not do, what we
          provide, and how liability is allocated—whether you use our cloud (SaaS) offering or a self-hosted deployment.
          By using the Service, you agree to these Terms and our
          <router-link class="terms-link" to="/privacy">Privacy Policy</router-link>.
        </p>
      </div>

      <div class="space-y-8 md:space-y-10">
        <!-- 1 -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">1</span>
            Agreement &amp; definitions
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              These Terms of Service (“<strong>Terms</strong>”) govern access to and use of the PixelCast digital signage
              platform and related services (“<strong>Service</strong>”) offered by the operator of PixelCast
              (“<strong>PixelCast</strong>,” “<strong>we</strong>,” “<strong>us</strong>,” or “<strong>our</strong>”).
            </p>
            <p>
              “<strong>You</strong>,” “<strong>your</strong>,” or “<strong>Customer</strong>” means the individual or
              entity accepting these Terms. “<strong>User</strong>” means anyone you authorize to use the Service under
              your account (for example employees or contractors). “<strong>Content</strong>” means media, templates,
              schedules, configuration, and other materials you upload or process through the Service. “<strong>Subscription</strong>”
              means a paid or trial cloud plan, where applicable. “<strong>Deployment</strong>” means either a hosted
              multi-tenant or dedicated cloud environment we operate for you (“<strong>SaaS</strong>”) or software you run
              on infrastructure you control (“<strong>Self-Hosted</strong>”), as described in your order, license, or setup
              documentation.
            </p>
            <p>
              If you accept on behalf of a company, you represent that you have authority to bind that organization. If
              you do not agree, do not use the Service. We may refuse or suspend access where permitted by law.
            </p>
          </div>
        </section>

        <!-- 2 -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">2</span>
            The Service
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              PixelCast provides tools to manage displays, templates, schedules, remote commands, users, analytics, and
              related operations. Features vary by plan, license, and Deployment type.
            </p>
            <ul class="terms-list">
              <li v-for="(f, i) in serviceHighlights" :key="i">{{ f }}</li>
            </ul>
            <p>
              We may update, add, or retire features where reasonably necessary for security, compliance, or reliability,
              subject to applicable law and any separate agreement with you.
            </p>
          </div>
        </section>

        <!-- 3 SaaS billing -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">3</span>
            SaaS: plans, trials, billing, renewal &amp; refunds
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              This section applies when you use PixelCast as a hosted SaaS product (including trials and paid
              Subscriptions). It does not replace your checkout terms or order form if those add different conditions.
            </p>
            <p>
              <strong>Fees and renewal.</strong> Fees, billing cycles, and renewal terms are those shown at purchase or in
              your order. Unless stated otherwise, Subscriptions renew automatically until cancelled in accordance with
              the cancellation method we provide (for example through your billing portal or Stripe customer portal where
              enabled).
            </p>
            <p>
              <strong>Trials.</strong> We may offer free trials. When a trial ends, continued access to paid features may
              require an active Subscription. We may change or discontinue trial programs.
            </p>
            <p>
              <strong>Refunds.</strong> Unless mandatory consumer law in your jurisdiction requires otherwise, fees are
              generally non-refundable once the paid period has started. If you believe a charge is in error, contact
              support promptly. Payment disputes may also be governed by your payment provider’s policies.
            </p>
            <p>
              <strong>Taxes.</strong> Fees are exclusive of applicable taxes unless stated otherwise. You are responsible
              for taxes on your purchase other than taxes based on our net income.
            </p>
            <p>
              <strong>Payment processors.</strong> We may use third parties such as Stripe. Their terms and privacy
              notices apply to payment data they process.
            </p>
          </div>
        </section>

        <!-- 4 SLA -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">4</span>
            SaaS: availability
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              For SaaS, we aim to keep the Service available and target high uptime (for example <strong>99.9% monthly
              availability</strong> of the core administrative API and web application, excluding scheduled maintenance
              announced in advance where practicable).
            </p>
            <p>
              <strong>Exclusions.</strong> Availability commitments do not apply to: (a) your internet connectivity or
              devices; (b) third-party services or integrations you enable; (c) emergency or security-related suspension;
              (d) events beyond our reasonable control (including force majeure); (e) beta or free-tier features; or (f)
              issues caused by your Content, misuse, or quota limits. Credits or remedies, if any, for qualifying outages
              may be described in a separate SLA or enterprise agreement; otherwise this section sets expectations only and
              does not create a financial remedy unless we expressly agree in writing.
            </p>
          </div>
        </section>

        <!-- 5 Self-hosted license -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">5</span>
            Self-Hosted: license, scope &amp; redistribution
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              This section applies when you run PixelCast on infrastructure you control under a self-hosted license or
              marketplace purchase. Your specific license (including seat, domain, or instance limits) is defined in your
              order, license key terms, or marketplace license—those limits are part of these Terms.
            </p>
            <p>
              Subject to payment and compliance, we grant you a non-exclusive, non-transferable (except as law allows)
              license to install and run the Software for your internal business purposes within the scope of your
              license. You may not:
            </p>
            <ul class="terms-list">
              <li v-for="(x, i) in selfHostedRestrictions" :key="i">{{ x }}</li>
            </ul>
            <p>
              <strong>Open source and third-party components.</strong> The Software may include third-party components
              subject to their own licenses; you must comply with those notices where provided.
            </p>
          </div>
        </section>

        <!-- 6 Self-hosted security -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">6</span>
            Self-Hosted: your infrastructure &amp; security
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              For Self-Hosted deployments, <strong>you control the server, network, database, backups, and configuration</strong>.
              We do not have routine access to your production database or Content except where you choose to send us data
              (for example support logs, or optional license/telemetry features if enabled in your build).
            </p>
            <p>
              <strong>Security disclaimer.</strong> To the maximum extent permitted by law, we are <strong>not
              responsible</strong> for security incidents, data loss, downtime, or misconfiguration on infrastructure you
              operate, including weak passwords, open ports, missing patches, or incorrect TLS or firewall settings. You
              are responsible for securing your environment and maintaining backups of Content and personal data you
              process.
            </p>
          </div>
        </section>

        <!-- 7 Accounts -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">7</span>
            Accounts, eligibility &amp; security
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              You must provide accurate registration information and keep it current. You are responsible for activity
              under your account and for safeguarding credentials. Notify us promptly of suspected unauthorized use.
            </p>
            <ul class="terms-list">
              <li v-for="(s, i) in securityItems" :key="i">{{ s }}</li>
            </ul>
            <p>You are responsible for your Users’ compliance with these Terms.</p>
          </div>
        </section>

        <!-- 8 License to use (access) -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">8</span>
            License to access &amp; use the Service
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              Subject to these Terms, we grant you a limited, revocable, non-exclusive license to access and use the
              Service (including the hosted application and APIs made available to you) for your internal business
              purposes during your Subscription or license term. This license is in addition to, and does not replace,
              Self-Hosted software license terms in Section 5 where applicable.
            </p>
            <p>
              You will not (and will not permit others to): reverse engineer, decompile, or attempt to extract source code
              except where mandatory law permits; circumvent technical limits or license enforcement; probe or test our
              systems without written authorization; or use the Service to build a competing product or service.
            </p>
          </div>
        </section>

        <!-- 9 Content -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">9</span>
            Your Content &amp; responsibility
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              You retain ownership of Content you provide. You grant us a license to host, process, transmit, and display
              Content only as needed to provide, secure, and improve the Service, as further described in the Privacy
              Policy.
            </p>
            <p>
              You represent that you have rights and consents needed for Content and for displaying it on your screens.
              You are solely responsible for legality and appropriateness of Content in your jurisdiction and industry.
            </p>
          </div>
        </section>

        <!-- 10 Acceptable use -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">10</span>
            Acceptable use
          </h2>
          <div class="terms-prose space-y-4">
            <p>You agree not to use the Service to:</p>
            <ul class="terms-list">
              <li v-for="(p, i) in prohibitedItems" :key="i">{{ p }}</li>
            </ul>
            <p>
              We may investigate violations and cooperate with authorities. We may remove Content or suspend access where
              reasonably necessary to protect the Service, users, or the public.
            </p>
          </div>
        </section>

        <!-- 11 IP -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">11</span>
            Our intellectual property
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              The Service—including software (except third-party open-source components as labeled), branding, logos,
              documentation, and underlying technology—is owned by us or our licensors and protected by intellectual
              property laws. Except for the limited licenses in these Terms, no rights are granted. Feedback you provide
              may be used without restriction or obligation.
            </p>
            <p>
              <strong>No reverse engineering.</strong> You may not copy, modify, or create derivative works of our
              Software except as allowed by law, and you may not remove or alter proprietary notices.
            </p>
          </div>
        </section>

        <!-- 12 Third parties -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">12</span>
            Third-party services
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              The Service may integrate with third parties (payments, email, SMS, identity, infrastructure). Those
              services are governed by their own terms. We are not responsible for third-party services or content.
            </p>
          </div>
        </section>

        <!-- 13 Disclaimers -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">13</span>
            Disclaimers
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              <strong>THE SERVICE IS PROVIDED “AS IS” AND “AS AVAILABLE.”</strong> TO THE MAXIMUM EXTENT PERMITTED BY LAW,
              WE DISCLAIM ALL WARRANTIES, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING MERCHANTABILITY, FITNESS FOR A
              PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT.
            </p>
            <p>
              <strong>No business outcome warranty.</strong> We do not warrant uninterrupted or error-free operation, that
              defects will be corrected, or that the Service will meet your business requirements. <strong>We are not
              liable for your profits, losses, or business decisions</strong> based on use of the Service, except as
              mandatory law may require.
            </p>
            <p>
              You are responsible for compliance with laws applicable to digital signage, accessibility, advertising, and
              public displays in your regions.
            </p>
          </div>
        </section>

        <!-- 14 Liability -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">14</span>
            Limitation of liability
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, WE AND OUR AFFILIATES, LICENSORS, AND SUPPLIERS WILL NOT
              BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES, OR ANY LOSS
              OF PROFITS, REVENUE, GOODWILL, DATA, OR BUSINESS INTERRUPTION, EVEN IF ADVISED OF THE POSSIBILITY.
            </p>
            <p>
              OUR AGGREGATE LIABILITY ARISING OUT OF OR RELATED TO THE SERVICE OR THESE TERMS WILL NOT EXCEED THE GREATER
              OF (A) THE AMOUNTS YOU PAID US FOR THE SERVICE IN THE TWELVE (12) MONTHS BEFORE THE CLAIM, OR (B) ONE HUNDRED
              U.S. DOLLARS (USD $100) IF YOU HAD NO PAYMENT OBLIGATION.
            </p>
            <p>
              Some jurisdictions do not allow certain limitations; in those cases our liability is limited to the fullest
              extent permitted by law. Nothing limits liability that cannot be limited under mandatory law.
            </p>
          </div>
        </section>

        <!-- 15 Indemnity -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">15</span>
            Indemnity
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              You will defend, indemnify, and hold harmless PixelCast and its affiliates, officers, directors, employees,
              and agents from claims, damages, losses, and expenses (including reasonable attorneys’ fees) arising from
              Content, your breach of these Terms, or your violation of law or third-party rights.
            </p>
          </div>
        </section>

        <!-- 16 Termination -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">16</span>
            Suspension &amp; termination
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              You may stop using the Service at any time. We may suspend or terminate access for material breach, legal
              requirement, or to prevent harm. Sections that should survive (including intellectual property, disclaimers,
              liability limits, indemnity, and dispute terms) survive termination.
            </p>
            <p>
              Upon termination, your right to use the Service ceases. We may delete or retain Content per the Privacy
              Policy and applicable law. Self-Hosted licenses may include additional termination effects in your order.
            </p>
          </div>
        </section>

        <!-- 17 Privacy -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">17</span>
            Privacy &amp; data
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              Our processing of personal data is described in the
              <router-link class="terms-link" to="/privacy">Privacy Policy</router-link>. For SaaS, we typically act as a
              processor or service provider for certain Customer-controlled data as described there. Additional data
              processing terms may apply under your order or a data processing addendum where provided.
            </p>
          </div>
        </section>

        <!-- 18 Changes -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">18</span>
            Changes to these Terms
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              We may modify these Terms. We will post updates and revise the “Last updated” date. Where required by law,
              we will provide additional notice. Continued use after the effective date constitutes acceptance where
              permitted by law.
            </p>
          </div>
        </section>

        <!-- 19 Export -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">19</span>
            Export, sanctions &amp; government use
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              You represent that you are not in a prohibited jurisdiction or on restricted party lists. You will comply
              with export and sanctions laws. U.S. government use may be subject to additional restrictions.
            </p>
          </div>
        </section>

        <!-- 20 Law -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">20</span>
            Governing law &amp; disputes
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              Unless mandatory consumer law requires otherwise, these Terms are governed by the laws applicable to the
              PixelCast entity contracting with you, without regard to conflict-of-law rules. Courts in that jurisdiction
              have exclusive jurisdiction, except either party may seek injunctive relief for IP or confidentiality in
              any competent court. Consumers may have additional local rights.
            </p>
          </div>
        </section>

        <!-- 21 General -->
        <section class="terms-glass rounded-2xl p-6 sm:p-8">
          <h2 class="terms-h2">
            <span class="terms-section-num">21</span>
            General
          </h2>
          <div class="terms-prose space-y-4">
            <p>
              <strong>Entire agreement.</strong> These Terms, the Privacy Policy, and any order or checkout terms you
              accept form the entire agreement regarding the Service.
            </p>
            <p>
              <strong>Assignment.</strong> You may not assign without our consent. We may assign in connection with a
              merger, acquisition, or asset sale.
            </p>
            <p><strong>Severability; waiver; force majeure.</strong> Invalid provisions do not affect the remainder. No
            waiver by inaction. We are not liable for delays beyond our reasonable control.</p>
          </div>
        </section>

        <!-- 22 Contact -->
        <section
          class="rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-slate-900/90 to-slate-950/95 p-6 shadow-[0_0_48px_rgba(34,211,238,0.08)] sm:p-8"
        >
          <h2 class="terms-h2 border-0 pb-0">
            <span class="terms-section-num border-cyan-400/35 bg-cyan-500/15 text-cyan-200">22</span>
            Contact
          </h2>
          <div class="terms-prose mt-4 space-y-4">
            <p>Questions about these Terms:</p>
            <ul class="space-y-2 text-sm">
              <li class="flex flex-wrap items-center gap-2">
                <EnvelopeIcon class="h-5 w-5 shrink-0 text-cyan-400/90" />
                <span class="text-white/70">Legal:</span>
                <a class="terms-link font-medium" href="mailto:legal@pixelcastsignage.com">legal@pixelcastsignage.com</a>
              </li>
              <li class="flex flex-wrap items-center gap-2">
                <EnvelopeIcon class="h-5 w-5 shrink-0 text-purple-400/90" />
                <span class="text-white/70">Support:</span>
                <a class="terms-link font-medium" href="mailto:support@pixelcastsignage.com">support@pixelcastsignage.com</a>
              </li>
            </ul>
            <p class="text-xs text-white/45">
              Self-Hosted customers: your internal administrator may be the first contact for account and infrastructure
              issues; legal questions about these Terms may still be directed to the addresses above.
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
  DocumentTextIcon,
  EnvelopeIcon,
} from '@heroicons/vue/24/outline'

const authStore = useAuthStore()

const lastUpdated = ref('April 4, 2026')
const currentYear = ref(new Date().getFullYear())

const backRoute = computed(() => (authStore.isAuthenticated ? '/dashboard' : '/'))
const backText = computed(() => (authStore.isAuthenticated ? 'Back to Dashboard' : 'Back to Home'))

const serviceHighlights = [
  'Screen and device registry, grouping, heartbeats, pairing, and web player flows where enabled',
  'Templates, media, schedules, remote commands, and operational logs',
  'Users, roles, permissions, audit and analytics features as offered in your plan or license',
  'Optional SaaS platform capabilities (billing, multi-tenant administration) when enabled for your account',
]

const securityItems = [
  'Use strong passwords and protect authentication factors (including 2FA where available)',
  'Revoke access for departing personnel when applicable',
  'Notify us of suspected compromise of accounts or API credentials',
]

const selfHostedRestrictions = [
  'Copy, distribute, sell, rent, lease, or sublicense the Software beyond your license scope',
  'Host the Software for third parties as a service without our written consent',
  'Remove or obscure proprietary or license notices',
  'Exceed the number of installations, domains, seats, or screens permitted by your license',
  'Use the Software after termination of your license except as law requires for interoperability',
]

const prohibitedItems = [
  'Violate applicable laws, regulations, or third-party rights',
  'Upload or display unlawful, fraudulent, defamatory, harassing, hateful, or discriminatory content',
  'Distribute malware, exploit vulnerabilities, or disrupt the Service or third-party networks',
  'Attempt unauthorized access to accounts, systems, or data (including penetration testing without written approval)',
  'Mine cryptocurrency, send spam, or run bulk unsolicited communications through the Service',
  'Use automated means to access the Service contrary to our documentation or rate limits',
  'Resell or redistribute the Service or Software except as expressly permitted in writing',
]
</script>
