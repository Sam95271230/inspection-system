<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  HomeFilled,
  Edit,
  Search,
  WarningFilled,
  Setting,
  User,
  Message,
} from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()

const isLoginPage = computed(() => route.path === '/login')

const menuItems = computed(() => {
  const items = [
    { path: '/', title: '首页', icon: HomeFilled },
    { path: '/inspection', title: '巡检录入', icon: Edit },
    { path: '/records', title: '记录查询', icon: Search },
    { path: '/exceptions', title: '异常签核', icon: WarningFilled },
  ]
  if (authStore.isSuperAdmin) {
    items.push(
      { path: '/dict', title: '厂区字典', icon: Setting },
      { path: '/users', title: '用户管理', icon: User },
      { path: '/email', title: '邮件配置', icon: Message },
    )
  }
  return items
})

const activeMenu = computed(() => route.path)

const logout = () => {
  authStore.logout()
  window.location.href = '/login'
}
</script>

<template>
  <div v-if="isLoginPage" class="app-login">
    <router-view />
  </div>
  <el-container v-else class="app-layout">
    <el-aside width="220px" class="app-aside">
      <div class="aside-header">
        <h2>产线电脑巡检系统</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        class="aside-menu"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
      <div class="aside-footer">
        <div class="user-info">
          <el-icon><User /></el-icon>
          <span class="user-name">{{ authStore.user?.real_name || authStore.user?.username }}</span>
        </div>
        <el-button type="danger" size="small" @click="logout" text>退出登录</el-button>
      </div>
    </el-aside>
    <el-container>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
}

.app-layout {
  height: 100%;
}

.app-aside {
  background-color: #304156;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.aside-header {
  padding: 20px 16px 16px;
  text-align: center;
}

.aside-header h2 {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.aside-menu {
  flex: 1;
  border-right: none;
  overflow-y: auto;
}

.aside-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #bfcbd9;
  font-size: 13px;
}

.user-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-main {
  background-color: #f0f2f5;
  min-height: 100%;
  padding: 20px;
}

.app-login {
  height: 100%;
}
</style>
