/**
 * Deep comparison utilities for smart state updates
 * Prevents unnecessary re-renders by comparing data before updating state
 */

/**
 * Deep equality check for two values
 * @param {any} a - First value
 * @param {any} b - Second value
 * @returns {boolean} - True if values are deeply equal
 */
export function deepEqual(a, b) {
  // Primitive comparison
  if (a === b) return true
  
  // Handle null/undefined
  if (a == null || b == null) return a === b
  
  // Type check
  if (typeof a !== typeof b) return false
  
  // Array comparison
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false
    for (let i = 0; i < a.length; i++) {
      if (!deepEqual(a[i], b[i])) return false
    }
    return true
  }
  
  // Object comparison
  if (typeof a === 'object' && typeof b === 'object') {
    const keysA = Object.keys(a)
    const keysB = Object.keys(b)
    
    if (keysA.length !== keysB.length) return false
    
    for (const key of keysA) {
      if (!keysB.includes(key)) return false
      if (!deepEqual(a[key], b[key])) return false
    }
    
    return true
  }
  
  return false
}

/**
 * Deep equality check for arrays of objects (by ID)
 * Useful for comparing lists where order might change but items are the same
 * @param {Array} oldArray - Old array
 * @param {Array} newArray - New array
 * @param {string} idKey - Key to use for ID comparison (default: 'id')
 * @returns {boolean} - True if arrays contain the same items (by ID)
 */
export function arraysEqualById(oldArray, newArray, idKey = 'id') {
  if (!Array.isArray(oldArray) || !Array.isArray(newArray)) {
    return deepEqual(oldArray, newArray)
  }
  
  if (oldArray.length !== newArray.length) return false
  
  // Create maps for quick lookup
  const oldMap = new Map(oldArray.map(item => [item[idKey], item]))
  const newMap = new Map(newArray.map(item => [item[idKey], item]))
  
  // Check all IDs match
  for (const id of oldMap.keys()) {
    if (!newMap.has(id)) return false
  }
  
  for (const id of newMap.keys()) {
    if (!oldMap.has(id)) return false
  }
  
  // Check all items with same ID are equal
  for (const [id, oldItem] of oldMap) {
    const newItem = newMap.get(id)
    if (!deepEqual(oldItem, newItem)) return false
  }
  
  return true
}

/**
 * Smart update: Merge new data into existing array, updating only changed items
 * Preserves object references for unchanged items to prevent re-renders
 * @param {Array} oldArray - Existing array
 * @param {Array} newArray - New array from API
 * @param {string} idKey - Key to use for ID comparison (default: 'id')
 * @returns {Array} - Updated array with preserved references for unchanged items
 */
export function smartUpdateArray(oldArray, newArray, idKey = 'id') {
  if (!Array.isArray(oldArray) || !Array.isArray(newArray)) {
    return newArray || oldArray || []
  }
  
  // If arrays are equal, return old array (preserve references)
  if (arraysEqualById(oldArray, newArray, idKey)) {
    return oldArray
  }
  
  // Create maps for quick lookup
  const oldMap = new Map(oldArray.map(item => [item[idKey], item]))
  const newMap = new Map(newArray.map(item => [item[idKey], item]))
  
  const result = []
  
  // Process new array to maintain order
  for (const newItem of newArray) {
    const id = newItem[idKey]
    const oldItem = oldMap.get(id)
    
    if (oldItem && deepEqual(oldItem, newItem)) {
      // Item unchanged - preserve reference
      result.push(oldItem)
    } else {
      // Item changed or new - use new reference
      result.push(newItem)
    }
  }
  
  return result
}

/**
 * Smart update: Merge new object into existing object, updating only changed properties
 * Preserves object reference if nothing changed
 * @param {Object} oldObj - Existing object
 * @param {Object} newObj - New object from API
 * @returns {Object} - Updated object (same reference if unchanged)
 */
export function smartUpdateObject(oldObj, newObj) {
  if (!oldObj || !newObj) return newObj || oldObj || {}
  
  // If objects are equal, return old object (preserve reference)
  if (deepEqual(oldObj, newObj)) {
    console.log('DEBUG [smartUpdateObject]: Objects are equal, preserving reference')
    return oldObj
  }
  
  // Check if only specific properties changed
  const changed = {}
  let hasChanges = false
  
  for (const key in newObj) {
    const oldValue = oldObj[key]
    const newValue = newObj[key]
    if (!deepEqual(oldValue, newValue)) {
      changed[key] = newValue
      hasChanges = true
      // DEBUG: Log detected changes
      console.log(`DEBUG [smartUpdateObject]: Change detected in key: "${key}"`, {
        old: oldValue,
        new: newValue,
        oldType: typeof oldValue,
        newType: typeof newValue,
        oldIsNull: oldValue === null,
        newIsNull: newValue === null,
      })
    }
  }
  
  // Check for removed properties
  for (const key in oldObj) {
    if (!(key in newObj)) {
      hasChanges = true
      console.log(`DEBUG [smartUpdateObject]: Property removed: "${key}"`)
      break
    }
  }
  
  if (!hasChanges) {
    console.log('DEBUG [smartUpdateObject]: No changes detected, preserving reference')
    return oldObj
  }
  
  console.log('DEBUG [smartUpdateObject]: Changes detected, creating new object. Changed keys:', Object.keys(changed))
  
  // Return new object with merged changes
  return { ...oldObj, ...newObj }
}

/**
 * Check if an object has specific property changes
 * Useful for determining if a component should re-render
 * @param {Object} oldObj - Old object
 * @param {Object} newObj - New object
 * @param {Array<string>} watchKeys - Keys to watch for changes
 * @returns {boolean} - True if any watched key changed
 */
export function hasPropertyChanges(oldObj, newObj, watchKeys) {
  if (!oldObj || !newObj) return true
  
  for (const key of watchKeys) {
    if (!deepEqual(oldObj[key], newObj[key])) {
      return true
    }
  }
  
  return false
}

