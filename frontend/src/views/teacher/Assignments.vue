<template>
  <div class="assignments-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>作业管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            + 创建作业
          </el-button>
        </div>
      </template>
      
      <el-table :data="assignments" style="width: 100%" v-loading="loading">
        <el-table-column prop="title" label="作业标题" width="200" />
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
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ scope.row.created_at ? new Date(scope.row.created_at).toLocaleString() : '' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="editAssignment(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteAssignment(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="showCreateDialog" title="创建作业" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="作业标题">
          <el-input v-model="form.title" placeholder="请输入作业标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="请输入作业描述" />
        </el-form-item>
        <el-form-item label="所属班级">
          <el-select v-model="form.class_id" placeholder="选择班级" clearable style="width: 100%;">
            <el-option label="所有班级" :value="null" />
            <el-option v-for="cls in classes" :key="cls.id" :label="cls.name" :value="cls.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止时间">
          <el-date-picker
            v-model="form.deadline"
            type="datetime"
            placeholder="选择截止时间"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="满分">
          <el-input-number v-model="form.total_score" :min="1" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createAssignment" :loading="saving">创建</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showEditDialog" title="编辑作业" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="作业标题">
          <el-input v-model="form.title" placeholder="请输入作业标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="请输入作业描述" />
        </el-form-item>
        <el-form-item label="所属班级">
          <el-select v-model="form.class_id" placeholder="选择班级" clearable style="width: 100%;">
            <el-option label="所有班级" :value="null" />
            <el-option v-for="cls in classes" :key="cls.id" :label="cls.name" :value="cls.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止时间">
          <el-date-picker
            v-model="form.deadline"
            type="datetime"
            placeholder="选择截止时间"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="满分">
          <el-input-number v-model="form.total_score" :min="1" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateAssignment" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const assignments = ref([])
const classes = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)

const form = ref({
  id: null,
  title: '',
  description: '',
  class_id: null,
  deadline: null,
  total_score: 100
})

async function fetchData() {
  loading.value = true
  try {
    const [assignmentsRes, classesRes] = await Promise.all([
      api.get('/assignments'),
      api.get('/classes')
    ])
    assignments.value = assignmentsRes.data
    classes.value = classesRes.data
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

async function createAssignment() {
  if (!form.value.title) {
    ElMessage.warning('请输入作业标题')
    return
  }
  saving.value = true
  try {
    const data = { ...form.value }
    if (data.deadline) {
      const date = new Date(data.deadline)
      data.deadline = new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString()
    }
    await api.post('/assignments', data)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    resetForm()
    fetchData()
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    saving.value = false
  }
}

function editAssignment(assignment) {
  form.value = {
    id: assignment.id,
    title: assignment.title,
    description: assignment.description,
    class_id: assignment.class_id,
    deadline: assignment.deadline ? new Date(assignment.deadline) : null,
    total_score: assignment.total_score
  }
  showEditDialog.value = true
}

async function updateAssignment() {
  saving.value = true
  try {
    const data = { ...form.value }
    if (data.deadline) {
      const date = new Date(data.deadline)
      data.deadline = new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString()
    }
    await api.put(`/assignments/${form.value.id}`, data)
    ElMessage.success('更新成功')
    showEditDialog.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    saving.value = false
  }
}

async function deleteAssignment(assignment) {
  try {
    await ElMessageBox.confirm(`确定要删除作业 ${assignment.title} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/assignments/${assignment.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function resetForm() {
  form.value = {
    id: null,
    title: '',
    description: '',
    class_id: null,
    deadline: null,
    total_score: 100
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
</style>
