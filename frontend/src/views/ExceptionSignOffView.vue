<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getExceptionList,
  getExceptionHistory,
  assignException,
  processException,
  approveException,
  rejectException,
  reprocessException,
  uploadExceptionImage
} from '@/api/exception'
import { getUserList } from '@/api/user'
import { useAuthStore } from '@/stores/auth'
import { Hide } from '@element-plus/icons-vue'
import { EXCEPTION_STATUS_MAP } from '@/constants'

// 状态映射（从常量导入）
const statusMap = EXCEPTION_STATUS_MAP

const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

const loading = ref(false)
const tableData = ref<any[]>([])
const total = ref(0)
const pagination = reactive({ page: 1, page_size: 10 })

const users = ref<any[]>([])

const actionDialogVisible = ref(false)
const actionType = ref('')
const currentTicket = ref<any>(null)
const actionForm = reactive({
  remark: '',
  assignee_id: ''
})
const actionImages = ref<any[]>([])
const actionUploading = ref(false)

const detailVisible = ref(false)
const currentDetail = ref<any>(null)
const historyList = ref<any[]>([])
const inspectionImages = ref<any[]>([])
const detailLoading = ref(false)

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await getExceptionList({
      page: pagination.page,
      page_size: pagination.page_size
    })
    tableData.value = res.list || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

const fetchUsers = async () => {
  const res: any = await getUserList({ page: 1, page_size: 100 })
  users.value = res.list || []
}

const openAction = (row: any, action: string) => {
  currentTicket.value = row
  actionType.value = action
  actionForm.remark = ''
  actionForm.assignee_id = ''
  actionImages.value = []
  actionDialogVisible.value = true
}

const handleActionImageUpload = async (file: any) => {
  const rawFile = file.raw as File
  if (!rawFile.type.startsWith('image/')) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (rawFile.size > 5 * 1024 * 1024) {
    ElMessage.error('单张图片不能超过 5MB')
    return false
  }
  actionUploading.value = true
  try {
    const res: any = await uploadExceptionImage(rawFile)
    actionImages.value.push(res)
    ElMessage.success('上传成功')
  } catch {
    ElMessage.error('上传失败')
  } finally {
    actionUploading.value = false
  }
  return false
}

const removeActionImage = (index: number) => {
  actionImages.value.splice(index, 1)
}

const submitAction = async () => {
  if (!currentTicket.value) return

  const { id } = currentTicket.value
  const data: any = {
    remark: actionForm.remark,
    assignee_id: actionForm.assignee_id
  }

  try {
    if (actionType.value === 'ASSIGN' && !data.assignee_id) {
      ElMessage.error('请选择处理人')
      return
    }

    switch (actionType.value) {
      case 'ASSIGN':
        await assignException(id, data)
        break
      case 'PROCESS':
        data.images = actionImages.value
        await processException(id, data)
        break
      case 'APPROVE':
        await approveException(id, data)
        break
      case 'REJECT':
        await rejectException(id, data)
        break
      case 'REPROCESS':
        data.images = actionImages.value
        await reprocessException(id, data)
        break
    }

    ElMessage.success('操作成功')
    actionDialogVisible.value = false
    fetchList()
    if (detailVisible.value && currentDetail.value?.id === id) {
      openDetail(currentDetail.value)
    }
  } catch (error) {
    console.error(error)
  }
}

const openDetail = async (row: any) => {
  currentDetail.value = row
  detailVisible.value = true
  detailLoading.value = true
  inspectionImages.value = []
  historyList.value = []
  try {
    const res: any = await getExceptionHistory(row.id)
    // 新接口返回 { history, images, inspection_id, serial_no }
    if (Array.isArray(res)) {
      historyList.value = res
    } else {
      historyList.value = res.history || []
      inspectionImages.value = res.images || []
    }
  } catch (error) {
    console.error(error)
  } finally {
    detailLoading.value = false
  }
}

