<template>
  <div class="chat-detail">
    <h2>对话详情</h2>
    <p>对话详情: {{ id }}</p>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
const id = route.params.id
</script>

<style scoped>
.chat-detail {
  padding: 16px;
}
</style>
