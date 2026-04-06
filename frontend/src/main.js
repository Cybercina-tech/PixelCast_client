import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createHead } from '@unhead/vue/client'
import { MotionPlugin } from '@vueuse/motion'
import App from './App.vue'
import router from './router'
import { fetchDeploymentConfig } from './utils/deploymentConfig'
import { bootGtm } from './analytics/gtm'
// App + widget fonts (bundled for TemplateEditor / WebPlayer text widgets)
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '@fontsource/inter/800.css'

import '@fontsource/open-sans/400.css'
import '@fontsource/open-sans/600.css'
import '@fontsource/open-sans/700.css'
import '@fontsource/open-sans/800.css'

import '@fontsource/roboto/400.css'
import '@fontsource/roboto/500.css'
import '@fontsource/roboto/700.css'

import '@fontsource/lato/400.css'
import '@fontsource/lato/700.css'

import '@fontsource/montserrat/400.css'
import '@fontsource/montserrat/600.css'
import '@fontsource/montserrat/700.css'
import '@fontsource/montserrat/800.css'

import '@fontsource/poppins/400.css'
import '@fontsource/poppins/600.css'
import '@fontsource/poppins/700.css'
import '@fontsource/poppins/800.css'

import '@fontsource/noto-sans/400.css'
import '@fontsource/noto-sans/600.css'
import '@fontsource/noto-sans/700.css'

import '@fontsource/oswald/400.css'
import '@fontsource/oswald/600.css'
import '@fontsource/oswald/700.css'

import './style.css'
import './styles/legal-document.css'

// Initialize Chart.js plugin before app creation
import './plugins/chartjs'

// Initialize client-side error logging
import { initClientLogger } from './services/clientLogger'
initClientLogger()

const app = createApp(App)

app.use(createHead())
app.use(createPinia())
app.use(router)
app.use(MotionPlugin)

bootGtm(import.meta.env.VITE_GTM_CONTAINER_ID)

fetchDeploymentConfig().finally(() => {
  app.mount('#app')
})
