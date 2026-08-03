<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getEmailConfig, updateEmailConfig, testEmailConfig } from '@/api/email'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const testEmail = ref('')
const testDialogVisible = ref(false)

const form = reactive({
  smtp_host: '',
  smtp_port: 587,
  smtp_user: '',
  smtp_password: '',
  smtp_password_set: false,
  smtp_use_tls: true,
  from_name: '巡检系统',
  enabled: false,
})

const fetchConfig = async () => {
  loading.value = true
  try {
    const data: any = await getEmailConfig()
    form.smtp_host = data.smtp_host || ''
    form.smtp_port = data.smtp_port || 587
    form.smtp_user = data.smtp_user || ''
    form.smtp_password = data.smtp_password || ''
    form.smtp_password_set = data.smtp_password_set || false
    form.smtp_use_tls = data.smtp_use_tls !== false
    form.from_name = data.from_name || '巡检系统'
    form.enabled = data.enabled || false
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  if (!form.smtp_host || !form.smtp_user) {
    ElMessage.error('SMTP 服务器和账号不能为空')
    return
  }

  saving.value = true
  try {
    const payload: any = {
      smtp_host: form.smtp_host,
      smtp_port: form.smtp_port,
      smtp_user: form.smtp_user,
      smtp_use_tls: form.smtp_use_tls,
      from_name: form.from_name,
      enabled: form.enabled,
    }
    // 只有用户修改了密码才传
    if (form.smtp_password && form.smtp_password !== '******') {
      payload.smtp_password = form.smtp_password
    }
    await updateEmailConfig(payload)
    ElMessage.success('邮件配置已保存')
    fetchConfig()
  } catch (e) {
    console.error(e)
  } finally {
    saving.value = false
  }
}

const openTestDialog = () => {
  testEmail.value = ''
  testDialogVisible.value = true
}

const handleTest = async () => {
  if (!testEmail.value) {
    ElMessage.error('请输入测试邮箱地址')
    return
  }

  testing.value = true
  try {
    await testEmailConfig({ to_email: testEmail.value })
    ElMessage.success(`测试邮件已发送至 ${testEmail.value}，请查收`)
    testDialogVisible.value = false
  } catch (e) {
    console.error(e)
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  fetchConfig()
})
</script>

<template>
  <div class="email-config-page">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <span>邮件配置</span>
          <div>
            <el-button type="primary" @click="openTestDialog">发送测试邮件</el-button>
            <el-button type="success" @click="handleSave" :loading="saving">保存配置</el-button>
          </div>
        </div>
      </template>

      <el-alert
        title="配置 SMTP 邮件服务器后，系统将在异常签核流程中自动发送邮件通知相关用户。请确保用户已设置邮件地址。"
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      />

      <el-form :model="form" label-width="140px" style="max-width: 640px;">
        <el-form-item label="启用邮件通知">
          <el-switch v-model="form.enabled" active-text="开启" inactive-text="关闭" />
        </el-form-item>

        <el-form-item label="SMTP 服务器">
          <el-input v-model="form.smtp_host" placeholder="例如 smtp.qq.com" />
        </el-form-item>

        <el-form-item label="SMTP 端口">
          <el-input-number v-model="form.smtp_port" :min="1" :max="65535" />
          <span style="margin-left: 8px; color: #909399; font-size: 12px;">
            常用：TLS=587，SSL=465
          </span>
        </el-form-item>

        <el-form-item label="使用 TLS 加密">
          <el-switch v-model="form.smtp_use_tls" active-text="TLS" inactive-text="SSL" />
        </el-form-item>

        <el-form-item label="发送账号">
          <el-input v-model="form.smtp_user" placeholder="例如 user@qq.com" />
        </el-form-item>

        <el-form-item label="授权码/密码">
          <el-input
            v-model="form.smtp_password"
            type="password"
            show-password
            :placeholder="form.smtp_password_set ? '已设置，留空则不修改' : '请输入 SMTP 授权码'"
          />
        </el-form-item>

        <el-form-item label="发件人名称">
          <el-input v-model="form.from_name" placeholder="巡检系统" />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 测试弹窗 -->
    <el-dialog v-model="testDialogVisible" title="发送测试邮件" width="480px">
      <el-form label-width="100px">
        <el-form-item label="收件邮箱">
          <el-input v-model="testEmail" placeholder="请输入测试接收邮箱地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleTest" :loading="testing">发送测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.email-config-page {
  max-width: 800px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
}
</style>