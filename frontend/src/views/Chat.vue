<template>
  <div class="chat-page">
    <div class="chat-container">
      <div class="sidebar">
        <div class="sidebar-header">
          <h3>🤖 AI 助手</h3>
          <el-button type="primary" size="small" @click="createSession">
            <el-icon Plus /> 新对话
          </el-button>
        </div>
        
        <div class="session-list">
          <div 
            v-for="session in sessions" 
            :key="session.id"
            :class="['session-item', { active: currentSessionId === session.id }]"
            @click="selectSession(session.id)"
          >
            <div class="session-info">
              <div class="session-title">{{ session.title }}</div>
              <div class="session-preview">{{ session.last_message || '暂无消息' }}</div>
            </div>
            <div class="session-actions">
              <el-button 
                size="small" 
                icon="Edit" 
                @click.stop="startEditTitle(session)"
                class="edit-btn"
              />
              <el-button 
                size="small" 
                icon="Delete" 
                @click.stop="deleteSession(session.id)"
                class="delete-btn"
              />
            </div>
          </div>
          
          <div v-if="sessions.length === 0" class="empty-state">
            <el-icon ChatDotRound class="empty-icon" />
            <p>暂无对话</p>
            <p class="empty-hint">点击上方按钮开始新对话</p>
          </div>
        </div>
      </div>
      
      <div class="chat-area">
        <div v-if="currentSession" class="chat-content">
          <div class="chat-header">
            <div class="chat-title">
              <template v-if="editingSessionId === currentSession.id">
                <el-input 
                  v-model="editingTitle" 
                  @blur="saveEditTitle"
                  @keyup.enter="saveEditTitle"
                  class="title-input"
                  ref="titleInput"
                />
              </template>
              <template v-else>
                {{ currentSession.title }}
                <el-button 
                  size="small" 
                  icon="Edit" 
                  @click="startEditTitle(currentSession)"
                  class="title-edit-btn"
                />
              </template>
            </div>
            <div class="chat-meta">{{ formatDate(currentSession.updated_at) }}</div>
          </div>
          
          <div class="chat-messages" ref="messagesContainer">
            <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
              <div class="message-header">
                <strong>{{ msg.role === 'user' ? '你' : 'AI 助手' }}</strong>
                <span class="message-time">{{ formatDate(msg.created_at) }}</span>
              </div>
              <div class="message-content" v-html="formatMessage(msg.content)"></div>
              <div v-if="msg.stdout" class="output">
                <strong>输出：</strong>
                <pre>{{ msg.stdout }}</pre>
              </div>
              <div v-if="msg.stderr" class="error">
                <strong>错误：</strong>
                <pre>{{ msg.stderr }}</pre>
              </div>
              <div v-if="msg.images && msg.images.length" class="images">
                <div v-for="(img, i) in msg.images" :key="i" class="image-item">
                  <img :src="img" :alt="`Generated image ${i + 1}`" />
                  <button class="download-btn" @click="downloadImage(img)" title="下载图片">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="7 10 12 15 17 10"/>
                      <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            
            <div v-if="loading" class="message bot">
              <div class="message-header"><strong>AI 助手</strong></div>
              <div class="message-content">
                <div class="typing">正在思考...</div>
              </div>
            </div>
            
            <div v-if="!loading && messages.length === 0" class="welcome-message">
              <h4>👋 你好！我是你的 AI 代码助手</h4>
              <p>我可以帮你编写和运行 Python 代码，支持生成图片和动图！</p>
              <ul>
                <li><strong>画图：</strong>用 matplotlib 画一条正弦曲线</li>
                <li><strong>动画：</strong>创建小球圆周运动动画</li>
                <li><strong>问题：</strong>任何编程相关的问题都可以问我</li>
              </ul>
            </div>
          </div>
          
          <div class="input-area">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="输入消息... (Shift+Enter 换行，Enter 发送)"
              @keydown="handleKeydown"
              :disabled="loading || !currentSession"
            />
            <el-button type="primary" @click="sendMessage" :loading="loading" :disabled="!currentSession">
              发送
            </el-button>
          </div>
        </div>
        
        <div v-else class="no-session">
          <el-icon Message class="no-session-icon" />
          <p>选择一个对话开始聊天</p>
          <el-button type="primary" @click="createSession">
            <el-icon Plus /> 创建新对话
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { Plus, ChatDotRound, Message, Edit, Delete } from '@element-plus/icons-vue'
import api from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'

