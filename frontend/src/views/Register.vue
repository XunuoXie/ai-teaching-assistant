<template>
  <div class="register-page">
    <div class="register-wrapper">
      <div class="brand-section">
        <div class="brand-logo">
          <div class="brand-icon">AI</div>
          <div class="brand-name">智慧教学平台</div>
        </div>
        <h1 class="brand-title">开始你的<br>编程学习之旅</h1>
        <p class="brand-description">加入我们的社区，享受AI驱动的学习体验。</p>
      </div>
      
      <div class="register-card">
        <div class="register-header">
          <h2 class="register-title">创建账号</h2>
          <p class="register-subtitle">填写以下信息完成注册</p>
        </div>
        
        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleRegister">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名（用于登录）"
              size="large"
              prefix-icon="User"
            />
          </el-form-item>
          
          <el-form-item prop="display_name">
            <el-input
              v-model="form.display_name"
              placeholder="姓名/昵称（用于显示）"
              size="large"
              prefix-icon="Avatar"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              size="large"
              prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          
          <el-form-item prop="role">
            <el-radio-group v-model="form.role" size="large">
              <el-radio-button value="student">学生</el-radio-button>
              <el-radio-button value="teacher">教师</el-radio-button>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              style="width: 100%"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="divider">
          <div class="divider-line"></div>
          <div class="divider-text">已有账号？</div>
          <div class="divider-line"></div>
        </div>
        
        <p class="footer-text">
          <router-link to="/login" class="link">立即登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  display_name: '',
  password: '',
  role: 'student'
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  display_name: [{ required: true, message: '请输入姓名/昵称', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

async function handleRegister() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.register(form)
        ElMessage.success('注册成功，请登录')
        router.push('/login')
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '注册失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
}

.register-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  max-width: 1000px;
  width: 100%;
  align-items: flex-start;
}

.brand-section {
  animation: fadeInLeft 0.6s ease-out;
  position: sticky;
  top: 24px;
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

.register-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  animation: fadeInRight 0.6s ease-out;
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

.divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 24px 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: #e2e8f0;
}

.divider-text {
  font-size: 14px;
  color: #64748b;
}

.footer-text {
  text-align: center;
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.link:hover {
  color: #1d4ed8;
  text-decoration: underline;
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
  .register-wrapper {
    grid-template-columns: 1fr;
    gap: 32px;
  }

  .brand-section {
    text-align: center;
    position: static;
  }

  .brand-logo {
    justify-content: center;
  }

  .brand-title {
    font-size: 28px;
  }
}
</style>
