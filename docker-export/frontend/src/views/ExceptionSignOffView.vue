<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getExceptionList,
  getExceptionHistory,
  assignException,
  processException,
  approveException,
  rejectException,
  reprocessException
} from '@/api/exception'
import { getUserList } from '@/api/user'


// 状态映射
const statusMap: Record<string, { label: string; type: string }> = {
  PENDING: { label: '待分配', type: 'info' },
  PROCESSING: { label: '处理中', type: 'warning' },
  PENDING_SIGNOFF: { label: '待签核', type: 'primary' },
  CLOSED: { label: '已结案', type: 'success' },
  REJECTED: { label: '已驳回', type: 'danger' }
}

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

const detailVisible = ref(false)
const currentDetail = ref<any>(null)
const historyList = ref<any[]>([])

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
  actionDialogVisible.value = true
}

const submitAction = async () => {
  if (!currentTicket.value) return

  const { id } = currentTicket.value
  const data = {
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
        await processException(id, data)
        break
      case 'APPROVE':
        await approveException(id, data)
        break
      case 'REJECT':
        await rejectException(id, data)
        break
      case 'REPROCESS':
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
  const res: any = await getExceptionHistory(row.id)
  historyList.value = res || []
}

const getActions = (row: any) => {
  const actions: any[] = []
  const status = row.status

  if (status === 'PENDING') {
    actions.push({ label: '分配', type: 'primary', action: 'ASSIGN' })
  }
  if (status === 'PROCESSING') {
    actions.push({ label: '提交处理结果', type: 'primary', action: 'PROCESS' })
  }
  if (status === 'PENDING_SIGNOFF') {
    actions.push({ label: '签核通过', type: 'success', action: 'APPROVE' })
    actions.push({ label: '驳回', type: 'danger', action: 'REJECT' })
  }
  if (status === 'REJECTED') {
    actions.push({ label: '重新处理', type: 'warning', action: 'REPROCESS' })
  }

  return actions
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
        </el-form>
      </div>
      <template #footer>
        <el-button @click="actionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAction">提交</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="异常详情" width="700px">
      <div v-if="currentDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="巡检单号">{{ currentDetail.serial_no }}</el-descriptions-item>
          <el-descriptions-item label="异常摘要">{{ currentDetail.title }}</el-descriptions-item>
          <el-descriptions-item label="厂区">{{ currentDetail.plant_name }}</el-descriptions-item>
          <el-descriptions-item label="当前处理人">{{ currentDetail.current_assignee_name || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 class="timeline-title">处理时间轴</h4>
        <el-timeline>
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
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.exception-page {
  padding: 16px;
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
.timeline-title {
  margin: 20px 0 12px 0;
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
</style>
