<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const apiStatus = ref('')

const checkBackend = async () => {
  try {
    const res = await fetch('/api/v1/health')
    const data = await res.json()
    apiStatus.value = data.message
  } catch (e: any) {
    apiStatus.value = '后端连接失败：' + e.message
  }
}

const goToInspection = () => router.push('/inspection')
const goToRecords = () => router.push('/records')
const goToUsers = () => router.push('/users')
const goToDict = () => router.push('/dict')
const goToExceptions = () => router.push('/exceptions')

const logout = () => {
  authStore.logout()
  window.location.href = '/login'
}
</script>

<template>
  <div class="container">
    <div v-if="authStore.isLoggedIn" class="user-bar">
      欢迎，{{ authStore.user?.real_name || authStore.user?.username }}
      <el-button type="danger" size="small" @click="logout">退出</el-button>
    </div>
    <h1>产线电脑巡检系统</h1>
    <el-button type="primary" @click="checkBackend">测试后端连接</el-button>
    <el-button type="success" @click="goToInspection">巡检录入</el-button>
    <el-button type="info" @click="goToRecords">记录查询</el-button>
    <el-button v-if="authStore.isSuperAdmin" type="warning" @click="goToUsers">用户管理</el-button>
    <el-button v-if="authStore.isSuperAdmin" type="success" @click="goToDict">厂区字典</el-button>
    <el-button type="danger" @click="goToExceptions">异常签核</el-button>
    <p v-if="apiStatus">后端状态：{{ apiStatus }}</p>
  </div>
</template>

<style>
.container {
  text-align: center;
  padding-top: 100px;
}
.user-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  border-bottom: 1px solid #eee;
}
</style>
