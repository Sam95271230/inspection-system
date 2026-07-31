import { defineStore } from 'pinia'

const getStoredUser = () => {
  const raw = localStorage.getItem('user')
  if (raw) {
    try {
      return JSON.parse(raw)
    } catch (e) {
      return null
    }
  }
  return null
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: getStoredUser() as any,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    isSuperAdmin: (state) => !!state.user?.is_superadmin,
  },

  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem('token', token)
    },
    setUser(user: any) {
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})
