<template>
  <div class="assignment-detail-page">
    <el-page-header @back="goBack" content="返回作业列表" style="margin-bottom: 20px;" />
    
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <h2>{{ assignment?.title }}</h2>
          <div>
            <el-tag>满分: {{ assignment?.total_score }} 分</el-tag>
            <el-tag v-if="assignment?.deadline" :type="isUrgent ? 'danger' : 'success'" style="margin-left: 10px;">
              截止: {{ formatDate(assignment.deadline) }}
            </el-tag>
          </div>
        </div>
      </template>
      
      <div v-if="assignment?.description" style="margin-bottom: 24px;">
        <h4>作业描述：</h4>
        <p style="white-space: pre-wrap;">{{ assignment.description }}</p>
      </div>
      
      <el-divider />
      
      <h4>编写代码：</h4>
      <el-input
        v-model="code"
        type="textarea"
        :rows="15"
        placeholder="在此编写 Python 代码..."
        style="font-family: monospace; margin-bottom: 16px;"
      />
      
      <div style="margin-bottom: 20px;">
        <el-button type="primary" @click="runCode" :loading="running">运行代码</el-button>
        <el-button type="success" @click="submitAssignment" :loading="submitting" :disabled="isExpired">
          {{ isExpired ? '已过截止时间' : '提交作业' }}
        </el-button>
        <el-tag v-if="isExpired" type="danger" style="margin-left: 10px;">
          作业已过截止时间，无法提交
        </el-tag>
      </div>
      
      <div v-if="stdout || stderr || images.length || code">
        <el-divider />
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h4>运行结果：</h4>
          <div>
            <el-button size="small" type="primary" @click="downloadCode">
              <el-icon><Download /></el-icon>
              下载代码
            </el-button>
            <el-button size="small" type="success" @click="downloadImages" :disabled="!images.length" style="margin-left: 10px;">
              <el-icon><Download /></el-icon>
              下载图片 ({{ images.length }})
            </el-button>
          </div>
        </div>
        
        <div v-if="stdout" style="margin-bottom: 12px;">
          <h5 style="color: #16a34a; margin-bottom: 8px;">标准输出：</h5>
          <pre style="background: #f0fdf4; padding: 12px; border-radius: 4px; border: 1px solid #86efac;">{{ stdout }}</pre>
        </div>
        
        <div v-if="stderr" style="margin-bottom: 12px;">
          <h5 style="color: #dc2626; margin-bottom: 8px;">错误输出：</h5>
          <pre style="background: #fef2f2; padding: 12px; border-radius: 4px; border: 1px solid #fca5a5;">{{ stderr }}</pre>
        </div>
        
        <div v-if="images.length" style="margin-bottom: 12px;">
          <h5 style="margin-bottom: 8px;">生成的图片：</h5>
          <div style="display: flex; gap: 12px; flex-wrap: wrap;">
            <img v-for="(img, i) in images" :key="i" :src="img" style="max-width: 400px; border-radius: 8px;" />
          </div>
        </div>
      </div>
      
      <div v-if="submission" style="margin-top: 24px;">
        <el-divider />
        <h4>提交记录：</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="提交时间">
            {{ formatDate(submission.submitted_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="得分">
            <el-tag v-if="submission.score !== null && submission.score !== undefined" :type="submission.score >= 60 ? 'success' : 'danger'">{{ submission.score }} 分</el-tag>
            <el-tag v-else type="warning">待评分</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="教师评语" :span="2">
            <span v-if="submission.feedback" :style="{ color: submission.score >= 60 ? '#67c23a' : '#f56c6c' }">
              {{ submission.feedback }}
            </span>
            <span v-else style="color: #909399">暂无评语</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const assignment = ref(null)
const submission = ref(null)
const code = ref('')
const stdout = ref('')
const stderr = ref('')
const images = ref([])
const loading = ref(false)
const running = ref(false)
const submitting = ref(false)

const assignmentId = computed(() => route.params.id)
const isUrgent = computed(() => assignment.value?.is_deadline_urgent)
const isExpired = computed(() => {
  if (!assignment.value?.deadline) return false
  return new Date() > new Date(assignment.value.deadline)
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}

async function fetchAssignment() {
  loading.value = true
  try {
    const response = await api.get(`/assignments/${assignmentId.value}`)
    assignment.value = response.data
    if (response.data.submission) {
      submission.value = response.data.submission
      code.value = response.data.submission.code || ''
      stdout.value = response.data.submission.stdout || ''
      stderr.value = response.data.submission.stderr || ''
      images.value = response.data.submission.images || []
    }
  } catch (error) {
    ElMessage.error('获取作业详情失败')
  } finally {
    loading.value = false
  }
}

async function runCode() {
  if (!code.value.trim()) {
    ElMessage.warning('请先编写代码')
    return
  }
  running.value = true
  stdout.value = ''
  stderr.value = ''
  images.value = []
  try {
    const response = await api.post('/execute-code', { code: code.value })
    stdout.value = response.data.stdout
    stderr.value = response.data.stderr
    images.value = response.data.images || []
    if (stderr.value) {
      ElMessage.warning('代码执行有错误，请查看输出')
    } else {
      ElMessage.success('代码执行成功')
    }
  } catch (error) {
    ElMessage.error('代码执行失败')
  } finally {
    running.value = false
  }
}

async function submitAssignment() {
  if (!code.value.trim()) {
    ElMessage.warning('请先编写代码')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要提交作业吗？提交后可以再次修改。', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    submitting.value = true
    console.log(`提交作业: /assignments/${assignmentId.value}/submit`)
    console.log('代码内容:', code.value.substring(0, 50) + '...')
    
    // 显示AI评卷加载提示（小弹窗，不覆盖全屏）
    const loadingMessage = ElMessage({
      message: 'AI评卷中，请稍候...',
      type: 'loading',
      duration: 0,  // 手动关闭
      showClose: false
    })
    
    try {
      const response = await api.post(`/assignments/${assignmentId.value}/submit`, { code: code.value })
      
      console.log('提交响应:', response.data)
      stdout.value = response.data.stdout
      stderr.value = response.data.stderr
      images.value = response.data.images || []
      
      // 关闭加载提示
      loadingMessage.close()
      
      // 显示评分结果
      if (response.data.score !== undefined) {
        if (response.data.score === 0) {
          ElMessage.warning('作业已提交，得0分')
        } else if (response.data.score) {
          ElMessage.success(`作业提交成功，得${response.data.score}分`)
        } else {
          ElMessage.info('作业已提交，等待评分')
        }
      } else {
        ElMessage.success('作业提交成功')
      }
      
      fetchAssignment()
    } catch (error) {
      // 关闭加载提示
      loadingMessage.close()
      throw error
    }
  } catch (error) {
    console.error('提交失败:', error)
    console.error('错误详情:', error.response?.data || error.message)
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || error.response?.statusText || '提交失败')
    }
  } finally {
    submitting.value = false
  }
}
function downloadCode() {
  if (!code.value.trim()) {
    ElMessage.warning('没有可下载的代码')
    return
  }
  
  const blob = new Blob([code.value], { type: 'text/x-python;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${assignment.value?.title || '代码'}.py`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('代码下载成功')
}

async function downloadImages() {
  if (!images.value.length) {
    ElMessage.warning('没有可下载的图片')
    return
  }
  
  for (let i = 0; i < images.value.length; i++) {
    const imgUrl = images.value[i]
    const filename = imgUrl.split('/').pop()
    
    try {
      const response = await fetch(imgUrl)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      if (i < images.value.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 300))
      }
    } catch (error) {
      console.error('下载图片失败:', error)
    }
  }
  
  ElMessage.success(`成功下载 ${images.value.length} 张图片`)
}

function goBack() {
  router.push('/student/assignments')
}

onMounted(() => {
  fetchAssignment()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
}

h4 {
  margin: 0 0 12px 0;
}

h5 {
  margin: 0;
}
</style>

