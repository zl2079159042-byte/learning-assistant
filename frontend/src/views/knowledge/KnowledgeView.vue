<template>
  <div class="kb">
    <div class="header">
      <h2>📚 知识库</h2>
      <t-input v-model="kw" placeholder="搜索知识点..." clearable @change="search" style="width:280px"><template #prefix-icon><t-icon name="search" /></template></t-input>
    </div>
    <t-loading :loading="loading">
      <div v-if="!items.length" class="empty">暂无知识点，去学习一下吧！</div>
      <t-card v-for="item in items" :key="item.id" class="kc" hover-shadow>
        <template #header><div class="title-row"><span>📌 {{ item.title }}</span><t-tag :theme="item.mastery_level>=80?'success':item.mastery_level>=50?'warning':'default'" size="small">掌握 {{ item.mastery_level }}%</t-tag></div></template>
        <div class="markdown-body" v-html="renderMd(item.content.slice(0, 500))" />
        <template #actions>
          <t-space><t-button variant="text" size="small" @click="del(item)"><t-icon name="delete" /> 删除</t-button></t-space>
        </template>
      </t-card>
    </t-loading>
    <t-pagination v-if="total>ps" v-model="pg" :total="total" :page-size="ps" @change="load" style="margin-top:20px" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import client from '@/api/client'
import MarkdownIt from 'markdown-it'

const items = ref([]), total = ref(0), pg = ref(1), ps = 20, loading = ref(false), kw = ref('')
const md = new MarkdownIt({ html: false, breaks: true })
const renderMd = (c) => md.render(c)
async function load() {
  loading.value = true
  try { const { data } = await client.get('/knowledge', { params: { page: pg.value, page_size: ps, keyword: kw.value || undefined } }); items.value = data.items; total.value = data.total } catch(_){} finally{ loading.value = false }
}
function search() { pg.value = 1; load() }
async function del(item) { if (confirm('删除「' + item.title + '」？')) { await client.delete('/knowledge/' + item.id); load() } }
onMounted(load)
</script>

<style scoped>
.kb { max-width: 800px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.empty { text-align: center; padding: 60px; color: #86909c; }
.kc { margin-bottom: 16px; }
.title-row { display: flex; justify-content: space-between; align-items: center; }
</style>
