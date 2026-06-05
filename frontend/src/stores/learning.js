import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'learning-current-model'

function loadFromStorage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored || 'qwen'
  } catch {
    return 'qwen'
  }
}

export const useLearningStore = defineStore('learning', () => {
  const currentModel = ref(loadFromStorage())

  watch(currentModel, (newVal) => {
    try {
      localStorage.setItem(STORAGE_KEY, newVal)
    } catch {
      // localStorage may be unavailable (private browsing, quota exceeded)
    }
  })

  function setModel(model) {
    currentModel.value = model
  }

  return {
    currentModel,
    setModel,
  }
})
