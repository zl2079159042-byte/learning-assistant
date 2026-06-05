<template>
  <div class="stream-text">
    <MarkdownViewer :content="content" />
    <span v-if="isStreaming" class="blinking-cursor">|</span>
  </div>
</template>

<script setup>
import MarkdownViewer from './MarkdownViewer.vue'

defineProps<{
  content: string
  isStreaming: boolean
}>()
</script>

<style scoped>
.stream-text {
  display: inline;
}

.blinking-cursor {
  display: inline;
  font-weight: bold;
  color: #0052d9;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}
</style>
