<template>
  <t-layout class="app-layout">
    <t-header class="app-header">
      <div class="header-brand">
        <span class="brand-title">AI 学习助手</span>
      </div>
      <t-menu
        mode="horizontal"
        theme="light"
        :value="activeMenu"
        class="header-menu"
        @change="onMenuChange"
      >
        <t-menu-item value="/home">首页</t-menu-item>
        <t-menu-item value="/learn">学习</t-menu-item>
        <t-menu-item value="/chat">对话</t-menu-item>
        <t-menu-item value="/document">文档</t-menu-item>
        <t-menu-item value="/knowledge">知识库</t-menu-item>
        <t-menu-item value="/history">历史</t-menu-item>
      </t-menu>
    </t-header>
    <t-content class="app-content">
      <router-view />
    </t-content>
  </t-layout>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/learn')) return '/learn'
  if (path.startsWith('/chat')) return '/chat'
  if (path.startsWith('/document')) return '/document'
  if (path.startsWith('/knowledge')) return '/knowledge'
  if (path.startsWith('/history')) return '/history'
  return '/home'
})

function onMenuChange(value) {
  router.push(value)
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  background: var(--td-bg-color-page, #f5f5f5);
}

.app-header {
  display: flex;
  align-items: center;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid var(--td-component-stroke, #e7e7e7);
  height: 56px;
}

.header-brand {
  margin-right: 32px;
}

.brand-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--td-brand-color, #0052d9);
  white-space: nowrap;
}

.header-menu {
  flex: 1;
}

.app-content {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
</style>
