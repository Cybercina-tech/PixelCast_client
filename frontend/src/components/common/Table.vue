<template>
  <div class="table-container">
    <table class="table-base">
      <thead class="table-thead">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            class="table-th"
          >
            {{ column.label }}
          </th>
          <th v-if="actions && actions.length > 0" class="table-th text-right">
            Actions
          </th>
        </tr>
      </thead>
      <tbody class="table-tbody">
        <tr v-for="row in (data || [])" :key="row.id || row[primaryKey]" class="table-tr">
          <td
            v-for="column in columns"
            :key="column.key"
            class="table-td"
          >
            <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
              {{ row[column.key] }}
            </slot>
          </td>
          <td v-if="actions && actions.length > 0" class="table-td text-right">
            <div class="flex items-center justify-end gap-1">
              <slot name="actions" :row="row">
                <button
                  v-if="actions.includes('view')"
                  @click="$emit('view', row)"
                  class="action-btn-view"
                  title="View"
                >
                  <EyeIcon class="w-4 h-4" />
                </button>
                <button
                  v-if="actions.includes('edit')"
                  @click="$emit('edit', row)"
                  class="action-btn-edit"
                  title="Edit"
                >
                  <PencilIcon class="w-4 h-4" />
                </button>
                <button
                  v-if="actions.includes('delete')"
                  @click="$emit('delete', row)"
                  class="action-btn-delete"
                  title="Delete"
                >
                  <TrashIcon class="w-4 h-4" />
                </button>
              </slot>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="(!data || data.length === 0) && !loading" class="text-center py-8 text-muted">
      No data available
    </div>
    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-brand"></div>
      <p class="mt-2 text-sm text-secondary">Loading...</p>
    </div>
  </div>
</template>

<script setup>
import { EyeIcon, PencilIcon, TrashIcon } from '@heroicons/vue/24/outline'

defineProps({
  columns: {
    type: Array,
    required: true,
  },
  data: {
    type: Array,
    required: true,
  },
  actions: {
    type: Array,
    default: () => [],
  },
  primaryKey: {
    type: String,
    default: 'id',
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['edit', 'delete', 'view'])
</script>
