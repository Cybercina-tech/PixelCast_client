<template>
  <div class="space-y-6">
    <!-- Template Statistics -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">Total Templates</p>
          <p class="text-2xl sm:text-3xl font-bold text-primary tabular-nums">
            {{ analyticsStore.templateStats?.total_templates || 0 }}
          </p>
        </div>
      </Card>

      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">Active Screens</p>
          <p class="text-2xl sm:text-3xl font-bold text-primary-color tabular-nums">
            {{ analyticsStore.templateStats?.total_active_screens || 0 }}
          </p>
        </div>
      </Card>

      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">By Orientation</p>
          <div class="space-y-1 mt-2">
            <div v-for="orient in analyticsStore.templateStats?.by_orientation || []" :key="orient.orientation">
              <span class="text-sm text-muted">{{ orient.orientation }}:</span>
              <span class="text-lg font-bold text-primary ml-2">{{ orient.count }}</span>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Most Active Templates -->
    <Card title="Most Active Templates">
      <div v-if="analyticsStore.templateStats?.most_active_templates?.length > 0" class="table-container">
        <table class="table-base">
          <thead class="table-thead">
            <tr>
              <th class="table-th">Template Name</th>
              <th class="table-th">Active Screens</th>
              <th class="table-th">Actions</th>
            </tr>
          </thead>
          <tbody class="table-tbody">
            <tr v-for="template in analyticsStore.templateStats.most_active_templates" :key="template.template_id" class="table-tr">
              <td class="table-td font-medium">
                {{ template.template_name }}
              </td>
              <td class="table-td">
                <span class="badge-primary px-2 py-1 rounded-full text-xs font-medium">
                  {{ template.active_screen_count }} screens
                </span>
              </td>
              <td class="table-td">
                <router-link
                  :to="`/templates/${template.template_id}`"
                  class="action-btn-view font-medium"
                >
                  View Details
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="text-center text-muted py-8">
        No active templates data available
      </div>
    </Card>
  </div>
</template>

<script setup>
import { useAnalyticsStore } from '@/stores/analytics'
import Card from '@/components/common/Card.vue'

const analyticsStore = useAnalyticsStore()
</script>
