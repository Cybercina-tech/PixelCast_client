import { ref, computed, watch } from 'vue'

function readWindowViewportSize() {
  if (typeof window === 'undefined') return { width: 1920, height: 1080 }
  const vv = window.visualViewport
  if (vv && vv.width >= 1 && vv.height >= 1) {
    return { width: vv.width, height: vv.height }
  }
  return { width: window.innerWidth, height: window.innerHeight }
}

function readElementSize(el) {
  if (!el) return null
  const width = el.clientWidth
  const height = el.clientHeight
  if (width >= 1 && height >= 1) {
    return { width, height }
  }
  return null
}

/**
 * Composable for responsive scaling calculations.
 * @param {import('vue').Ref} template - active template
 * @param {{ fit?: 'cover' | 'contain', containerRef?: import('vue').Ref }} [options]
 */
export function useResponsiveScaling(template, options = {}) {
  const fitMode = options.fit === 'contain' ? 'contain' : 'cover'
  const containerRef = options.containerRef

  const initial = readWindowViewportSize()
  const viewportWidth = ref(initial.width)
  const viewportHeight = ref(initial.height)

  const readViewportSize = () => {
    const fromContainer = readElementSize(containerRef?.value)
    if (fromContainer) return fromContainer
    return readWindowViewportSize()
  }

  const updateViewport = () => {
    const { width, height } = readViewportSize()
    viewportWidth.value = width
    viewportHeight.value = height
  }

  let resizeTimeout = null
  const handleResize = () => {
    if (resizeTimeout) clearTimeout(resizeTimeout)
    resizeTimeout = setTimeout(() => {
      updateViewport()
    }, 50)
  }

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
    let scale = fitMode === 'contain' ? Math.min(scaleX, scaleY) : Math.max(scaleX, scaleY)
    scale *= 1 - 1e-6
    if (fitMode === 'contain') {
      scale *= 0.96
    }

    return Math.max(0.01, Math.min(scale, 10))
  })

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
    return Math.round(gap * 0.5 * 1000) / 1000
  })

  const offsetY = computed(() => {
    if (!template.value) return 0
    const gap = viewportHeight.value - scaledHeight.value
    return Math.round(gap * 0.5 * 1000) / 1000
  })

  let resizeObserver = null
  let stopContainerWatch = null

  const disconnectContainerObserver = () => {
    if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = null
    }
  }

  const bindContainerObserver = (el) => {
    disconnectContainerObserver()
    if (!el || typeof ResizeObserver === 'undefined') {
      updateViewport()
      return
    }
    resizeObserver = new ResizeObserver(() => {
      handleResize()
    })
    resizeObserver.observe(el)
    updateViewport()
  }

  const setupResizeListener = () => {
    updateViewport()
    window.addEventListener('resize', handleResize)
    window.addEventListener('orientationchange', handleResize)
    document.addEventListener('fullscreenchange', handleResize)
    const vv = window.visualViewport
    if (vv) {
      vv.addEventListener('resize', handleResize)
      vv.addEventListener('scroll', handleResize)
    }

    if (containerRef) {
      stopContainerWatch = watch(
        containerRef,
        (el) => {
          if (el) bindContainerObserver(el)
          else disconnectContainerObserver()
        },
        { immediate: true },
      )
    }
  }

  const cleanupResizeListener = () => {
    window.removeEventListener('resize', handleResize)
    window.removeEventListener('orientationchange', handleResize)
    document.removeEventListener('fullscreenchange', handleResize)
    const vv = window.visualViewport
    if (vv) {
      vv.removeEventListener('resize', handleResize)
      vv.removeEventListener('scroll', handleResize)
    }
    if (resizeTimeout) {
      clearTimeout(resizeTimeout)
      resizeTimeout = null
    }
    disconnectContainerObserver()
    if (stopContainerWatch) {
      stopContainerWatch()
      stopContainerWatch = null
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
    cleanupResizeListener,
  }
}
