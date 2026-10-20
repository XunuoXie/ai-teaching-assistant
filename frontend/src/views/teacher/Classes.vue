<template>
  <div class="classes-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>班级管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            + 创建班级
          </el-button>
        </div>
      </template>
      
      <el-table :data="classes" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="班级名称" width="200" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="student_count" label="学生人数" width="120" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="manageStudents(scope.row)">管理学生</el-button>
            <el-button size="small" type="primary" @click="editClass(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteClass(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="showCreateDialog" title="创建班级" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="班级名称">
          <el-input v-model="form.name" placeholder="请输入班级名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="请输入班级描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createClass" :loading="saving">创建</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showEditDialog" title="编辑班级" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="班级名称">
          <el-input v-model="form.name" placeholder="请输入班级名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="请输入班级描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateClass" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showStudentsDialog" :title="`管理 ${currentClass?.name} 的学生`" width="800px">
      <div v-if="currentClass">
        <h4>已添加的学生</h4>
        <el-table :data="classStudents" style="width: 100%; margin-bottom: 20px;">
          <el-table-column prop="display_name" label="学生姓名" />
          <el-table-column prop="username" label="学号" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button size="small" type="danger" @click="removeStudent(scope.row.id)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <h4>可添加的学生</h4>
        <el-table :data="availableStudents" style="width: 100%;">
          <el-table-column prop="display_name" label="学生姓名" />
          <el-table-column prop="username" label="学号" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button size="small" type="primary" @click="addStudent(scope.row.id)">添加</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showStudentsDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const classes = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showStudentsDialog = ref(false)
const currentClass = ref(null)
const classStudents = ref([])
const availableStudents = ref([])

const form = ref({
  id: null,
  name: '',
  description: ''
})

async function fetchClasses() {
  loading.value = true
  try {
    const response = await api.get('/classes')
    classes.value = response.data
  } catch (error) {
    ElMessage.error('获取班级列表失败')
  } finally {
    loading.value = false
  }
}

async function createClass() {
  if (!form.value.name) {
    ElMessage.warning('请输入班级名称')
    return
  }
  saving.value = true
  try {
    await api.post('/classes', form.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    form.value = { id: null, name: '', description: '' }
    fetchClasses()
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    saving.value = false
  }
}

function editClass(cls) {
  form.value = { ...cls }
  showEditDialog.value = true
}

async function updateClass() {
  saving.value = true
  try {
    await api.put(`/classes/${form.value.id}`, form.value)
    ElMessage.success('更新成功')
    showEditDialog.value = false
    fetchClasses()
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    saving.value = false
  }
}

async function deleteClass(cls) {
  try {
    await ElMessageBox.confirm(`确定要删除班级 ${cls.name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/classes/${cls.id}`)
    ElMessage.success('删除成功')
    fetchClasses()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function manageStudents(cls) {
  currentClass.value = cls
  showStudentsDialog.value = true
  try {
    const response = await api.get(`/classes/${cls.id}/students`)
    classStudents.value = response.data.class_students
    availableStudents.value = response.data.available_students
  } catch (error) {
    ElMessage.error('获取学生列表失败')
  }
}

async function addStudent(studentId) {
  try {
    await api.post(`/classes/${currentClass.value.id}/students`, { student_id: studentId })
    ElMessage.success('添加成功')
    manageStudents(currentClass.value)
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '添加失败')
  }
}

async function removeStudent(studentId) {
  try {
    await api.delete(`/classes/${currentClass.value.id}/students/${studentId}`)
    ElMessage.success('移除成功')
    manageStudents(currentClass.value)
  } catch (error) {
    ElMessage.error('移除失败')
  }
}

onMounted(() => {
  fetchClasses()
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
</style>
