import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

client.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail || error.response?.data?.message || error.message || '请求失败'

    if (error.response?.status === 401) {
      console.warn('[API] 未授权，请重新登录')
    } else if (error.response?.status === 500) {
      console.error('[API] 服务器错误:', message)
    }

    return Promise.reject(new Error(message))
  }
)

export default client

// Convenience API methods
export const api = {
  // Knowledge
  listKnowledge(params = {}) {
    return client.get('/knowledge', { params })
  },

  getKnowledge(id) {
    return client.get(`/knowledge/${id}`)
  },

  updateKnowledge(id, data) {
    return client.put(`/knowledge/${id}`, data)
  },

  deleteKnowledge(id) {
    return client.delete(`/knowledge/${id}`)
  },

  // Chat
  getChatSession(sessionId) {
    return client.get(`/chat/${sessionId}`)
  },

  // History
  listHistory(params = {}) {
    return client.get('/history', { params })
  },

  getStats() {
    return client.get('/history/stats')
  },

  // Streaming chat — uses raw fetch for SSE consumption
  sendChatStream(body) {
    return fetch('/api/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
  }
}
