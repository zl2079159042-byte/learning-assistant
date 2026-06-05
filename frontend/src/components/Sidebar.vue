<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="logo">
        <span class="logo-icon">📚</span>
        <span class="logo-text">学习助手</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        active-class="nav-item--active"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <p class="footer-text">Learning Assistant v1.0</p>
    </div>
  </aside>
</template>

<script setup>
const navItems = [
  { path: '/home', icon: '🏠', label: '首页' },
  { path: '/learn', icon: '🎓', label: '粘贴学习' },
  { path: '/chat', icon: '💬', label: '对话学习' },
  { path: '/document', icon: '📄', label: '文档学习' },
  { path: '/knowledge', icon: '📖', label: '知识库' },
  { path: '/history', icon: '🕐', label: '学习历史' },
]
</script>

<style scoped>
.sidebar {
  width: 220px;
  min-width: 220px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #1b1b2f;
  color: #e0e0e0;
  overflow-y: auto;
}

.sidebar-header {
  padding: 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  text-decoration: none;
  color: #b0b0c0;
  font-size: 15px;
  transition: background-color 0.2s, color 0.2s;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}

.nav-item--active {
  background-color: rgba(0, 82, 217, 0.2);
  color: #4582ff;
  border-left-color: #4582ff;
}

.nav-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
}

.nav-label {
  font-weight: 500;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  text-align: center;
}

.footer-text {
  font-size: 12px;
  color: #666;
  margin: 0;
}
</style>
