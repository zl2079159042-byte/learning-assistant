<template>
  <div class="layout">
    <Sidebar />
    <div class="layout-main">
      <header class="layout-topbar">
        <ModelSelector />
      </header>
      <main class="layout-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import ModelSelector from './ModelSelector.vue'
</script>

<style scoped>
.layout {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background-color: #f5f6f8;
}

.layout-topbar {
  display: flex;
  align-items: center;
  height: 56px;
  background-color: #ffffff;
  border-bottom: 1px solid #e7e7e7;
  padding: 0 20px;
  flex-shrink: 0;
}

.layout-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
