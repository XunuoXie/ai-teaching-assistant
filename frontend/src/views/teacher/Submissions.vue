<template>
  <div class="submissions-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>提交管理</span>
        </div>
      </template>
      
      <el-form :inline="true" :model="filters" style="margin-bottom: 20px;">
        <el-form-item label="作业">
          <el-select v-model="filters.assignment_id" placeholder="选择作业" @change="fetchSubmissions">
            <el-option :value="0" label="全部作业" />
            <el-option v-for="a in assignments" :key="a.id" :label="a.title" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="filters.class_id" placeholder="选择班级" @change="fetchSubmissions">
            <el-option :value="0" label="全部班级" />
            <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <el-table :data="submissions" style="width: 100%" v-loading="loading">
        <el-table-column prop="assignment_title" label="作业" width="200" />
        <el-table-column prop="student_name" label="学生" width="150" />
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.score !== null && scope.row.score !== undefined ? (scope.row.score > 0 ? 'success' : 'danger') : 'warning'">
              {{ scope.row.score !== null && scope.row.score !== undefined ? '已评分' : '待评分' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="得分" width="100">
          <template #default="scope">
            <span v-if="scope.row.score !== null && scope.row.score !== undefined" :style="{ color: scope.row.score >= 60 ? '#16a34a' : '#dc2626', fontWeight: 'bold' }">
              {{ scope.row.score }} 分
            </span>
            <span v-else style="color: #9ca3af;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="submitted_at" label="提交时间" width="180">
          <template #default="scope">
            {{ scope.row.submitted_at ? new Date(scope.row.submitted_at).toLocaleString() : '' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="viewSubmission(scope.row.id)">查看/评分</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="showViewDialog" title="作业详情" width="80%" top="5vh">
      <div v-if="currentSubmission">
        <el-descriptions :column="2" border style="margin-bottom: 20px;">
          <el-descriptions-item label="学生">{{ currentSubmission.student?.display_name }}</el-descriptions-item>
          <el-descriptions-item label="作业">{{ currentSubmission.assignment?.title }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ currentSubmission.submitted_at ? new Date(currentSubmission.submitted_at).toLocaleString() : '' }}</el-descriptions-item>
          <el-descriptions-item label="满分">{{ currentSubmission.assignment?.total_score }} 分</el-descriptions-item>
        </el-descriptions>
        
        <div style="margin-bottom: 20px;">
          <h4>学生提交的代码：</h4>
          <el-input
            v-model="currentSubmission.code"
            type="textarea"
            :rows="10"
            style="font-family: monospace;"
            placeholder="请输入代码..."
          />
          <div style="margin-top: 10px;">
            <el-button type="primary" @click="runCode" :loading="running">运行代码</el-button>
            <el-button type="primary" @click="downloadCode" style="margin-left: 10px;">
              <el-icon><Download /></el-icon>
              下载代码
            </el-button>
            <el-button type="success" @click="downloadSubmittedImages" style="margin-left: 10px;">
              <el-icon><Download /></el-icon>
              下载提交图片 ({{ currentSubmission?.images?.length || 0 }})
            </el-button>
            <el-button type="warning" @click="downloadRunImages" :disabled="!runResult?.images?.length" style="margin-left: 10px;">
              <el-icon><Download /></el-icon>
              下载运行图片 ({{ runResult?.images?.length || 0 }})
            </el-button>
          </div>
        </div>
        
        <div v-if="runResult" style="margin-bottom: 20px;">
          <h4>运行结果：</h4>
          <div v-if="runResult.stdout" style="margin-bottom: 12px;">
            <div style="color: #16a34a; margin-bottom: 8px;">标准输出：</div>
            <pre style="background: #f0fdf4; padding: 12px; border-radius: 4px; border: 1px solid #86efac;">{{ runResult.stdout }}</pre>
          </div>
          <div v-if="runResult.stderr" style="margin-bottom: 12px;">
            <div style="color: #dc2626; margin-bottom: 8px;">错误输出：</div>
            <pre style="background: #fef2f2; padding: 12px; border-radius: 4px; border: 1px solid #fca5a5;">{{ runResult.stderr }}</pre>
          </div>
          <div v-if="runResult.images && runResult.images.length" style="margin-bottom: 12px;">
            <div style="margin-bottom: 8px;">生成的图片：</div>
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
              <img v-for="(img, i) in runResult.images" :key="i" :src="img" style="max-width: 300px; border-radius: 8px;" />
            </div>
          </div>
        </div>
        
        <div v-if="currentSubmission.stdout" style="margin-bottom: 20px;">
          <h4>标准输出：</h4>
          <pre style="background: #f5f7fa; padding: 12px; border-radius: 4px;">{{ currentSubmission.stdout }}</pre>
        </div>
        
        <div v-if="currentSubmission.stderr" style="margin-bottom: 20px;">
          <h4>错误输出：</h4>
          <pre style="background: #fef2f2; padding: 12px; border-radius: 4px; color: #dc2626;">{{ currentSubmission.stderr }}</pre>
        </div>
        
        <div v-if="currentSubmission.images && currentSubmission.images.length" style="margin-bottom: 20px;">
          <h4>提交时的图片：</h4>
          <div style="display: flex; gap: 12px; flex-wrap: wrap;">
            <img v-for="(img, i) in currentSubmission.images" :key="i" :src="img" style="max-width: 300px; border-radius: 8px;" />
          </div>
        </div>
        
        <el-divider />
        
        <h4>评分：</h4>
        <el-form :model="gradeForm" label-width="80px">
          <el-form-item label="得分">
            <el-input-number v-model="gradeForm.score" :min="0" :max="currentSubmission.assignment?.total_score || 100" />
          </el-form-item>
          <el-form-item label="评语">
            <el-input v-model="gradeForm.feedback" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveGrade" :loading="saving">保存评分</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

const submissions = ref([])
const assignments = ref([])
const classes = ref([])
const loading = ref(false)
const saving = ref(false)
const running = ref(false)
const showViewDialog = ref(false)
const currentSubmission = ref(null)
const runResult = ref(null)

const filters = ref({
  assignment_id: 0,
  class_id: 0
})

const gradeForm = ref({
  score: null,
  feedback: ''
})

async function fetchData() {
  loading.value = true
  try {
    const [submissionsRes, assignmentsRes, classesRes] = await Promise.all([
      api.get('/submissions', { params: filters.value }),
      api.get('/assignments'),
      api.get('/classes')
    ])
    submissions.value = submissionsRes.data
    assignments.value = assignmentsRes.data
    classes.value = classesRes.data
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

async function fetchSubmissions() {
  loading.value = true
  try {
    const response = await api.get('/submissions', { params: filters.value })
    submissions.value = response.data
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

async function viewSubmission(id) {
  try {
    const response = await api.get(`/submissions/${id}`)
    currentSubmission.value = response.data
    gradeForm.value.score = response.data.score
    gradeForm.value.feedback = response.data.feedback || ''
    runResult.value = null
    showViewDialog.value = true
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}

async function runCode() {
  if (!currentSubmission.value?.code) {
    ElMessage.warning('没有可运行的代码')
    return
  }
  
  running.value = true
  runResult.value = null
  try {
    const response = await api.post('/execute-code', { code: currentSubmission.value.code })
    runResult.value = response.data
    if (response.data.stderr) {
      ElMessage.warning('代码执行有错误，请查看输出')
    } else {
      ElMessage.success('代码执行成功')
    }
  } catch (error) {
    ElMessage.error('运行失败：' + (error.response?.data?.message || error.message))
  } finally {
    running.value = false
  }
}

function downloadCode() {
  if (!currentSubmission.value?.code.trim()) {
    ElMessage.warning('没有可下载的代码')
    return
  }
  
  const blob = new Blob([currentSubmission.value.code], { type: 'text/x-python;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${currentSubmission.value.student_name}_${currentSubmission.value.assignment_title}.py`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('代码下载成功')
}

async function downloadSubmittedImages() {
  if (!currentSubmission.value?.images?.length) {
    ElMessage.warning('没有可下载的提交图片')
    return
  }
  
  for (let i = 0; i < currentSubmission.value.images.length; i++) {
    const imgUrl = currentSubmission.value.images[i]
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
      
      if (i < currentSubmission.value.images.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 300))
      }
    } catch (error) {
      console.error('下载图片失败:', error)
    }
  }
  
  ElMessage.success(`成功下载 ${currentSubmission.value.images.length} 张提交图片`)
}

async function downloadRunImages() {
  if (!runResult.value?.images?.length) {
    ElMessage.warning('没有可下载的运行图片')
    return
  }
  
  for (let i = 0; i < runResult.value.images.length; i++) {
    const imgUrl = runResult.value.images[i]
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
      
      if (i < runResult.value.images.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 300))
      }
    } catch (error) {
      console.error('下载图片失败:', error)
    }
  }
  
  ElMessage.success(`成功下载 ${runResult.value.images.length} 张运行图片`)
}

async function saveGrade() {
  saving.value = true
  try {
    await api.post(`/submissions/${currentSubmission.value.id}/grade`, gradeForm.value)
    ElMessage.success('评分保存成功')
    currentSubmission.value.score = gradeForm.value.score
    currentSubmission.value.feedback = gradeForm.value.feedback
    fetchSubmissions()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.card-header {
  font-weight: 600;
}

h4 {
  margin: 0 0 12px 0;
}

.btn-disabled {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
}
</style>