const getActions = (row: any) => {
  const actions: any[] = []
  const status = row.status
  const userId = currentUser.value?.id
  const isSuperAdmin = currentUser.value?.is_superadmin

  // 按钮权限控制：根据用户角色和工单状态决定可见的操作
  if (status === 'PENDING') {
    // 超级管理员或厂区 Leader 可分配（后端做最终权限校验）
    if (isSuperAdmin || row.current_assignee_id !== userId) {
      actions.push({ label: '分配', type: 'primary', action: 'ASSIGN' })
    }
  }
  if (status === 'PROCESSING') {
    // 只有当前处理人可以提交处理结果
    if (row.current_assignee_id === userId) {
      actions.push({ label: '提交处理结果', type: 'primary', action: 'PROCESS' })
    }
  }
  if (status === 'PENDING_SIGNOFF') {
    // 超级管理员或该厂区Leader可签核
    if (isSuperAdmin || row.current_assignee_id === userId) {
      actions.push({ label: '签核通过', type: 'success', action: 'APPROVE' })
      actions.push({ label: '驳回', type: 'danger', action: 'REJECT' })
    }
  }
  if (status === 'REJECTED' && row.current_assignee_id === userId) {
    // 驳回后的工单，原处理人可重新提交
    actions.push({ label: '重新处理', type: 'warning', action: 'REPROCESS' })
  }

  return actions
}

const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')

const openImagePreview = (url: string) => {
  imagePreviewUrl.value = url
  imagePreviewVisible.value = true
}

const getImageUrl = (item: string): string | null => {
  try {
    const obj = JSON.parse(item)
    return obj.url || null
  } catch {
    if (item.startsWith('http')) return item
    return null
  }
}

onMounted(() => {
  fetchList()
  fetchUsers()
})
</script>

