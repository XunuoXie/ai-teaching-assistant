<template>
  <el-container class="main-layout">
    <el-aside width="240px" class="sidebar">
      <div class="logo">
        <div class="logo-icon">AI</div>
        <div class="logo-text">智慧教学平台</div>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        background-color="#ffffff"
        text-color="#64748b"
        active-text-color="#2563eb"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <span>控制台</span>
        </el-menu-item>

        <template v-if="userStore.isAdmin">
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
        </template>

        <template v-if="userStore.isTeacher">
          <el-menu-item index="/teacher/classes">
            <el-icon><School /></el-icon>
            <span>班级管理</span>
          </el-menu-item>
          <el-menu-item index="/teacher/assignments">
            <el-icon><Document /></el-icon>
            <span>作业管理</span>
          </el-menu-item>
          <el-menu-item index="/teacher/students">
            <el-icon><User /></el-icon>
            <span>学生管理</span>
          </el-menu-item>
          <el-menu-item index="/teacher/submissions">
            <el-icon><List /></el-icon>
            <span>提交管理</span>
          </el-menu-item>
          <el-menu-item index="/teacher/chat-history">
            <el-icon><ChatDotRound /></el-icon>
            <span>聊天记录</span>
          </el-menu-item>
        </template>
        
        <template v-else>
          <el-menu-item index="/student/assignments">
            <el-icon><Document /></el-icon>
            <span>我的作业</span>
          </el-menu-item>
        </template>
        
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 辅导</span>
        </el-menu-item>
        
        <el-menu-divider />
        <el-menu-item index="/profile">
          <el-icon><UserFilled /></el-icon>
          <span>个人资料</span>
        </el-menu-item>
        <el-menu-item @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container class="content-container">
      <el-header class="header">
        <div class="welcome">
          <h1>{{ pageTitle }}</h1>
          <p>{{ pageSubtitle }}</p>
        </div>
        <div class="user-info">
          <el-avatar :size="40" :style="{ backgroundColor: '#2563eb' }">
            {{ userStore.user?.display_name?.[0] || 'U' }}
          </el-avatar>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  Monitor,
  School,
  Document,
  User,
  List,
  ChatDotRound,
  UserFilled,
  SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => {
  const titles = {
    '/dashboard': '欢迎回来',
    '/chat': 'AI 辅导',
    '/profile': '个人资料',
    '/admin/users': '用户管理',
    '/teacher/classes': '班级管理',
    '/teacher/assignments': '作业管理',
    '/teacher/students': '学生管理',
    '/teacher/submissions': '提交管理',
    '/teacher/chat-history': '聊天记录',
    '/student/assignments': '我的作业'
  }
  return titles[route.path] || '智慧教学平台'
})

const pageSubtitle = computed(() => {
  const subtitles = {
    '/dashboard': '这是你的教学管理控制台',
    '/chat': '让 AI 帮助你解决编程问题',
    '/profile': '管理你的个人信息',
    '/admin/users': '管理系统中的所有用户账户',
    '/teacher/classes': '管理教学班级和学生结构',
    '/teacher/assignments': '发布和管理编程作业',
    '/teacher/students': '管理学生信息',
    '/teacher/submissions': '查看和批改学生作业',
    '/teacher/chat-history': '查看学生与 AI 的聊天记录',
    '/student/assignments': '在这里查看和完成你的编程任务'
  }
  return subtitles[route.path] || ''
})

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
  font-weight: bold;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.sidebar-menu {
  flex: 1;
  border: none;
}

.content-container {
  background: #f8fafc;
}

.header {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  height: 70px;
}

.welcome h1 {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.welcome p {
  font-size: 14px;
  color: #64748b;
  margin: 4px 0 0 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-content {
  padding: 24px 32px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
