<template>
  <div class="chat-history-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📋 学生 AI 聊天记录</span>
        </div>
      </template>
      
      <div class="main-content">
        <div class="student-selector">
          <el-select 
            v-model="selectedStudentId" 
            placeholder="选择学生"
            class="student-select"
            @change="loadStudentSessions"
          >
            <el-option
              v-for="student in students"
              :key="student.id"
              :label="`${student.username} - ${student.display_name}`"
              :value="student.id"
            />
          </el-select>
        </div>
        
        <div class="chat-container" v-if="selectedStudent">
          <div class="sidebar">
            <div class="sidebar-header">
              <h4>{{ selectedStudent.display_name }} 的对话</h4>
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
              </div>
              
              <div v-if="sessions.length === 0" class="empty-state">
                <el-icon ChatDotRound class="empty-icon" />
                <p>该学生暂无对话记录</p>
              </div>
            </div>
          </div>
          
          <div class="chat-area">
            <div v-if="currentSession" class="chat-content">
              <div class="chat-header">
                <div class="chat-title">{{ currentSession.title }}</div>
                <div class="chat-meta">{{ formatDate(currentSession.updated_at) }}</div>
              </div>
              
              <div class="chat-messages" ref="messagesContainer">
                <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
                  <div class="message-header">
                    <strong>{{ msg.role === 'user' ? selectedStudent.display_name : 'AI 助手' }}</strong>
                    <span class="message-time">{{ formatDate(msg.created_at) }}</span>
                  </div>
                  <div class="message-content">
                    <div v-html="formatMessage(msg.content)"></div>
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
                </div>
                
                <div v-if="messages.length === 0" class="empty-chat">
                  <p>暂无消息</p>
                </div>
              </div>
            </div>
            
            <div v-else class="no-session">
              <el-icon Message class="no-session-icon" />
              <p>选择一个对话查看详情</p>
            </div>
          </div>
        </div>
        
        <div v-else class="no-student">
          <el-icon User class="no-student-icon" />
          <p>请先选择一个学生</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ChatDotRound, Message, User } from '@element-plus/icons-vue'
import api from '@/services/api'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'

hljs.registerLanguage('python', python)

const renderer = new marked.Renderer()

renderer.code = function(code) {
  const text = typeof code === 'string' ? code : (code.text || '')
  const lang = code.lang || 'python'
  const encodedCode = encodeURIComponent(text)
  
  let highlightedCode
  try {
    highlightedCode = hljs.highlight(text, { language: lang }).value
  } catch {
    const div = document.createElement('div')
    div.textContent = text
    highlightedCode = div.innerHTML
  }
  
  return `<div class="code-block-container" data-code="${encodedCode}">
    <div class="code-block-header">
      <span class="code-lang">${lang}</span>
    </div>
    <pre class="code-pre"><code class="hljs language-${lang}">${highlightedCode}</code></pre>
  </div>`
}

marked.use({ renderer })

const students = ref([])
const selectedStudentId = ref(null)
const selectedStudent = ref(null)
const sessions = ref([])
const currentSessionId = ref(null)
const currentSession = ref(null)
const messages = ref([])
const messagesContainer = ref(null)

async function loadStudents() {
  try {
    const response = await api.get('/students')
    students.value = response.data
  } catch (error) {
    ElMessage.error('加载学生列表失败')
  }
}

async function loadStudentSessions() {
  if (!selectedStudentId.value) {
    selectedStudent.value = null
    sessions.value = []
    currentSessionId.value = null
    currentSession.value = null
    messages.value = []
    return
  }
  
  selectedStudent.value = students.value.find(s => s.id === selectedStudentId.value)
  
  try {
    const response = await api.get(`/teacher/students/${selectedStudentId.value}/chat-sessions`)
    sessions.value = response.data.sessions
    currentSessionId.value = null
    currentSession.value = null
    messages.value = []
    
    if (sessions.value.length > 0) {
      selectSession(sessions.value[0].id)
    }
  } catch (error) {
    ElMessage.error('加载会话列表失败')
  }
}

async function selectSession(sessionId) {
  currentSessionId.value = sessionId
  
  try {
    const response = await api.get(`/teacher/students/${selectedStudentId.value}/chat-sessions/${sessionId}/messages`)
    currentSession.value = response.data.session
    messages.value = response.data.messages
  } catch (error) {
    ElMessage.error('加载会话失败')
  }
}

function formatMessage(content) {
  return marked(content, {
    breaks: true,
    gfm: true
  })
}

