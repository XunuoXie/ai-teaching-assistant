<template>
  <div class="xuetang-page">
    <div class="xuetang-wrapper">
      <div class="brand-section">
        <div class="brand-logo">
          <div class="brand-icon">AI</div>
          <div class="brand-name">智慧教学平台</div>
        </div>
        <h1 class="brand-title">AI驱动的<br>编程学习体验</h1>
        <p class="brand-description">结合人工智能技术，让编程学习更高效、更有趣。</p>
      </div>

      <div class="xuetang-card">
        <!-- Loading -->
        <div v-if="state === 'loading'" class="status-container">
          <el-icon class="status-icon" :size="48" color="#2563eb"><Loading /></el-icon>
          <p class="status-text">验证身份中...</p>
        </div>

        <!-- Already registered: auto-login -->
        <div v-else-if="state === 'redirecting'" class="status-container">
          <el-icon class="status-icon" :size="48" color="#22c55e"><CircleCheck /></el-icon>
          <p class="status-text">已识别身份，正在进入...</p>
        </div>

        <!-- No xuetang params -->
        <div v-else-if="state === 'no_params'" class="status-container">
          <el-icon class="status-icon" :size="48" color="#94a3b8"><Warning /></el-icon>
          <h2 class="status-title">无法访问</h2>
          <p class="status-text">请通过学习通课程页面访问本平台</p>
        </div>

        <!-- Registration form -->
        <div v-else-if="state === 'register'" class="register-form">
          <div class="register-header">
            <h2 class="register-title">欢迎使用智慧教学平台</h2>
            <p class="register-subtitle">首次使用请填写以下信息完成身份登记</p>
          </div>

          <el-form
            ref="formRef"
            :model="form"
            :rules="formRules"
            label-position="top"
            @submit.prevent="handleRegister"
          >
            <el-form-item label="姓名" prop="name">
              <el-input
                v-model="form.name"
                placeholder="请输入你的真实姓名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item :label="isTeacherCpi ? '工号' : '学号'" prop="studentId">
              <el-input
                v-model="form.studentId"
                :placeholder="isTeacherCpi ? '请输入你的工号' : '请输入你的学号'"
                size="large"
                :prefix-icon="Reading"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="submitting"
                style="width: 100%"
                @click="handleRegister"
              >
                完成登记
              </el-button>
            </el-form-item>
          </el-form>

          <p class="register-footer">
            登记后系统会为你创建学习账号，下次可自动登录
          </p>
        </div>

        <!-- Error -->
        <div v-else-if="state === 'error'" class="status-container">
          <el-icon class="status-icon" :size="48" color="#ef4444"><CircleClose /></el-icon>
          <p class="status-text">{{ errorMessage }}</p>
          <el-button type="primary" style="margin-top: 16px" @click="initCheck">重试</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import api from '@/services/api'
import { ElMessage } from 'element-plus'
import { User, Reading, Loading, CircleCheck, CircleClose, Warning } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const submitting = ref(false)

const state = ref('loading')
const errorMessage = ref('')
const isTeacherCpi = ref(false)

const form = reactive({
  name: '',
  studentId: ''
})

const formRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 1, max: 50, message: '姓名长度在 1-50 个字符', trigger: 'blur' }
  ],
  studentId: [
    { required: true, message: '请输入学号', trigger: 'blur' },
    { min: 1, max: 50, message: '学号长度在 1-50 个字符', trigger: 'blur' }
  ]
}

onMounted(() => {
  initCheck()
})

async function initCheck() {
  state.value = 'loading'

  try {
    // Pass URL query params (cpi/courseId/clazzId) for cross-origin support
    const params = {}
    if (route.query.cpi) {
      params.cpi = route.query.cpi
      params.courseId = route.query.courseId || ''
      params.clazzId = route.query.clazzId || ''
    }

    const resp = await api.get('/xuetang/check', { params })
    const data = resp.data

    if (data.registered) {
      state.value = 'redirecting'
      localStorage.setItem('token', data.token)
      userStore.user = data.user
      userStore.token = data.token
      await router.push('/dashboard')
    } else if (data.hasParams) {
      isTeacherCpi.value = data.isTeacherCpi || false
      state.value = 'register'
    } else {
      state.value = 'no_params'
    }
  } catch (e) {
    state.value = 'error'
    errorMessage.value = '验证失败，请重试'
  }
}

async function handleRegister() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const resp = await api.post('/xuetang/register', {
        name: form.name,
        student_id: form.studentId,
        cpi: route.query.cpi || '',
        courseId: route.query.courseId || '',
        clazzId: route.query.clazzId || ''
      })
      const data = resp.data
      if (!data.success) {
        ElMessage.error(data.message || '登记失败')
        return
      }

      localStorage.setItem('token', data.token)
      userStore.user = data.user
      userStore.token = data.token
      ElMessage.success('登记成功，欢迎！')
      await router.push('/dashboard')
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '登记失败，请重试')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.xuetang-page {
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
}

.xuetang-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  max-width: 1000px;
  width: 100%;
  align-items: center;
}

.brand-section {
  animation: fadeInLeft 0.6s ease-out;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.brand-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  font-weight: bold;
}

.brand-name {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.brand-title {
  font-size: 36px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
  margin-bottom: 16px;
}

.brand-description {
  font-size: 16px;
  color: #64748b;
  line-height: 1.6;
}

.xuetang-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  animation: fadeInRight 0.6s ease-out;
}

.status-container {
  text-align: center;
  padding: 32px 0;
}

.status-icon {
  margin-bottom: 16px;
}

.status-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
}

.status-text {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.register-header {
  margin-bottom: 32px;
}

.register-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
}

.register-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.register-footer {
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 16px;
}

@keyframes fadeInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@media (max-width: 768px) {
  .xuetang-wrapper {
    grid-template-columns: 1fr;
    gap: 32px;
  }

  .brand-section {
    text-align: center;
  }

  .brand-logo {
    justify-content: center;
  }

  .brand-title {
    font-size: 28px;
  }
}
</style>
