<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getUserList, createUser, updateUser, deleteUser, toggleUserStatus, getRoleList } from '@/api/user'
import { getPlantDictTree } from '@/api/inspection'

const authStore = useAuthStore()

const isSuperAdmin = computed(() => {
  return authStore.user?.is_superadmin || false
})

const users = ref<any[]>([])
const roles = ref<any[]>([])
const plants = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)

const form = reactive({
  id: '',
  username: '',
  password: '',
  real_name: '',
  email: '',
  mobile: '',
  is_active: true,
  is_superadmin: false,
  role_ids: [] as string[],
  plant_ids: [] as string[]
})
const plantRolesMap = reactive<Record<string, string>>({})

const fetchUsers = async () => {
  loading.value = true
  try {
    const res: any = await getUserList({ page: 1, page_size: 100 })
    users.value = res.list || []
  } finally {
    loading.value = false
  }
}

const fetchRoles = async () => {
  const res: any = await getRoleList()
  roles.value = res || []
}

const fetchPlants = async () => {
  const res: any = await getPlantDictTree()
  plants.value = res.map((p: any) => ({ value: p.id, label: `${p.code} - ${p.name}` })) || []
}

const openCreate = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row: any) => {
  isEdit.value = true
  form.id = row.id
  form.username = row.username
  form.password = ''
  form.real_name = row.real_name || ''
  form.email = row.email || ''
  form.mobile = row.mobile || ''
  form.is_active = row.is_active
  form.is_superadmin = row.is_superadmin
  form.role_ids = row.role_ids || []
  form.plant_ids = row.plant_ids || []
  for (const pid of Object.keys(plantRolesMap)) delete plantRolesMap[pid]
  if (row.plant_roles?.length) {
    for (const pr of row.plant_roles) plantRolesMap[pr.plant_id] = pr.role
  } else if (row.plant_ids?.length) {
    for (const pid of row.plant_ids) plantRolesMap[pid] = 'MEMBER'
  }
  dialogVisible.value = true
}

const resetForm = () => {
  form.id = ''
  form.username = ''
  form.password = ''
  form.real_name = ''
  form.email = ''
  form.mobile = ''
  form.is_active = true
  form.is_superadmin = false
  form.role_ids = []
  form.plant_ids = []
  for (const pid of Object.keys(plantRolesMap)) delete plantRolesMap[pid]
}

const handleSave = async () => {
  if (!form.username) {
    ElMessage.error('用户名不能为空')
    return
  }
  if (!isEdit.value && !form.password) {
    ElMessage.error('密码不能为空')
    return
  }

  const plantRoles = (form.plant_ids || []).map(pid => ({
    plant_id: pid,
    role: plantRolesMap[pid] || 'MEMBER'
  }))
  const data: any = {
    username: form.username,
    real_name: form.real_name,
    email: form.email,
    mobile: form.mobile,
    is_active: form.is_active,
    is_superadmin: form.is_superadmin,
    role_ids: form.role_ids,
    plant_ids: form.is_superadmin ? [] : form.plant_ids,
    plant_roles: form.is_superadmin ? [] : plantRoles
  }

  try {
    if (isEdit.value) {
      if (form.password) data.password = form.password
      await updateUser(form.id, data)
      ElMessage.success('用户更新成功')
    } else {
      data.password = form.password
      await createUser(data)
      ElMessage.success('用户创建成功')
    }
    dialogVisible.value = false
    fetchUsers()
  } catch (error) {
    console.error(error)
  }
}

const handleToggleStatus = async (row: any) => {
  try {
    await toggleUserStatus(row.id)
    ElMessage.success('状态更新成功')
    fetchUsers()
  } catch (error) {
    console.error(error)
  }
}

const handleDelete = async (row: any) => {
  if (!isSuperAdmin.value) {
    ElMessage.error('仅超级管理员可删除用户')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认删除用户 "${row.username}" 吗？此操作不可恢复`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
  fetchPlants()
})
</script>

<template>
  <div class="user-management-page">
    <el-card>
      <template #header>
        <div class="page-header">
          <span>用户与权限管理</span>
          <el-button v-if="isSuperAdmin" type="primary" @click="openCreate">新增用户</el-button>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" border stripe>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="email" label="邮件地址" width="180" />
        <el-table-column prop="mobile" label="手机号" width="130" />
        <el-table-column label="角色" width="160">
          <template #default="{ row }">
            <template v-if="row.is_superadmin">
              <el-tag type="danger">超级管理员</el-tag>
            </template>
            <template v-else-if="row.role_names?.length">
              <el-tag v-for="name in row.role_names" :key="name" size="small" style="margin-right: 4px;">
                {{ name }}
              </el-tag>
            </template>
            <span v-else class="no-permission">无角色</span>
          </template>
        </el-table-column>
        <el-table-column label="授权厂区（角色）" min-width="280">
          <template #default="{ row }">
            <el-tag v-if="row.is_superadmin" type="success">全部厂区</el-tag>
            <template v-else>
              <template v-if="row.plant_roles?.length">
                <el-tag
                  v-for="pr in row.plant_roles"
                  :key="pr.plant_id"
                  :type="pr.role === 'LEADER' ? 'warning' : 'info'"
                  class="plant-tag"
                >
                  {{ plants.find(p => p.value === pr.plant_id)?.label || pr.plant_id }}
                  <span style="margin-left:4px;font-size:11px">[{{ pr.role === 'LEADER' ? 'Leader' : 'Member' }}]</span>
                </el-tag>
              </template>
              <!-- 向后兼容旧数据 plant_ids -->
              <template v-else-if="row.plant_ids?.length">
                <el-tag v-for="pid in row.plant_ids" :key="pid" type="info" class="plant-tag">
                  {{ plants.find(p => p.value === pid)?.label || pid }}
                </el-tag>
              </template>
              <span v-else class="no-permission">无授权厂区</span>
            </template>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button :type="row.is_active ? 'danger' : 'success'" link @click="handleToggleStatus(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button v-if="isSuperAdmin" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" :placeholder="isEdit ? '不填则保持不变' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="邮件地址">
          <el-input v-model="form.email" placeholder="用于接收签核通知等" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.mobile" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_ids" multiple style="width: 100%" placeholder="请选择角色">
            <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="超级管理员">
          <el-switch v-model="form.is_superadmin" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item label="授权厂区（角色）" v-if="!form.is_superadmin">
          <div v-for="plant in plants" :key="plant.value" style="margin-bottom:8px;">
            <el-checkbox
              :model-value="form.plant_ids.includes(plant.value)"
              @change="(val: boolean) => {
                if (val) {
                  form.plant_ids.push(plant.value)
                  if (!plantRolesMap[plant.value]) plantRolesMap[plant.value] = 'MEMBER'
                } else {
                  const idx = form.plant_ids.indexOf(plant.value)
                  if (idx > -1) form.plant_ids.splice(idx, 1)
                  delete plantRolesMap[plant.value]
                }
              }"
            >
              {{ plant.label }}
            </el-checkbox>
            <el-radio-group
              v-if="form.plant_ids.includes(plant.value)"
              v-model="plantRolesMap[plant.value]"
              style="margin-left:24px;"
              size="small"
            >
              <el-radio value="MEMBER">Member</el-radio>
              <el-radio value="LEADER">Leader</el-radio>
            </el-radio-group>
          </div>
          <span v-if="plants.length === 0" style="color:#909399;font-size:12px">暂无可选厂区，请先在厂区字典中添加</span>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.user-management-page {
  padding: 0;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
}
.plant-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}
.no-permission {
  color: #f56c6c;
  font-size: 12px;
}
</style>