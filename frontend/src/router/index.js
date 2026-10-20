import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

let isInitializing = true
let initializationPromise = null

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/xuetang-entry',
    redirect: to => {
      const params = new URLSearchParams(to.query)
      const target = params.toString() ? `/xuetang?${params.toString()}` : '/xuetang'
      return target
    }
  },
  {
    path: '/xuetang',
    name: 'XuetangEntry',
    component: () => import('@/views/XuetangEntry.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/Chat.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue')
      },
      {
        path: 'admin',
        meta: { requiresAdmin: true },
        children: [
          {
            path: 'users',
            name: 'AdminUsers',
            component: () => import('@/views/admin/Users.vue')
          }
        ]
      },
      {
        path: 'teacher',
        meta: { requiresTeacher: true },
        children: [
          {
            path: 'classes',
            name: 'Classes',
            component: () => import('@/views/teacher/Classes.vue')
          },
          {
            path: 'assignments',
            name: 'Assignments',
            component: () => import('@/views/teacher/Assignments.vue')
          },
          {
            path: 'students',
            name: 'Students',
            component: () => import('@/views/teacher/Students.vue')
          },
          {
            path: 'submissions',
            name: 'Submissions',
            component: () => import('@/views/teacher/Submissions.vue')
          },
          {
            path: 'submission/:id',
            name: 'ViewSubmission',
            component: () => import('@/views/teacher/ViewSubmission.vue')
          },
          {
            path: 'chat-history',
            name: 'ChatHistory',
            component: () => import('@/views/teacher/ChatHistory.vue')
          }
        ]
      },
      {
        path: 'student',
        children: [
          {
            path: 'assignments',
            name: 'StudentAssignments',
            component: () => import('@/views/student/Assignments.vue')
          },
          {
            path: 'assignment/:id',
            name: 'StudentAssignmentDetail',
            component: () => import('@/views/student/AssignmentDetail.vue')
          }
        ]
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

async function ensureUserInitialized() {
  const userStore = useUserStore()
  
  if (userStore.user) {
    return true
  }
  
  const token = localStorage.getItem('token')
  if (!token) {
    return false
  }
  
  if (initializationPromise) {
    return initializationPromise
  }
  
  initializationPromise = userStore.fetchUser()
    .then(() => true)
    .catch(() => {
      userStore.logout()
      return false
    })
    .finally(() => {
      initializationPromise = null
    })
  
  return initializationPromise
}

router.beforeEach(async (to, from, next) => {
  if (!window.__VUE_APP_READY__) {
    next('/login')
    return
  }
  
  if (isInitializing) {
    isInitializing = false
    const hasUser = await ensureUserInitialized()
    if (!hasUser && to.meta.requiresAuth) {
      next('/login')
      return
    }
  }
  
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.meta.requiresTeacher && !userStore.isTeacher) {
    next('/dashboard')
  } else if (to.meta.requiresAdmin && userStore.user?.role !== 'admin') {
    next('/dashboard')
  } else if (!to.meta.requiresAuth && userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