hljs.registerLanguage('python', python)

const sessions = ref([])
const currentSessionId = ref(null)
const currentSession = ref(null)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const editingSessionId = ref(null)
const editingTitle = ref('')
const titleInput = ref(null)

const renderer = new marked.Renderer()

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

renderer.code = function(code) {
  const text = typeof code === 'string' ? code : (code.text || '')
  const lang = code.lang || 'python'
  const encodedCode = encodeURIComponent(text)
  
  let highlightedCode
  try {
    highlightedCode = hljs.highlight(text, { language: lang }).value
  } catch {
    highlightedCode = escapeHtml(text)
  }
  
  return `<div class="code-block-container" data-code="${encodedCode}">
    <div class="code-block-header">
      <span class="code-lang">${lang}</span>
      <div class="code-actions">
        <button class="run-btn" title="运行代码">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          <span>运行</span>
        </button>
        <button class="copy-btn" title="复制代码">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
            <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
          </svg>
        </button>
      </div>
    </div>
    <pre class="code-pre"><code class="hljs language-${lang}">${highlightedCode}</code></pre>
  </div>`
}

marked.use({ renderer })

document.addEventListener('click', function(e) {
  const codeBlock = e.target.closest('.code-block-container')
  if (!codeBlock) return
  
  const encodedCode = codeBlock.getAttribute('data-code')
  if (!encodedCode) return
  
  const code = decodeURIComponent(encodedCode)
  
  if (e.target.closest('.copy-btn')) {
    navigator.clipboard.writeText(code).then(() => {
      const btn = e.target.closest('.copy-btn')
      btn.classList.add('copied')
      setTimeout(() => btn.classList.remove('copied'), 2000)
    })
    return
  }
  
  if (e.target.closest('.run-btn')) {
    const btn = e.target.closest('.run-btn')
    btn.classList.add('running')
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"><animate attributeName="stroke-dasharray" values="0,200;100,200;0,200" dur="1.5s" repeatCount="indefinite"/></circle></svg><span>运行中...</span>'
    
    api.post('/execute-code', { code }).then(response => {
      if (response.data.success) {
        const resultDiv = document.createElement('div')
        resultDiv.className = 'code-result'
        
        let resultHtml = ''
        if (response.data.images && response.data.images.length > 0) {
          resultHtml += '<div class="result-images">'
          response.data.images.forEach(img => {
            const filename = img.split('/').pop()
            resultHtml += `<div class="image-item">
              <img src="${img}" alt="执行结果" />
              <button class="download-btn" onclick="downloadImage('${img}', '${filename}')" title="下载图片">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
              </button>
            </div>`
          })
          resultHtml += '</div>'
        }
        
        if (response.data.stdout) {
          resultHtml += `<pre class="result-stdout">${escapeHtml(response.data.stdout)}</pre>`
        }
        
        if (response.data.stderr) {
          resultHtml += `<pre class="result-stderr">${escapeHtml(response.data.stderr)}</pre>`
        }
        
        resultDiv.innerHTML = resultHtml
        codeBlock.parentNode.insertBefore(resultDiv, codeBlock.nextSibling)
      }
    }).catch(error => {
      ElMessage.error('代码执行失败：' + (error.response?.data?.message || error.message))
    }).finally(() => {
      btn.classList.remove('running')
      btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg><span>运行</span>'
    })
  }
})

async function loadSessions() {
  try {
    const response = await api.get('/chat/sessions')
    sessions.value = response.data
    if (sessions.value.length > 0 && !currentSessionId.value) {
      selectSession(sessions.value[0].id)
    }
  } catch (error) {
    ElMessage.error('加载会话列表失败')
  }
}

