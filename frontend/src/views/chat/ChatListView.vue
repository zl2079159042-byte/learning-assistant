<template>
  <div class="chat-view">
    <h2>💬 对话学习</h2>
    <p class="desc">与 AI 导师对话，苏格拉底式引导学习</p>

    <div class="chat-box">
      <div class="messages" ref="msgBox">
        <div v-if="msgs.length === 0 && !streaming" class="empty">
          <p>👋 你好！我是你的 AI 学习导师，告诉我你想学什么？</p>
          <t-space style="margin-top:16px">
            <t-tag v-for="q in hints" :key="q" class="hint" @click="send(q)">{{ q }}</t-tag>
          </t-space>
        </div>
        <div v-for="m in msgs" :key="m.id" :class="['msg', m.role]">
          <span class="avatar">{{ m.role === 'user' ? '👤' : '🤖' }}</span>
          <div :class="['bubble', m.role]">
            <div class="markdown-body" v-html="renderMd(m.content)" />
          </div>
        </div>
        <div v-if="streaming && stream" class="msg ai">
          <span class="avatar">🤖</span>
          <div class="bubble ai">
            <div class="markdown-body" v-html="renderMd(stream)" />
            <span class="streaming-cursor" />
          </div>
        </div>
      </div>
      <div class="input-row">
        <t-textarea v-model="input" placeholder="输入问题... (Enter 发送)" :autosize="{ minRows: 2, maxRows: 4 }" @keydown.enter.exact.prevent="send()" />
        <t-button theme="primary" :loading="streaming" :disabled="!input.trim()" @click="send()">发送</t-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useLearningStore } from '@/stores/learning'
import { sseFetch } from '@/api/client'
import MarkdownIt from 'markdown-it'

const store = useLearningStore()
const input = ref('')
const msgs = ref([])
const stream = ref('')
const streaming = ref(false)
const sessionId = ref(null)
const msgBox = ref(null)
let counter = 0

const md = new MarkdownIt({ html: false, breaks: true, linkify: true })
const renderMd = (c) => md.render(c)
const hints = ['我想学 Python 基础', '帮我理解机器学习', '讲解 HTTP 协议', '怎么高效背单词？']

function scroll() { nextTick(() => { const el = msgBox.value; if (el) el.scrollTop = el.scrollHeight }) }

async function send(preset) {
  const msg = preset || input.value.trim()
  if (!msg || streaming.value) return
  msgs.value.push({ id: ++counter, role: 'user', content: msg })
  input.value = ''
  scroll()
  streaming.value = true
  stream.value = ''
  try {
    const resp = await sseFetch('/api/chat/send', { session_id: sessionId.value, message: msg, model: store.currentModel })
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
          const d = line.slice(6)
          try { const p = JSON.parse(d); if (p.session_id) sessionId.value = p.session_id } catch (_) { stream.value += d }
        }
      }
    }
  } catch (e) { console.error(e) } finally {
    if (stream.value) msgs.value.push({ id: ++counter, role: 'ai', content: stream.value })
    stream.value = ''
    streaming.value = false
    scroll()
  }
}
</script>

<style scoped>
.chat-view { max-width: 800px; margin: 0 auto; height: calc(100vh - 100px); display: flex; flex-direction: column; }
.desc { color: #86909c; margin-bottom: 16px; }
.chat-box { flex: 1; display: flex; flex-direction: column; border: 1px solid #e7e7e7; border-radius: 12px; background: #fafafa; overflow: hidden; }
.messages { flex: 1; overflow-y: auto; padding: 20px; }
.empty { text-align: center; padding: 40px; color: #4e5969; }
.hint { cursor: pointer; }
.msg { display: flex; gap: 10px; margin-bottom: 16px; }
.msg.user { flex-direction: row-reverse; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: #f0f5ff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 16px; }
.bubble { max-width: 72%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.6; }
.bubble.ai { background: #fff; border: 1px solid #e7e7e7; }
.bubble.user { background: #0052d9; color: #fff; }
.input-row { padding: 12px; background: #fff; border-top: 1px solid #e7e7e7; display: flex; gap: 8px; align-items: flex-end; }
.input-row :deep(.t-textarea) { flex: 1; }
</style>
