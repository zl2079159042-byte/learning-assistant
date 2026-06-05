<template>
  <div class="learn-detail">
    <h2>学习详情</h2>
    <p>学习内容详情: {{ id }}</p>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
const id = route.params.id
</script>

<style scoped>
.learn-detail {
  padding: 16px;
}
</style>
