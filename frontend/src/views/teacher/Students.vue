<template>
  <div class="students-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学生管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            + 添加学生
          </el-button>
        </div>
      </template>
      
      <el-table :data="students" style="width: 100%" v-loading="loading">
        <el-table-column prop="username" label="学号" width="150" />
        <el-table-column prop="display_name" label="姓名" width="150" />
        <el-table-column label="所属班级">
          <template #default="scope">
            <el-tag v-for="cls in scope.row.classes" :key="cls.id" style="margin-right: 8px; margin-bottom: 4px;">
              {{ cls.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="viewStudentDetail(scope.row)">查看详情</el-button>
            <el-button size="small" type="danger" @click="deleteStudent(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 添加学生对话框 -->
    <el-dialog v-model="showCreateDialog" title="添加学生" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="学号">
          <el-input v-model="form.username" placeholder="请输入学号" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.display_name" placeholder="请输入学生姓名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请设置密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createStudent" :loading="saving">添加</el-button>
      </template>
    </el-dialog>
    
    <!-- 学生详情对话框 -->
    <el-dialog v-model="showDetailDialog" :title="`${currentStudent?.display_name} 的详情`" width="800px">
      <div v-if="studentDetail" class="student-detail">
        <el-descriptions :column="2" border style="margin-bottom: 20px;">
          <el-descriptions-item label="学号">{{ studentDetail.username }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ studentDetail.display_name }}</el-descriptions-item>
          <el-descriptions-item label="所属班级" :span="2">
            <el-tag v-for="cls in studentDetail.classes" :key="cls.id" style="margin-right: 8px;">
              {{ cls.name }}
            </el-tag>
            <span v-if="!studentDetail.classes || studentDetail.classes.length === 0">暂无班级</span>
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider />
        
        <h4>作业完成情况</h4>
        <el-table :data="studentDetail.assignments" style="width: 100%; margin-top: 15px;">
          <el-table-column prop="title" label="作业名称" width="200" />
          <el-table-column label="提交状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.submitted ? 'success' : 'info'">
                {{ scope.row.submitted ? '已提交' : '未提交' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="成绩" width="100">
            <template #default="scope">
              <span v-if="scope.row.score !== null">
                {{ scope.row.score }} / {{ scope.row.total_score }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="submitted_at" label="提交时间" width="180">
            <template #default="scope">
              {{ scope.row.submitted_at ? new Date(scope.row.submitted_at).toLocaleString() : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="feedback" label="教师评语" show-overflow-tooltip />
        </el-table>
        
        <el-divider />
        
        <h4>管理班级</h4>
        <div class="class-management">
          <div style="margin-bottom: 15px;">
            <h5>已加入的班级：</h5>
            <el-tag
              v-for="cls in studentDetail.classes"
              :key="cls.id"
              closable
              @close="removeClass(cls.id)"
              style="margin-right: 8px; margin-bottom: 8px;"
            >
              {{ cls.name }}
            </el-tag>
            <span v-if="!studentDetail.classes || studentDetail.classes.length === 0">暂无班级</span>
          </div>
          
          <div>
            <h5>可加入的班级：</h5>
            <el-tag
              v-for="cls in availableClasses"
              :key="cls.id"
              @click="addClass(cls.id)"
              style="margin-right: 8px; margin-bottom: 8px; cursor: pointer;"
            >
              {{ cls.name }} +
            </el-tag>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const students = ref([])
const classes = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const currentStudent = ref(null)
const studentDetail = ref(null)

const form = ref({
  username: '',
  display_name: '',
  password: ''
})

const availableClasses = computed(() => {
  if (!studentDetail.value) return []
  const joinedIds = new Set(studentDetail.value.classes.map(c => c.id))
  return classes.value.filter(c => !joinedIds.has(c.id))
})

async function fetchData() {
  loading.value = true
  try {
    const [studentsRes, classesRes] = await Promise.all([
      api.get('/students'),
      api.get('/classes')
    ])
    students.value = studentsRes.data
    classes.value = classesRes.data
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

async function createStudent() {
  if (!form.value.username || !form.value.display_name || !form.value.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  saving.value = true
  try {
    await api.post('/students', form.value)
    ElMessage.success('添加成功')
    showCreateDialog.value = false
    form.value = { username: '', display_name: '', password: '' }
    fetchData()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '添加失败')
  } finally {
    saving.value = false
  }
}

async function viewStudentDetail(student) {
  currentStudent.value = student
  try {
    const response = await api.get(`/students/${student.id}`)
    studentDetail.value = response.data
    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error('获取学生详情失败')
  }
}

async function addClass(classId) {
  try {
    await api.post(`/students/${currentStudent.value.id}/add-class`, { class_id: classId })
    ElMessage.success('添加成功')
    // 刷新详情
    await viewStudentDetail(currentStudent.value)
    fetchData()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '添加失败')
  }
}

async function removeClass(classId) {
  try {
    await api.post(`/students/${currentStudent.value.id}/remove-class`, { class_id: classId })
    ElMessage.success('移除成功')
    // 刷新详情
    await viewStudentDetail(currentStudent.value)
    fetchData()
  } catch (error) {
    ElMessage.error('移除失败')
  }
}

async function deleteStudent(student) {
  try {
    await ElMessageBox.confirm(`确定要删除学生 ${student.display_name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/students/${student.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

h4 {
  margin: 0 0 12px 0;
}

h5 {
  margin: 0 0 8px 0;
  color: #606266;
}

.class-management {
  padding: 10px 0;
}
</style>
