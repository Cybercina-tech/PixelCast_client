import { ref, computed } from 'vue'

/**
 * Use the same pixel box for scaling math as for the player clip rect.
 * `100vh`/`100vw` often differ from `innerWidth`/`innerHeight` (scrollbars, mobile UI).
 * `visualViewport` matches what is actually visible when available.
 */
function readViewportSize() {
  if (typeof window === 'undefined') return { width: 1920, height: 1080 }
  const vv = window.visualViewport
  if (vv && vv.width >= 1 && vv.height >= 1) {
    return { width: vv.width, height: vv.height }
  }
  return { width: window.innerWidth, height: window.innerHeight }
}

/**
 * Composable for responsive scaling calculations
 * Handles template scaling to fit any screen size while maintaining aspect ratio
 */
export function useResponsiveScaling(template) {
  const initial = readViewportSize()
  const viewportWidth = ref(initial.width)
  const viewportHeight = ref(initial.height)
  
  // Update viewport dimensions on resize
  const updateViewport = () => {
    const { width, height } = readViewportSize()
    viewportWidth.value = width
    viewportHeight.value = height
  }
  
  // Debounced resize handler for performance
  let resizeTimeout = null
  const handleResize = () => {
    if (resizeTimeout) {
      clearTimeout(resizeTimeout)
    }
    resizeTimeout = setTimeout(() => {
      updateViewport()
    }, 100) // 100ms debounce
  }
  
  /**
   * Contain mode (full template visible, no cropping):
   * - Entire template pixel rect fits inside the viewport; aspect ratio preserved.
   * - Letterboxing on one axis when viewport and template aspects differ.
   * (Cover mode would fill the screen but clip edge widgets — bad for signage layouts.)
   */
  const scaleFactor = computed(() => {
    if (!template.value) return 1

    const templateWidth = template.value.width || 1920
    const templateHeight = template.value.height || 1080

    if (templateWidth <= 0 || templateHeight <= 0) {
      console.warn('Invalid template dimensions, using default scale')
      return 1
    }

    if (viewportWidth.value <= 0 || viewportHeight.value <= 0) {
      console.warn('Invalid viewport dimensions, using default scale')
      return 1
    }

    const scaleX = viewportWidth.value / templateWidth
    const scaleY = viewportHeight.value / templateHeight
    let scale = Math.min(scaleX, scaleY)
    scale *= 1 - 1e-6
    // Slight inset so the full canvas stays visible (overscan / safe area on TVs)
    scale *= 0.96

    return Math.max(0.01, Math.min(scale, 10))
  })
  
  // Calculate scaled dimensions
  const scaledWidth = computed(() => {
    if (!template.value) return viewportWidth.value
    return (template.value.width || 1920) * scaleFactor.value
  })
  
  const scaledHeight = computed(() => {
    if (!template.value) return viewportHeight.value
    return (template.value.height || 1080) * scaleFactor.value
  })
  
  const offsetX = computed(() => {
    if (!template.value) return 0
    const gap = viewportWidth.value - scaledWidth.value
    return Math.max(0, Math.floor(gap * 0.5 * 1000) / 1000)
  })

  const offsetY = computed(() => {
    if (!template.value) return 0
    const gap = viewportHeight.value - scaledHeight.value
    return Math.max(0, Math.floor(gap * 0.5 * 1000) / 1000)
  })
  
  // Setup resize listener (call from component's onMounted)
  const setupResizeListener = () => {
    updateViewport()
    window.addEventListener('resize', handleResize)
    // Also listen to orientation change for mobile devices
    window.addEventListener('orientationchange', handleResize)
    const vv = window.visualViewport
    if (vv) {
      vv.addEventListener('resize', handleResize)
      vv.addEventListener('scroll', handleResize)
    }
  }
  
  // Cleanup (call from component's onUnmounted)
  const cleanupResizeListener = () => {
    window.removeEventListener('resize', handleResize)
    window.removeEventListener('orientationchange', handleResize)
    const vv = window.visualViewport
    if (vv) {
      vv.removeEventListener('resize', handleResize)
      vv.removeEventListener('scroll', handleResize)
    }
    if (resizeTimeout) {
      clearTimeout(resizeTimeout)
      resizeTimeout = null
    }
  }
  
  return {
    viewportWidth,
    viewportHeight,
    scaleFactor,
    scaledWidth,
    scaledHeight,
    offsetX,
    offsetY,
    updateViewport,
    setupResizeListener,
    cleanupResizeListener
  }
}

