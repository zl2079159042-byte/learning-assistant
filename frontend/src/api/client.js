import axios from 'axios'
import { API_BASE, API_PREFIX, apiUrl } from '../config'

const client = axios.create({
  baseURL: API_BASE + API_PREFIX,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('[API]', message)
    return Promise.reject(new Error(message))
  }
)

export default client

// SSE 流式请求封装
export function sseFetch(url, body) {
  return fetch(apiUrl(url), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function sseUploadFile(url, formData) {
  return fetch(apiUrl(url), {
    method: 'POST',
    body: formData,
  })
}
