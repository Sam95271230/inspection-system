<script setup lang="ts">
import { ref } from 'vue'

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
</script>

<template>
  <div class="home-page">
    <el-card>
      <h2 style="margin-bottom: 24px;">欢迎使用产线电脑巡检系统</h2>
      <p style="color: #666; margin-bottom: 24px;">请通过左侧导航菜单选择功能模块</p>
      <el-button type="primary" @click="checkBackend">测试后端连接</el-button>
      <p v-if="apiStatus" style="margin-top: 16px; color: #909399;">后端状态：{{ apiStatus }}</p>
    </el-card>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 800px;
}
</style>