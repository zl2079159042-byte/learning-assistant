import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client.js'

export const useChatStore = defineStore('chat', () => {
  // --- State ---
  const sessions = ref([])
  const currentSessionId = ref(null)
  const messages = ref([])
  const isStreaming = ref(false)
  const streamText = ref('')

  // --- Getters ---
  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentSessionId.value) || null
  )

  // --- Setters ---
  function setSessions(list) {
    sessions.value = list
  }

  function setCurrentSessionId(id) {
    currentSessionId.value = id
  }

  function setMessages(list) {
    messages.value = list
  }

  function setIsStreaming(val) {
    isStreaming.value = val
  }

  function setStreamText(text) {
    streamText.value = text
  }

  function appendStreamToken(token) {
    streamText.value += token
  }

  function clearStreamText() {
    streamText.value = ''
  }

  // --- Actions ---
  async function fetchSessions(params = {}) {
    const data = await api.listHistory({ ...params, type: 'chat' })
    sessions.value = data.items
    return data
  }

  async function fetchSession(sessionId) {
    const data = await api.getChatSession(sessionId)
    currentSessionId.value = sessionId
    messages.value = data.messages || []
    return data
  }

  function addMessage(message) {
    messages.value.push(message)
  }

  function startStreaming() {
    isStreaming.value = true
    streamText.value = ''
  }

  function stopStreaming() {
    isStreaming.value = false
  }

  function reset() {
    sessions.value = []
    currentSessionId.value = null
    messages.value = []
    isStreaming.value = false
    streamText.value = ''
  }

  return {
    // state
    sessions,
    currentSessionId,
    messages,
    isStreaming,
    streamText,
    // getters
    currentSession,
    // setters
    setSessions,
    setCurrentSessionId,
    setMessages,
    setIsStreaming,
    setStreamText,
    appendStreamToken,
    clearStreamText,
    // actions
    fetchSessions,
    fetchSession,
    addMessage,
    startStreaming,
    stopStreaming,
    reset,
  }
})