<template>
  <div class="exception-page">
    <el-card>
      <template #header>
        <div class="page-header">异常签核与追踪</div>
      </template>

      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="serial_no" label="巡检单号" width="160" />
        <el-table-column prop="plant_name" label="厂区" width="120" />
        <el-table-column prop="ip_address" label="IP 地址" width="140" />
        <el-table-column prop="title" label="异常摘要" min-width="200" />
        <el-table-column label="当前状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type">
              {{ statusMap[row.status]?.label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_assignee_name" label="当前处理人" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button
              v-for="btn in getActions(row)"
              :key="btn.action"
              :type="btn.type"
              size="small"
              link
              @click="openAction(row, btn.action)"
            >
              {{ btn.label }}
            </el-button>
            <el-button type="primary" size="small" link @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </el-card>

    <!-- 操作弹窗 -->
    <el-dialog v-model="actionDialogVisible" title="异常处理" width="500px">
      <div v-if="currentTicket">
        <el-form :model="actionForm" label-width="100px">
          <el-form-item label="处理人" v-if="actionType === 'ASSIGN'">
            <el-select v-model="actionForm.assignee_id" placeholder="请选择处理人" style="width: 100%">
              <el-option v-for="u in users" :key="u.id" :label="u.username" :value="u.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="处理说明">
            <el-input v-model="actionForm.remark" type="textarea" :rows="4" placeholder="请输入处理说明" />
          </el-form-item>
          <el-form-item label="处理图片" v-if="actionType === 'PROCESS' || actionType === 'REPROCESS'">
            <div>
              <el-upload
                :show-file-list="false"
                :auto-upload="false"
                :on-change="handleActionImageUpload"
                accept="image/*"
              >
                <el-button type="primary" :loading="actionUploading" size="small">上传图片</el-button>
              </el-upload>
              <div class="action-images" v-if="actionImages.length > 0">
                <div v-for="(img, idx) in actionImages" :key="idx" class="action-image-item">
                  <el-image :src="img.url" fit="cover" style="width:80px;height:80px;border-radius:4px" />
                  <span class="action-image-name">{{ img.name }}</span>
                  <span class="action-image-remove" @click="removeActionImage(idx)">×</span>
                </div>
              </div>
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="actionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAction">提交</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="异常详情" width="800px" v-loading="detailLoading">
      <div v-if="currentDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="巡检单号">{{ currentDetail.serial_no }}</el-descriptions-item>
          <el-descriptions-item label="异常摘要">{{ currentDetail.title }}</el-descriptions-item>
          <el-descriptions-item label="厂区">{{ currentDetail.plant_name }}</el-descriptions-item>
          <el-descriptions-item label="当前处理人">{{ currentDetail.current_assignee_name || '-' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 巡检证据图片 -->
        <div v-if="inspectionImages.length > 0" class="images-section">
          <h4 class="section-title">巡检证据图片</h4>
          <div class="image-gallery">
            <div
              v-for="img in inspectionImages"
              :key="img.id"
              class="image-item"
              @click="openImagePreview(img.url)"
            >
              <el-image
                :src="img.url"
                fit="cover"
                class="inspection-image"
                :preview-src-list="inspectionImages.map(i => i.url)"
                :initial-index="inspectionImages.findIndex(i => i.id === img.id)"
                preview-teleported
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Hide /></el-icon>
                    <span>加载失败</span>
                  </div>
                </template>
              </el-image>
              <div class="image-name">{{ img.file_name }}</div>
            </div>
          </div>
        </div>

        <h4 class="section-title">处理时间轴</h4>
        <el-timeline v-if="historyList.length > 0">
          <el-timeline-item
            v-for="(item, index) in historyList"
            :key="index"
            :type="statusMap[item.to_status]?.type || 'info'"
            :timestamp="item.created_at"
            placement="top"
          >
            <div class="timeline-content">
              <div class="timeline-header">
                <span class="operator">{{ item.operator_name }}</span>
                <span class="action">{{ item.action }}</span>
              </div>
              <div v-if="item.remark" class="timeline-remark">备注：{{ item.remark }}</div>
              <div v-if="item.attachment_urls && item.attachment_urls.length > 0" class="timeline-images">
                <div
                  v-for="(att, attIdx) in item.attachment_urls"
                  :key="attIdx"
                  class="timeline-image-item"
                >
                  <el-image
                    v-if="getImageUrl(att)"
                    :src="getImageUrl(att)"
                    fit="cover"
                    style="width:100px;height:80px;border-radius:4px;cursor:pointer"
                    :preview-src-list="item.attachment_urls.map((a: string) => getImageUrl(a)).filter(Boolean)"
                  />
                  <el-tag v-else size="small" style="margin:2px">{{ att }}</el-tag>
                </div>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无处理记录" :image-size="60" />
      </div>
    </el-dialog>

    <!-- 图片预览弹窗 -->
    <el-dialog v-model="imagePreviewVisible" title="图片预览" width="80%" :close-on-click-modal="true">
      <div style="text-align: center;">
        <img :src="imagePreviewUrl" style="max-width: 100%; max-height: 70vh;" />
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.exception-page {
  padding: 0;
}
.page-header {
  font-size: 18px;
  font-weight: 600;
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
.section-title {
  margin: 20px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
  font-size: 15px;
}
.images-section {
  margin-top: 16px;
}
.image-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.image-item {
  width: 150px;
  cursor: pointer;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
  transition: transform 0.2s;
}
.image-item:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}
.inspection-image {
  width: 150px;
  height: 120px;
  display: block;
}
.image-name {
  padding: 4px 8px;
  font-size: 12px;
  color: #909399;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 120px;
  color: #c0c4cc;
  font-size: 12px;
  gap: 6px;
}
.timeline-content {
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
}
.timeline-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.operator {
  font-weight: 600;
}
.action {
  color: #409eff;
}
.timeline-remark {
  color: #606266;
  font-size: 13px;
}
.timeline-images {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.timeline-image-item {
  display: inline-block;
}
.action-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.action-image-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.action-image-name {
  font-size: 11px;
  color: #909399;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.action-image-remove {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 16px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  background: rgba(0,0,0,0.6);
  color: #fff;
  border-radius: 50%;
  font-size: 12px;
  cursor: pointer;
}
</style>