async function createSession() {
  try {
    const response = await api.post('/chat/sessions', { title: '新对话' })
    sessions.value.unshift(response.data.session)
    selectSession(response.data.session.id)
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}

async function selectSession(sessionId) {
  currentSessionId.value = sessionId
  loading.value = true
  
  try {
    const response = await api.get(`/chat/sessions/${sessionId}`)
    currentSession.value = response.data
    messages.value = response.data.messages
  } catch (error) {
    ElMessage.error('加载会话失败')
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

async function deleteSession(sessionId) {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/chat/sessions/${sessionId}`)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
      currentSession.value = null
      messages.value = []
    }
    
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function startEditTitle(session) {
  editingSessionId.value = session.id
  editingTitle.value = session.title
  nextTick(() => {
    const input = document.querySelector('.title-input')
    if (input) {
      input.focus()
      input.select()
    }
  })
}

async function saveEditTitle() {
  if (!editingSessionId.value || !editingTitle.value.trim()) {
    editingSessionId.value = null
    return
  }
  
  try {
    await api.put(`/chat/sessions/${editingSessionId.value}`, { title: editingTitle.value.trim() })
    
    const session = sessions.value.find(s => s.id === editingSessionId.value)
    if (session) {
      session.title = editingTitle.value.trim()
    }
    if (currentSession.value && currentSession.value.id === editingSessionId.value) {
      currentSession.value.title = editingTitle.value.trim()
    }
    
    ElMessage.success('修改成功')
  } catch (error) {
    ElMessage.error('修改失败')
  } finally {
    editingSessionId.value = null
  }
}

function formatMessage(content) {
  return marked(content, {
    breaks: true,
    gfm: true
  })
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

async function downloadImage(url, filename = null) {
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('图片下载失败')
    }
    
    const blob = await response.blob()
    const blobUrl = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = blobUrl
    const fileName = filename || url.split('/').pop() || `image_${Date.now()}.png`
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(blobUrl)
    
    ElMessage.success('图片下载成功')
  } catch (error) {
    ElMessage.error('图片下载失败：' + error.message)
  }
}

window.downloadImage = downloadImage

async function sendMessage() {
  const content = inputMessage.value.trim()
  if (!content || loading.value || !currentSessionId.value) return
  
  messages.value.push({ role: 'user', content, created_at: new Date().toISOString() })
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()
  
  try {
    const response = await api.post(`/chat/sessions/${currentSessionId.value}/messages`, { message: content })
    
    if (response.data.success) {
      messages.value.push(response.data.message)
      
      const sessionIndex = sessions.value.findIndex(s => s.id === currentSessionId.value)
      if (sessionIndex !== -1) {
        sessions.value[sessionIndex].last_message = content.length > 50 ? content.slice(0, 50) + '...' : content
        sessions.value[sessionIndex].updated_at = new Date().toISOString()
        sessions.value.unshift(sessions.value.splice(sessionIndex, 1)[0])
      }
    }
  } catch (error) {
    ElMessage.error('发送消息失败：' + (error.response?.data?.reply || error.message))
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.chat-container {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 320px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1e293b;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
  border: 1px solid #e2e8f0;
}

.session-item:hover {
  background: #f1f5f9;
}

.session-item.active {
  background: #dbeafe;
  border-color: #3b82f6;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-preview {
  font-size: 13px;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.edit-btn, .delete-btn {
  color: #94a3b8;
}

.edit-btn:hover {
  color: #3b82f6;
}

.delete-btn:hover {
  color: #ef4444;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #94a3b8;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 4px 0;
}

.empty-hint {
  font-size: 13px;
  color: #cbd5e1;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.chat-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-input {
  width: 200px;
}

.title-edit-btn {
  color: #94a3b8;
  padding: 4px;
}

.title-edit-btn:hover {
  color: #3b82f6;
}

.chat-meta {
  font-size: 13px;
  color: #94a3b8;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f5f7fa;
}

.welcome-message {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(124, 58, 237, 0.1));
  border: 1px solid rgba(37, 99, 235, 0.2);
  border-radius: 12px;
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
}

.welcome-message h4 {
  margin: 0 0 12px 0;
  color: #2563eb;
}

.welcome-message ul {
  margin: 12px 0 0 20px;
  padding: 0;
}

.welcome-message li {
  padding: 6px 0;
}

.message {
  margin-bottom: 20px;
}

.message.user {
  text-align: right;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: #64748b;
  font-size: 14px;
}

.message.user .message-header {
  justify-content: flex-end;
}

.message-time {
  font-size: 12px;
  color: #94a3b8;
  margin-left: 8px;
}

.message-content {
  display: inline-block;
  max-width: 70%;
  padding: 14px 18px;
  border-radius: 14px;
  text-align: left;
  word-break: break-word;
}

.message.user .message-content {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: white;
  border-radius: 14px 14px 4px 14px;
}

.message.bot .message-content {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 14px 14px 14px 4px;
}



.output, .error {
  margin-top: 12px;
  padding: 14px;
  border-radius: 10px;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
}

.output {
  background: #f0fdf4;
  border: 1px solid #86efac;
}

.error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
}

.images {
  margin-top: 12px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.image-item {
  position: relative;
  display: inline-block;
}

.image-item img {
  max-width: 100%;
  max-height: 350px;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.image-item .download-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
  padding: 0;
}

.image-item:hover .download-btn {
  opacity: 1;
}

.image-item .download-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}

.message-content h1,
.message-content h2,
.message-content h3,
.message-content h4,
.message-content h5,
.message-content h6 {
  font-weight: 600;
  margin: 16px 0 12px 0;
  color: #1e293b;
}

.message-content h1 {
  font-size: 24px;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 8px;
}

.message-content h2 {
  font-size: 20px;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 6px;
}

.message-content h3 {
  font-size: 17px;
  display: flex;
  align-items: center;
}

.message-content h3::before {
  content: '🔹';
  margin-right: 8px;
}

.message-content h4 {
  font-size: 16px;
}

.message-content h5 {
  font-size: 15px;
}

.message-content h6 {
  font-size: 14px;
  color: #64748b;
}

.message-content strong {
  font-weight: 600;
  color: #1e293b;
}

.message-content em {
  font-style: italic;
}

.message-content code:not(pre code) {
  background: #f1f5f9;
  color: #e11d48;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
}

.message-content ul,
.message-content ol {
  margin: 12px 0;
  padding-left: 28px;
}

.message-content li {
  margin: 8px 0;
  line-height: 1.6;
}

.message-content ul li::marker {
  color: #3b82f6;
  font-weight: bold;
}

.message-content ol li::marker {
  color: #64748b;
  font-weight: 500;
}

.message-content p {
  margin: 8px 0;
  line-height: 1.8;
}

.message-content blockquote {
  border-left: 4px solid #3b82f6;
  padding: 8px 16px;
  margin: 12px 0;
  background: #f0f9ff;
  border-radius: 0 8px 8px 0;
  color: #334155;
}

.message-content hr {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 20px 0;
}

.message-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 14px;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message-content th {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: white;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
}

.message-content td {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: top;
}

.message-content tbody tr:hover {
  background: #f8fafc;
}

.message-content tbody tr:last-child td {
  border-bottom: none;
}

.message-content a {
  color: #3b82f6;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}

.message-content a:hover {
  border-bottom-color: #3b82f6;
}

.typing {
  display: flex;
  gap: 4px;
  color: #94a3b8;
}

.typing::after {
  content: '';
  animation: typing 1.4s infinite;
}

@keyframes typing {
  0%, 20% { content: '.'; }
  40% { content: '..'; }
  60%, 100% { content: '...'; }
}

.input-area {
  padding: 16px 24px;
  background: white;
  border-top: 1px solid #e2e8f0;
}

.no-session {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

.no-session-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.no-session p {
  margin: 0 0 16px 0;
  font-size: 16px;
}
</style>