async function downloadImage(url) {
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('图片下载失败')
    }
    
    const blob = await response.blob()
    const blobUrl = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = blobUrl
    const fileName = url.split('/').pop() || `image_${Date.now()}.png`
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

onMounted(() => {
  loadStudents()
})
</script>

<style scoped>
.chat-history-page {
  max-width: 1600px;
  margin: 0 auto;
  padding: 20px;
}

.main-content {
  padding: 0;
}

.student-selector {
  margin-bottom: 24px;
}

.student-select {
  width: 400px;
}

.chat-container {
  display: flex;
  height: 750px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.sidebar {
  width: 360px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-header h4 {
  margin: 0;
  font-size: 16px;
  color: #1e293b;
  font-weight: 600;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.session-item {
  padding: 16px;
  margin-bottom: 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
  border: 1px solid #e2e8f0;
}

.session-item:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.session-item.active {
  background: #dbeafe;
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.session-info {
  min-width: 0;
}

.session-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 15px;
}

.session-preview {
  font-size: 14px;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
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
  padding: 20px 28px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.chat-meta {
  font-size: 14px;
  color: #94a3b8;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  background: #f5f7fa;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #94a3b8;
}

.message {
  margin-bottom: 24px;
}

.message.user {
  text-align: right;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  color: #64748b;
  font-size: 15px;
}

.message.user .message-header {
  justify-content: flex-end;
}

.message-time {
  font-size: 13px;
  color: #94a3b8;
  margin-left: 10px;
}

.message-content {
  display: inline-block;
  max-width: 80%;
  padding: 18px 24px;
  border-radius: 16px;
  text-align: left;
  word-break: break-word;
  font-size: 15px;
  line-height: 1.7;
}

.message.user .message-content {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: white;
  border-radius: 16px 16px 6px 16px;
}

.message.assistant .message-content {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 16px 16px 16px 6px;
}

.output, .error {
  margin-top: 16px;
  padding: 18px;
  border-radius: 12px;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 14px;
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
  margin-top: 16px;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.image-item {
  position: relative;
  display: inline-block;
}

.image-item img {
  max-width: 100%;
  max-height: 420px;
  border-radius: 12px;
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

:deep(.code-block-container) {
  background: #0f172a;
  border-radius: 12px;
  overflow: hidden;
  margin: 16px 0;
  border: 2px solid #3b82f6;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15), 0 0 0 1px rgba(59, 130, 246, 0.1);
  max-width: 100%;
}

:deep(.code-block-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: linear-gradient(135deg, #1e3a5f, #1e293b);
  border-bottom: 1px solid #334155;
}

:deep(.code-lang) {
  font-size: 13px;
  color: #60a5fa;
  font-weight: 600;
  font-family: 'Fira Code', 'Consolas', monospace;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

:deep(.code-block-container pre) {
  background: #0f172a !important;
  color: #e2e8f0 !important;
  padding: 20px !important;
  margin: 0 !important;
  overflow-x: auto;
  font-family: 'Fira Code', 'Source Code Pro', 'Consolas', monospace !important;
  font-size: 14px !important;
  line-height: 1.8 !important;
  tab-size: 4;
  border: none !important;
  border-radius: 0 !important;
}

:deep(.code-block-container pre code) {
  background: none !important;
  color: #e2e8f0 !important;
  padding: 0 !important;
  font-size: 14px !important;
  line-height: 1.8 !important;
  font-family: 'Fira Code', 'Source Code Pro', 'Consolas', monospace !important;
}

:deep(.code-block-container .hljs-keyword) { color: #c678dd; font-weight: 600; }
:deep(.code-block-container .hljs-string) { color: #98c379; }
:deep(.code-block-container .hljs-comment) { color: #6a9955; font-style: italic; }
:deep(.code-block-container .hljs-number) { color: #d19a66; }
:deep(.code-block-container .hljs-function .hljs-title) { color: #61afef; }
:deep(.code-block-container .hljs-title.function_) { color: #61afef; }
:deep(.code-block-container .hljs-params) { color: #e5c07b; }
:deep(.code-block-container .hljs-variable) { color: #e06c75; }
:deep(.code-block-container .hljs-built_in) { color: #e6c07b; }
:deep(.code-block-container .hljs-name) { color: #61afef; }
:deep(.code-block-container .hljs-punctuation) { color: #d4d4d4; }
:deep(.code-block-container .hljs-operator) { color: #d4d4d4; }

.no-session, .no-student {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

.no-session-icon, .no-student-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.no-session p, .no-student p {
  margin: 0;
  font-size: 16px;
}
</style>