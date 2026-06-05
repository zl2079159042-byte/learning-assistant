import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client.js'

export const useKnowledgeStore = defineStore('knowledge', () => {
  // --- State ---
  const items = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)

  // --- Actions ---
  async function fetchList(params = {}) {
    loading.value = true
    try {
      const query = {
        page: params.page || page.value,
        page_size: params.pageSize || pageSize.value,
        ...params,
      }

      const data = await api.listKnowledge(query)

      items.value = data.items
      total.value = data.total
      page.value = data.page
      pageSize.value = data.page_size

      return data
    } finally {
      loading.value = false
    }
  }

  async function updateKnowledge(id, payload) {
    loading.value = true
    try {
      const updated = await api.updateKnowledge(id, payload)
      const index = items.value.findIndex((item) => item.id === id)
      if (index !== -1) {
        items.value[index] = updated
      }
      return updated
    } finally {
      loading.value = false
    }
  }

  async function deleteKnowledge(id) {
    loading.value = true
    try {
      await api.deleteKnowledge(id)
      items.value = items.value.filter((item) => item.id !== id)
      total.value = Math.max(0, total.value - 1)
    } finally {
      loading.value = false
    }
  }

  function reset() {
    items.value = []
    total.value = 0
    page.value = 1
    pageSize.value = 20
    loading.value = false
  }

  return {
    // state
    items,
    total,
    page,
    pageSize,
    loading,
    // actions
    fetchList,
    updateKnowledge,
    deleteKnowledge,
    reset,
  }
})
