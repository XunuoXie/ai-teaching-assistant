<template>
  <div class="view-submission-page">
    <el-page-header @back="goBack" content="返回提交列表" style="margin-bottom: 20px;" />
    
    <el-card v-loading="loading">
      <div v-if="submission">
        <el-descriptions :column="2" border style="margin-bottom: 20px;">
          <el-descriptions-item label="学生">{{ submission.student?.display_name }}</el-descriptions-item>
          <el-descriptions-item label="作业">{{ submission.assignment?.title }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ submission.submitted_at ? new Date(submission.submitted_at).toLocaleString() : '' }}</el-descriptions-item>
          <el-descriptions-item label="满分">{{ submission.assignment?.total_score }} 分</el-descriptions-item>
        </el-descriptions>
        
        <div style="margin-bottom: 20px;">
          <h4>提交的代码：</h4>
          <el-input
            v-model="submission.code"
            type="textarea"
            :rows="10"
            readonly
            style="font-family: monospace;"
          />
        </div>
        
        <div v-if="submission.stdout" style="margin-bottom: 20px;">
          <h4>标准输出：</h4>
          <pre style="background: #f5f7fa; padding: 12px; border-radius: 4px;">{{ submission.stdout }}</pre>
        </div>
        
        <div v-if="submission.stderr" style="margin-bottom: 20px;">
          <h4>错误输出：</h4>
          <pre style="background: #fef2f2; padding: 12px; border-radius: 4px; color: #dc2626;">{{ submission.stderr }}</pre>
        </div>
        
        <div v-if="submission.images && submission.images.length" style="margin-bottom: 20px;">
          <h4>生成的图片：</h4>
          <div style="display: flex; gap: 12px; flex-wrap: wrap;">
            <img v-for="(img, i) in submission.images" :key="i" :src="img" style="max-width: 300px; border-radius: 8px;" />
          </div>
        </div>
        
        <el-divider />
        
        <h4>评分：</h4>
        <el-form :model="gradeForm" label-width="80px">
          <el-form-item label="得分">
            <el-input-number v-model="gradeForm.score" :min="0" :max="maxScore" />
          </el-form-item>
          <el-form-item label="评语">
            <el-input v-model="gradeForm.feedback" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveGrade" :loading="saving">保存评分</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const submission = ref(null)
const loading = ref(false)
const saving = ref(false)

const gradeForm = ref({
  score: null,
  feedback: ''
})

const maxScore = computed(() => submission.value?.assignment?.total_score || 100)

async function fetchSubmission() {
  loading.value = true
  try {
    const response = await api.get(`/submissions/${route.params.id}`)
    submission.value = response.data
    gradeForm.value.score = response.data.score
    gradeForm.value.feedback = response.data.feedback || ''
  } catch (error) {
    ElMessage.error('获取详情失败')
  } finally {
    loading.value = false
  }
}

async function saveGrade() {
  saving.value = true
  try {
    await api.post(`/submissions/${route.params.id}/grade`, gradeForm.value)
    ElMessage.success('评分保存成功')
    submission.value.score = gradeForm.value.score
    submission.value.feedback = gradeForm.value.feedback
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function goBack() {
  router.push('/teacher/submissions')
}

onMounted(() => {
  fetchSubmission()
})
</script>

<style scoped>
h4 {
  margin: 0 0 12px 0;
}
</style>
