import jsQR from 'jsqr'

const MAX_SCAN_DIMENSION = 960

/**
 * Normalize decoded QR text into a full URL string that AddScreen can parse for `token=`.
 */
export function pairingUrlFromDecodedText(text) {
  const raw = text.trim()
  if (!raw) return null

  try {
    const u = new URL(raw)
    if (u.searchParams.get('token')) return u.href
  } catch {
    /* not absolute */
  }

  const tokenMatch = raw.match(/[?&]token=([^&#\s]+)/)
  if (tokenMatch) {
    try {
      if (raw.startsWith('http://') || raw.startsWith('https://')) {
        return new URL(raw).href
      }
      const pathAndQuery = raw.startsWith('/') ? raw : `/${raw}`
      return new URL(pathAndQuery, window.location.origin).href
    } catch {
      return null
    }
  }

  return null
}

function decodeImageData(imageData) {
  return jsQR(imageData.data, imageData.width, imageData.height, {
    inversionAttempts: 'attemptBoth',
  })
}

export function decodeQrFromImageFile(file) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      const w0 = img.naturalWidth
      const h0 = img.naturalHeight
      if (!w0 || !h0) {
        resolve(null)
        return
      }
      const canvas = document.createElement('canvas')
      const scale = Math.min(1, MAX_SCAN_DIMENSION / Math.max(w0, h0))
      const w = Math.max(1, Math.floor(w0 * scale))
      const h = Math.max(1, Math.floor(h0 * scale))
      canvas.width = w
      canvas.height = h
      const ctx = canvas.getContext('2d', { willReadFrequently: true })
      ctx.drawImage(img, 0, 0, w, h)
      const imageData = ctx.getImageData(0, 0, w, h)
      const code = decodeImageData(imageData)
      resolve(code?.data ?? null)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Could not load image'))
    }
    img.src = url
  })
}

/**
 * Live camera QR scan: requests camera via getUserMedia, decodes frames until `onDecoded` returns truthy to stop, or `stop()` is called.
 */
export function createLiveQrScanner() {
  let rafId = null
  let stream = null
  let canvas = null
  let ctx = null
  let videoEl = null
  let stopped = false

  function cleanupTracks() {
    stream?.getTracks().forEach((t) => t.stop())
    stream = null
  }

  function stop() {
    stopped = true
    if (rafId != null) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
    cleanupTracks()
    if (videoEl) {
      videoEl.srcObject = null
      videoEl = null
    }
    canvas = null
    ctx = null
  }

  /**
   * @param {HTMLVideoElement} video
   * @param {{ onDecoded: (data: string) => void, onError: (err: Error) => void }} callbacks
   */
  async function start(video, { onDecoded, onError }) {
    stopped = false
    videoEl = video
    if (!navigator.mediaDevices?.getUserMedia) {
      onError(new Error('Camera is not available in this browser.'))
      return
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      })
    } catch (err) {
      const name = err?.name || ''
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        onError(new Error('Camera access was denied. Allow camera permission and try again.'))
      } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
        onError(new Error('No camera was found on this device.'))
      } else if (name === 'NotReadableError' || name === 'TrackStartError') {
        onError(new Error('The camera is in use by another app or could not be started.'))
      } else {
        onError(err instanceof Error ? err : new Error(String(err)))
      }
      return
    }

    video.srcObject = stream
    video.setAttribute('playsinline', 'true')
    video.muted = true
    try {
      await video.play()
    } catch (e) {
      cleanupTracks()
      onError(e instanceof Error ? e : new Error('Could not start video preview.'))
      return
    }

    canvas = document.createElement('canvas')
    ctx = canvas.getContext('2d', { willReadFrequently: true })

    function tick() {
      if (stopped) return
      rafId = requestAnimationFrame(tick)

      if (video.readyState < video.HAVE_CURRENT_DATA) return

      const vw = video.videoWidth
      const vh = video.videoHeight
      if (!vw || !vh) return

      const scale = Math.min(1, MAX_SCAN_DIMENSION / Math.max(vw, vh))
      const w = Math.max(1, Math.floor(vw * scale))
      const h = Math.max(1, Math.floor(vh * scale))

      canvas.width = w
      canvas.height = h
      ctx.drawImage(video, 0, 0, w, h)
      const imageData = ctx.getImageData(0, 0, w, h)
      const code = decodeImageData(imageData)
      if (code?.data) {
        onDecoded(code.data)
      }
    }

    rafId = requestAnimationFrame(tick)
  }

  return { start, stop }
}

export function isCameraScanSupported() {
  if (typeof window === 'undefined') return false
  if (!window.isSecureContext) return false
  return Boolean(navigator.mediaDevices?.getUserMedia)
}
