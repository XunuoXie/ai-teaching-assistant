<template>
  <div class="profile-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>个人资料</span>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">{{ userStore.user?.username }}</el-descriptions-item>
        <el-descriptions-item label="显示名称">{{ userStore.user?.display_name }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag>{{ userStore.user?.role === 'admin' ? '管理员' : userStore.user?.role === 'teacher' ? '教师' : '学生' }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
      
      <div style="margin-top: 24px;">
        <el-button type="primary" @click="userStore.logout(); router.push('/login')">退出登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
</script>

<style scoped>
.profile-page {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  font-weight: 600;
}
</style>
