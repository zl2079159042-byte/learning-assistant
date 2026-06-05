<template>
  <div
    class="message-bubble"
    :class="[`message-bubble--${message.role}`]"
  >
    <div class="bubble-avatar">
      <span class="avatar-emoji">{{ avatarEmoji }}</span>
    </div>
    <div class="bubble-body">
      <div class="bubble-content">
        <MarkdownViewer :content="message.content" />
      </div>
      <div class="bubble-time">{{ formattedTime }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownViewer from './MarkdownViewer.vue'

interface ChatMessage {
  id: string
  role: 'user' | 'ai' | 'system'
  content: string
  created_at: string
}

const props = defineProps<{
  message: ChatMessage
}>()

const avatarEmoji = computed<string>(() => {
  switch (props.message.role) {
    case 'user':
      return '👤'
    case 'ai':
      return '🤖'
    default:
      return '⚙️'
  }
})

const formattedTime = computed<string>(() => {
  if (!props.message.created_at) return ''
  const date = new Date(props.message.created_at)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)

  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes} 分钟前`

  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours} 小时前`

  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays} 天前`

  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d} ${hh}:${mm}`
})
</script>

<style scoped>
.message-bubble {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  max-width: 80%;
}

.message-bubble--user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-bubble--user .bubble-body {
  align-items: flex-end;
}

.message-bubble--user .bubble-content {
  background-color: #0052d9;
  color: #ffffff;
}

.message-bubble--ai .bubble-content {
  background-color: #ffffff;
  color: #242424;
}

.bubble-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-emoji {
  font-size: 18px;
  line-height: 1;
}

.bubble-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.bubble-content {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Override markdown colors inside blue user bubble */
.message-bubble--user .bubble-content :deep(.markdown-body) {
  color: #ffffff;
}

.message-bubble--user .bubble-content :deep(a) {
  color: #b3d4ff;
}

.message-bubble--user .bubble-content :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.75);
}

.message-bubble--user .bubble-content :deep(code) {
  background-color: rgba(255, 255, 255, 0.15);
  color: #ffffff;
}

.bubble-time {
  font-size: 12px;
  color: #999;
  padding: 0 4px;
}
</style>
