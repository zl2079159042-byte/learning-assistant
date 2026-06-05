<template>
  <div class="doc-view">
    <h2>📄 文档学习</h2>
    <p class="desc">上传 PDF/Word/Markdown/TXT，AI 解析后拆解知识点</p>

    <t-upload v-model="files" :action="uploadUrl" accept=".pdf,.docx,.md,.txt" :max="1" :on-success="onOk" draggable theme="file-flow">
      <template #drag-content>
        <div class="upload-zone"><span class="icon">📁</span><p>点击或拖拽文件上传</p><p class="hint">PDF / Word / Markdown / TXT</p></div>
      </template>
    </t-upload>

    <div v-if="doc" class="preview">
      <t-divider>文档预览</t-divider>
      <t-card :title="doc.title">
        <pre class="preview-text">{{ doc.source_text?.slice(0, 1500) }}...</pre>
        <t-button theme="primary" :loading="streaming" @click="learn" style="margin-top:12px">开始学习</t-button>
      </t-card>
    </div>

    <div v-if="result || streaming" class="result">
      <t-divider>学习结果</t-divider>
      <t-card>
        <div class="markdown-body" v-html="renderMd(result)" />
        <span v-if="streaming" class="streaming-cursor" />
      </t-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useLearningStore } from '@/stores/learning'
import { sseUploadFile } from '@/api/client'
import MarkdownIt from 'markdown-it'

const store = useLearningStore()
const files = ref([])
const doc = ref(null)
const result = ref('')
const streaming = ref(false)
const md = new MarkdownIt({ html: false, breaks: true })
const renderMd = (c) => md.render(c)

const uploadUrl = (() => {
  const base = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || '')
  return base + '/api/document/upload'
})()

function onOk(res) { if (res.response) doc.value = res.response }

async function learn() {
  if (!doc.value) return
  streaming.value = true
  result.value = ''
  const fd = new FormData()
  fd.append('session_id', doc.value.session_id)
  fd.append('model', store.currentModel)
  try {
    const resp = await sseUploadFile('/api/document/learn', fd)
    const reader = resp.body.getReader()
    const dec = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true })
      for (const line of buf.split('\n')) {
        if (line.startsWith('data: ')) result.value += line.slice(6)
      }
      buf = ''
    }
  } catch (e) { console.error(e) } finally { streaming.value = false }
}
</script>

<style scoped>
.doc-view { max-width: 800px; margin: 0 auto; }
.desc { color: #86909c; margin-bottom: 20px; }
.upload-zone { text-align: center; padding: 40px; }
.icon { font-size: 48px; }
.hint { color: #c9cdd4; font-size: 13px; margin-top: 8px; }
.preview { margin-top: 24px; }
.preview-text { max-height: 200px; overflow-y: auto; font-size: 13px; line-height: 1.8; background: #fafafa; padding: 12px; border-radius: 8px; white-space: pre-wrap; }
.result { margin-top: 24px; }
</style>
