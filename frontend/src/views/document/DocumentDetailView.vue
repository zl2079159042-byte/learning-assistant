<template>
  <div class="document-detail">
    <h2>文档详情</h2>
    <p>文档详情: {{ id }}</p>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
const id = route.params.id
</script>

<style scoped>
.document-detail {
  padding: 16px;
}
</style>
