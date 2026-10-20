<template>
  <div class="dashboard">
    <el-row :gutter="24" class="stats-grid">
      <el-col :xs="24" :sm="12" :md="6" v-for="stat in stats" :key="stat.title">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color + '20', color: stat.color }">
              <el-icon :size="28">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24" class="actions-grid" v-if="userStore.isTeacher">
      <el-col :xs="24" :md="8">
        <el-card class="action-card" shadow="hover" @click="$router.push('/teacher/assignments')">
          <div class="action-icon" style="background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)">
            <el-icon :size="32"><DocumentAdd /></el-icon>
          </div>
          <h3>创建作业</h3>
          <p>发布新的编程作业给学生</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card class="action-card" shadow="hover" @click="$router.push('/teacher/submissions')">
          <div class="action-icon" style="background: linear-gradient(135deg, #16a34a 0%, #10b981 100%)">
            <el-icon :size="32"><List /></el-icon>
          </div>
          <h3>查看提交</h3>
          <p>查看和批改学生作业</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card class="action-card" shadow="hover" @click="$router.push('/teacher/classes')">
          <div class="action-icon" style="background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%)">
            <el-icon :size="32"><School /></el-icon>
          </div>
          <h3>管理班级</h3>
          <p>管理教学班级和学生</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24" class="actions-grid" v-else>
      <el-col :xs="24" :md="8">
        <el-card class="action-card" shadow="hover" @click="$router.push('/student/assignments')">
          <div class="action-icon" style="background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)">
            <el-icon :size="32"><Document /></el-icon>
          </div>
          <h3>我的作业</h3>
          <p>查看和完成编程任务</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card class="action-card" shadow="hover" @click="$router.push('/chat')">
          <div class="action-icon" style="background: linear-gradient(135deg, #16a34a 0%, #10b981 100%)">
            <el-icon :size="32"><ChatDotRound /></el-icon>
          </div>
          <h3>AI 辅导</h3>
          <p>让 AI 帮助你解决问题</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/services/api'
import { Document, User, Clock, Check, DocumentAdd, List, School, ChatDotRound } from '@element-plus/icons-vue'

const userStore = useUserStore()

const statsData = ref({
  totalAssignments: 0,
  totalStudents: 0,
  unscoredSubmissions: 0,
  scoredSubmissions: 0,
  totalSubmissions: 0
})

const stats = computed(() => {
  if (userStore.isTeacher) {
    return [
      { title: '作业数量', value: statsData.value.totalAssignments, icon: Document, color: '#2563eb' },
      { title: '学生人数', value: statsData.value.totalStudents, icon: User, color: '#16a34a' },
      { title: '已完成批改', value: statsData.value.scoredSubmissions, icon: Check, color: '#7c3aed' }
    ]
  } else {
    return [
      { title: '总作业数', value: statsData.value.totalAssignments, icon: Document, color: '#2563eb' },
      { title: '已提交', value: statsData.value.totalSubmissions, icon: Check, color: '#16a34a' },
      { title: '未完成', value: statsData.value.totalAssignments - statsData.value.totalSubmissions, icon: Clock, color: '#d97706' }
    ]
  }
})

async function fetchStats() {
  try {
    const response = await api.get('/dashboard/stats')
    statsData.value = response.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-grid {
  margin-bottom: 32px;
}

.stat-card {
  border: none;
  border-radius: 12px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.actions-grid {
  margin-top: 24px;
}

.action-card {
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s ease;
  text-align: center;
  padding: 32px 24px;
}

.action-card:hover {
  transform: translateY(-4px);
}

.action-icon {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 16px;
}

.action-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.action-card p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}
</style>
