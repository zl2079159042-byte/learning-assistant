// API 配置：开发环境走 Vite 代理，生产环境直连后端
const isDev = import.meta.env.DEV

// 生产环境需要在 Vercel 设置 VITE_API_BASE_URL 环境变量
// 例如: https://learning-assistant-api.onrender.com
const PROD_API = import.meta.env.VITE_API_BASE_URL || 'https://your-backend.onrender.com'

export const API_BASE = isDev ? '' : PROD_API
export const API_PREFIX = '/api'

export function apiUrl(path) {
  return `${API_BASE}${path}`
}
