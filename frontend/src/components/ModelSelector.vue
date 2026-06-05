<template>
  <div class="model-selector">
    <t-select
      :model-value="learningStore.currentModel"
      :options="modelOptions"
      placeholder="选择模型"
      @change="handleModelChange"
    />
  </div>
</template>

<script setup>
import { useLearningStore } from '@/stores/learning'

interface ModelOption {
  label: string
  value: string
}

const learningStore = useLearningStore()

const modelOptions: ModelOption[] = [
  { label: 'DeepSeek', value: 'deepseek' },
  { label: '通义千问', value: 'qwen' },
  { label: '文心一言', value: 'wenxin' },
]

function handleModelChange(value: string): void {
  learningStore.setCurrentModel(value)
}
</script>

<style scoped>
.model-selector {
  display: flex;
  align-items: center;
  padding: 8px 16px;
}

.model-selector :deep(.t-select) {
  width: 180px;
}
</style>
