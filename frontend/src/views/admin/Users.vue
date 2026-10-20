<template>
  <div class="admin-users-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            + 添加用户
          </el-button>
        </div>
      </template>

      <el-table :data="users" style="width: 100%" v-loading="loading">
        <el-table-column prop="username" label="用户名/学号" width="150" />
        <el-table-column prop="display_name" label="姓名" width="150" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="scope">
            <el-tag :type="getRoleTagType(scope.row.role)">
              {{ getRoleText(scope.row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ scope.row.created_at ? new Date(scope.row.created_at).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="editUser(scope.row)">编辑</el-button>
            <el-button size="small" type="warning" @click="resetPassword(scope.row)">重置密码</el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteUser(scope.row)"
              :disabled="scope.row.role === 'admin'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加用户对话框 -->
    <el-dialog v-model="showCreateDialog" title="添加用户" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名/学号">
          <el-input v-model="form.username" placeholder="请输入用户名或学号" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.display_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" placeholder="请选择角色">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createUser" :loading="saving">添加</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑用户" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="用户名/学号">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="editForm.display_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" placeholder="请选择角色" :disabled="editForm.role === 'admin'">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateUser" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="showResetDialog" title="重置密码" width="400px">
      <el-form :model="resetForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="resetForm.username" disabled />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="resetForm.password" type="password" placeholder="请输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResetDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmResetPassword" :loading="saving">重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const users = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showResetDialog = ref(false)

const form = ref({
  username: '',
  display_name: '',
  password: '',
  role: 'student'
})

const editForm = ref({
  id: null,
  username: '',
  display_name: '',
  role: ''
})

const resetForm = ref({
  id: null,
  username: '',
  password: ''
})

function getRoleTagType(role) {
  const types = {
    admin: 'danger',
    teacher: 'warning',
    student: 'success'
  }
  return types[role] || 'info'
}

function getRoleText(role) {
  const texts = {
    admin: '管理员',
    teacher: '教师',
    student: '学生'
  }
  return texts[role] || role
}

async function fetchUsers() {
  loading.value = true
  try {
    const response = await api.get('/admin/users')
    users.value = response.data
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function createUser() {
  if (!form.value.username || !form.value.display_name || !form.value.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  saving.value = true
  try {
    await api.post('/admin/users', form.value)
    ElMessage.success('添加成功')
    showCreateDialog.value = false
    form.value = { username: '', display_name: '', password: '', role: 'student' }
    fetchUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '添加失败')
  } finally {
    saving.value = false
  }
}

function editUser(user) {
  editForm.value = {
    id: user.id,
    username: user.username,
    display_name: user.display_name,
    role: user.role
  }
  showEditDialog.value = true
}

async function updateUser() {
  if (!editForm.value.display_name) {
    ElMessage.warning('姓名不能为空')
    return
  }
  saving.value = true
  try {
    await api.put(`/admin/users/${editForm.value.id}`, {
      display_name: editForm.value.display_name,
      role: editForm.value.role
    })
    ElMessage.success('更新成功')
    showEditDialog.value = false
    fetchUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '更新失败')
  } finally {
    saving.value = false
  }
}

function resetPassword(user) {
  resetForm.value = {
    id: user.id,
    username: user.username,
    password: ''
  }
  showResetDialog.value = true
}

async function confirmResetPassword() {
  if (!resetForm.value.password) {
    ElMessage.warning('请输入新密码')
    return
  }
  saving.value = true
  try {
    await api.post(`/admin/users/${resetForm.value.id}/reset-password`, {
      password: resetForm.value.password
    })
    ElMessage.success('密码重置成功')
    showResetDialog.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '密码重置失败')
  } finally {
    saving.value = false
  }
}

async function deleteUser(user) {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${user.display_name} (${user.username}) 吗？\n注意：此操作不可恢复，用户的作业提交记录也将被删除。`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await api.delete(`/admin/users/${user.id}`)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
