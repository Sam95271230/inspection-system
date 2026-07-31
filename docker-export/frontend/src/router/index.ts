import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/inspection',
    name: 'Inspection',
    component: () => import('@/views/InspectionFormView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/records',
    name: 'Records',
    component: () => import('@/views/InspectionRecordsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('@/views/UserManagementView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/exceptions',
    name: 'Exceptions',
    component: () => import('@/views/ExceptionSignOffView.vue'),
    meta: { requiresAuth: true },
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
  } else if (to.meta.requiresAdmin && !authStore.isSuperAdmin) {
    next('/')
  } else {
    next()
  }
})

export default router
