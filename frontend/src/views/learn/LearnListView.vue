<template>
  <div class="learn-view">
    <h2>📝 粘贴学习</h2>
    <p class="desc">贴上文本，AI 自动拆解为结构化知识点</p>

    <t-textarea v-model="text" placeholder="在此粘贴学习材料（至少10字）..." :autosize="{ minRows: 8, maxRows: 18 }" />
    <t-input v-model="title" placeholder="学习名称（可选）" style="margin-top: 12px;" />
    <t-button theme="primary" size="large" :loading="streaming" :disabled="text.length < 10" @click="start" style="margin-top: 12px;">
      {{ streaming ? 'AI 正在分析...' : '开始学习' }}
    </t-button>

    <div v-if="result || streaming" class="result-area">
      <t-divider>学习结果</t-divider>
      <t-card>
        <div class="markdown-body" v-html="rendered" />
        <span v-if="streaming" class="streaming-cursor" />
      </t-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useLearningStore } from '@/stores/learning'
import { sseFetch } from '@/api/client'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const store = useLearningStore()
const text = ref('')
const title = ref('')
const result = ref('')
const streaming = ref(false)

const md = new MarkdownIt({ html: false, breaks: true, linkify: true,
  highlight(str, lang) {
    if (lang && hljs.getLanguage(lang)) return '<pre><code>' + hljs.highlight(str, { language: lang }).value + '</code></pre>'
    return '<pre><code>' + md.utils.escapeHtml(str) + '</code></pre>'
  }
})

const rendered = computed(() => md.render(result.value))

async function start() {
  if (text.value.length < 10) return
  streaming.value = true
  result.value = ''
  try {
    const resp = await sseFetch('/api/learn/analyze', {
      text: text.value, title: title.value || '未命名学习', model: store.currentModel,
    })
    const reader = resp.body.getReader()
    const dec = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          result.value += line.slice(6)
        }
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    streaming.value = false
  }
}
</script>

<style scoped>
.learn-view { max-width: 800px; margin: 0 auto; }
.desc { color: #86909c; margin-bottom: 20px; }
.result-area { margin-top: 32px; }
</style>
