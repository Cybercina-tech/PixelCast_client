/**
 * Composable for showing delete confirmation dialogs
 * 
 * Usage:
 * import { useDeleteConfirmation } from '@/composables/useDeleteConfirmation'
 * 
 * const { confirmDelete } = useDeleteConfirmation()
 * 
 * // In your component
 * const handleDelete = async (itemId) => {
 *   try {
 *     await confirmDelete(
 *       itemId,
 *       async () => {
 *         // Your delete logic here
 *         await deleteItem(itemId)
 *       },
 *       {
 *         title: 'Delete Item?',
 *         message: 'Are you sure?',
 *         itemName: 'Item Name'
 *       }
 *     )
 *     // Success - item was deleted
 *     notify.success('Item deleted successfully')
 *   } catch (error) {
 *     // User cancelled or error occurred
 *     if (error.message !== 'Delete cancelled') {
 *       notify.error('Failed to delete item')
 *     }
 *   }
 * }
 */

import { reactive } from 'vue'

// Global state for the delete confirmation
const state = reactive({
  show: false,
  title: 'Confirm Deletion',
  message: 'Are you sure you want to delete this item? This action cannot be undone.',
  itemName: '',
  confirmText: 'Yes, Delete',
  cancelText: 'Cancel',
  loading: false,
  loadingText: 'Deleting...',
  resolve: null,
  reject: null,
  callback: null,
  itemId: null,
})

/**
 * Show the delete confirmation dialog
 * @param {string|number} itemId - The ID of the item to delete (optional, for display purposes)
 * @param {Function} callback - The function to execute when confirmed
 * @param {Object} options - Additional options for customization
 * @param {string} options.title - Custom title
 * @param {string} options.message - Custom message
 * @param {string} options.itemName - Name of the item to display
 * @param {string} options.confirmText - Text for confirm button
 * @param {string} options.cancelText - Text for cancel button
 * @returns {Promise} - Resolves if confirmed, rejects if cancelled
 */
export function confirmDelete(itemId, callback, options = {}) {
  return new Promise((resolve, reject) => {
    // Set options
    state.title = options.title || 'Confirm Deletion'
    state.message = options.message || 'Are you sure you want to delete this item? This action cannot be undone.'
    state.itemName = options.itemName || ''
    state.confirmText = options.confirmText || 'Yes, Delete'
    state.cancelText = options.cancelText || 'Cancel'
    state.loading = false
    state.loadingText = options.loadingText || 'Deleting...'
    state.itemId = itemId
    state.callback = callback
    state.resolve = resolve
    state.reject = reject
    
    // Show the modal
    state.show = true
  })
}

/**
 * Handle confirm action
 */
export async function handleConfirm() {
  try {
    state.loading = true
    
    // Execute the callback
    if (state.callback && typeof state.callback === 'function') {
      await state.callback(state.itemId)
    }
    
    // Close the modal
    state.show = false
    
    // Resolve the promise
    if (state.resolve) {
      state.resolve(state.itemId)
    }
  } catch (error) {
    state.loading = false
    // Reject the promise with the error
    if (state.reject) {
      state.reject(error)
    }
    throw error
  } finally {
    state.loading = false
  }
}

/**
 * Handle cancel action
 */
export function handleCancel() {
  state.show = false
  
  // Reject the promise
  if (state.reject) {
    state.reject(new Error('Delete cancelled'))
  }
}

/**
 * Composable function for use in components
 */
export function useDeleteConfirmation() {
  return {
    confirmDelete,
  }
}

/**
 * Export state for use in DeleteConfirmation component
 */
export const deleteConfirmationState = state
