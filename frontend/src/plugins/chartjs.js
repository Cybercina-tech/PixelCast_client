/**
 * Chart.js Plugin Configuration
 * 
 * Registers all Chart.js controllers, scales, and elements globally.
 * This ensures Chart.js components are available throughout the application.
 * 
 * Chart.js v4 requires explicit registration of controllers, scales, and elements.
 * Controllers are available as named exports in Chart.js v4.4+
 */

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  // Controllers - Chart.js v4.4+ exports these directly
  LineController,
  BarController,
  DoughnutController,
  PieController,
} from 'chart.js'

// Register all Chart.js components globally
ChartJS.register(
  // Scales
  CategoryScale,
  LinearScale,
  
  // Elements
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  
  // Controllers (REQUIRED for Chart.js v4 - these enable chart types)
  LineController,
  BarController,
  DoughnutController,
  PieController,
  
  // Plugins
  Title,
  Tooltip,
  Legend,
  Filler
)

export default ChartJS

