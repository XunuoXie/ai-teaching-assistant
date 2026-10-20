<template>
  <div class="student-assignments-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的作业</span>
        </div>
      </template>
      
      <el-table :data="assignments" style="width: 100%" v-loading="loading">
        <el-table-column prop="title" label="作业标题" width="250" />
        <el-table-column prop="class_name" label="所属班级" width="150">
          <template #default="scope">
            {{ scope.row.class_name || '所有班级' }}
          </template>
        </el-table-column>
        <el-table-column prop="total_score" label="满分" width="100" />
        <el-table-column label="截止时间" width="200">
          <template #default="scope">
            <el-tag :type="scope.row.is_deadline_urgent ? 'danger' : 'success'">
              {{ scope.row.deadline ? new Date(scope.row.deadline).toLocaleString() : '无' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="150">
          <template #default="scope">
            <el-tag :type="getSubmissionStatus(scope.row).type">
              {{ getSubmissionStatus(scope.row).text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button 
              size="small" 
              type="primary" 
              @click="viewAssignment(scope.row.id)"
              :disabled="getSubmissionStatus(scope.row).expired && !getSubmissionStatus(scope.row).submitted"
            >
              {{ getSubmissionStatus(scope.row).submitted ? '查看/修改' : (getSubmissionStatus(scope.row).expired ? '已过期' : '开始答题') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const assignments = ref([])
const loading = ref(false)

async function fetchAssignments() {
  loading.value = true
  try {
    const response = await api.get('/assignments')
    assignments.value = response.data
  } catch (error) {
    ElMessage.error('获取作业列表失败')
  } finally {
    loading.value = false
  }
}

function getSubmissionStatus(assignment) {
  const isExpired = assignment.deadline && new Date() > new Date(assignment.deadline)
  
  if (isExpired && !assignment.submitted_at) {
    return { text: '已过期', type: 'danger', submitted: false, expired: true }
  }
  if (assignment.submitted_at) {
    const hasScore = assignment.score !== null && assignment.score !== undefined
    return { text: hasScore ? `已评分: ${assignment.score} 分` : '已提交, 待评分', type: hasScore ? (assignment.score > 0 ? 'success' : 'danger') : 'warning', submitted: true, expired: false }
  }
  return { text: '未提交', type: 'info', submitted: false, expired: false }
}

function viewAssignment(id) {
  router.push(`/student/assignment/${id}`)
}

onMounted(() => {
  fetchAssignments()
})

onActivated(() => {
  fetchAssignments()
})
</script>

<style scoped>
.card-header {
  font-weight: 600;
}
</style>
