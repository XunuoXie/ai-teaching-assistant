import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))

  const isLoggedIn = computed(() => !!user.value)
  const isTeacher = computed(() => user.value?.role === 'teacher' || user.value?.role === 'admin')
  const isStudent = computed(() => user.value?.role === 'student')
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(credentials) {
    const response = await api.post('/auth/login', credentials)
    user.value = response.data.user
    token.value = response.data.token
    localStorage.setItem('token', response.data.token)
    return response
  }

  async function register(data) {
    const response = await api.post('/auth/register', data)
    return response
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  return {
    user,
    token,
    isLoggedIn,
    isTeacher,
    isStudent,
    isAdmin,
    login,
    register,
    fetchUser,
    logout
  }
})
