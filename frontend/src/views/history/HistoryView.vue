<template>
  <div class="history">
    <h2>📜 学习历史</h2>
    <t-tabs v-model="tab" @change="load">
      <t-tab-panel value="" label="全部" />
      <t-tab-panel value="learn" label="粘贴学习" />
      <t-tab-panel value="chat" label="对话学习" />
      <t-tab-panel value="document" label="文档学习" />
    </t-tabs>
    <t-loading :loading="loading">
      <div v-if="!items.length && !loading" class="empty">暂无学习记录</div>
      <t-list v-else>
        <t-list-item v-for="item in items" :key="item.id">
          <t-list-item-meta :title="item.title" :description="labels[item.type] + ' · ' + (item.knowledge_count||0) + ' 知识点 · ' + fmt(item.created_at)" />
          <template #action><t-button variant="text" size="small" @click="$router.push('/'+item.type+'/'+item.id)">查看</t-button></template>
        </t-list-item>
      </t-list>
    </t-loading>
    <t-pagination v-if="total > ps" v-model="pg" :total="total" :page-size="ps" @change="load" style="margin-top:20px" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import client from '@/api/client'

const items = ref([]), total = ref(0), pg = ref(1), ps = 20, loading = ref(false), tab = ref('')
const labels = { learn: '粘贴学习', chat: '对话学习', document: '文档学习' }
const fmt = (d) => new Date(d).toLocaleDateString('zh-CN')
async function load() {
  loading.value = true
  try { const { data } = await client.get('/history', { params: { page: pg.value, page_size: ps, session_type: tab.value || undefined } }); items.value = data.items; total.value = data.total } catch (_) {} finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.history { max-width: 800px; margin: 0 auto; }
.empty { text-align: center; padding: 60px; color: #86909c; }
</style>
