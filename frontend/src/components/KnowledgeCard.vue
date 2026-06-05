<template>
  <t-card class="knowledge-card" hover>
    <template #header>
      <div class="card-header">
        <span class="card-title">{{ knowledge.title }}</span>
        <t-tag
          :theme="masteryTheme"
          variant="light"
          size="small"
        >
          掌握度 {{ masteryPercent }}%
        </t-tag>
      </div>
    </template>

    <div class="card-body">
      <MarkdownViewer :content="knowledge.content" />
    </div>

    <template #actions>
      <t-space>
        <t-button
          theme="default"
          variant="text"
          size="small"
          @click="$emit('review', knowledge.id)"
        >
          复习
        </t-button>
        <t-button
          theme="default"
          variant="text"
          size="small"
          @click="$emit('edit', knowledge.id)"
        >
          编辑
        </t-button>
        <t-button
          theme="danger"
          variant="text"
          size="small"
          @click="$emit('delete', knowledge.id)"
        >
          删除
        </t-button>
      </t-space>
    </template>
  </t-card>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownViewer from './MarkdownViewer.vue'

interface KnowledgePoint {
  id: string
  title: string
  content: string
  mastery_level: number
  tags?: string
  category?: string
}

const props = defineProps<{
  knowledge: KnowledgePoint
}>()

defineEmits<{
  review: [id: string]
  edit: [id: string]
  delete: [id: string]
}>()

const masteryPercent = computed<number>(() => {
  return Math.round(props.knowledge.mastery_level * 100)
})

const masteryTheme = computed<string>(() => {
  const pct = masteryPercent.value
  if (pct >= 80) return 'success'
  if (pct >= 50) return 'warning'
  return 'default'
})
</script>

<style scoped>
.knowledge-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #242424;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 12px;
}

.card-body {
  max-height: 200px;
  overflow-y: auto;
}
</style>
