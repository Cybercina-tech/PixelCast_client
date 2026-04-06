<template>
  <div class="space-y-8">
    <section class="relative overflow-hidden rounded-3xl border border-border-color/80 bg-gradient-to-br from-cyan-500/10 via-violet-500/10 to-transparent p-5 md:p-7">
      <p class="text-[11px] uppercase tracking-wider text-muted mb-2">Super Admin</p>
      <h2 class="text-xl md:text-2xl font-bold text-primary">Operator tools</h2>
      <p class="text-secondary text-sm mt-2 max-w-2xl">
        This distribution includes ticket forwarding to the mother platform and self-hosted license registry
        management. Marketing, billing, and multi-tenant analytics are not shipped in the CodeCanyon package.
      </p>
      <div class="mt-4 flex flex-wrap gap-2">
        <router-link to="/super-admin/tickets" class="btn-primary px-4 py-2 rounded-lg text-sm">
          Ticket queue
        </router-link>
        <router-link to="/super-admin/self-hosted-licenses" class="btn-outline px-4 py-2 rounded-lg text-sm">
          Self-hosted licenses
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
</script>
