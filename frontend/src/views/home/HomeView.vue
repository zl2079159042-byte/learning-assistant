<template>
  <div class="home">
    <div class="hero"><h1>👋 AI 学习助手</h1><p>选择一种方式，开始高效学习</p></div>
    <div class="cards">
      <t-card v-for="c in cards" :key="c.path" hover-shadow class="card" @click="$router.push(c.path)">
        <div class="card-icon">{{ c.icon }}</div>
        <h3>{{ c.title }}</h3>
        <p>{{ c.desc }}</p>
      </t-card>
    </div>
    <div v-if="stats" class="stats">
      <t-divider>学习统计</t-divider>
      <t-row :gutter="16">
        <t-col :span="3" v-for="s in statItems" :key="s.label">
          <t-card bordered class="stat"><div class="val">{{ s.value }}</div><div class="lbl">{{ s.label }}</div></t-card>
        </t-col>
      </t-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import client from '@/api/client'

const stats = ref(null)
const cards = [
  { path: '/learn', icon: '📝', title: '粘贴学习', desc: '粘贴文本，AI 拆解知识点' },
  { path: '/chat', icon: '💬', title: '对话学习', desc: '苏格拉底式 AI 导师互动' },
  { path: '/document', icon: '📄', title: '文档学习', desc: '上传文档，智能解析学习' },
]
const statItems = computed(() => !stats.value ? [] : [
  { label: '学习会话', value: stats.value.total_sessions },
  { label: '知识点', value: stats.value.total_knowledge_points },
  { label: '粘贴学习', value: stats.value.total_learn },
  { label: '对话学习', value: stats.value.total_chat },
])
onMounted(async () => { try { stats.value = await client.get('/history/stats') } catch (_) {} })
</script>

<style scoped>
.home { max-width: 800px; margin: 0 auto; text-align: center; padding-top: 24px; }
.hero h1 { font-size: 28px; margin-bottom: 8px; }
.hero p { color: #86909c; margin-bottom: 40px; }
.cards { display: flex; gap: 24px; justify-content: center; margin-bottom: 48px; }
.card { width: 220px; cursor: pointer; transition: transform .2s; }
.card:hover { transform: translateY(-4px); }
.card-icon { font-size: 40px; margin-bottom: 8px; }
.card h3 { margin-bottom: 8px; }
.card p { color: #86909c; font-size: 13px; }
.stat { text-align: center; }
.val { font-size: 28px; font-weight: 700; color: #0052d9; }
.lbl { font-size: 13px; color: #86909c; margin-top: 4px; }
</style>
