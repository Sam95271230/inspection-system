<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getInspectionList, getPlantDictTree, exportInspections } from '@/api/inspection'
import { ElMessage } from 'element-plus'

// 字典
const plantOptions = ref<any[]>([])
const lineOptions = ref<any[]>([])
const stationOptions = ref<any[]>([])

// 查询条件
const query = reactive({
  plant_id: '',
  line_id: '',
  station_id: '',
  start_time: '',
  end_time: '',
  antivirus_status: '',
  domain_status: '',
})

// 表格数据
const loading = ref(false)
const tableData = ref<any[]>([])
const total = ref(0)
const pagination = reactive({
  page: 1,
  page_size: 10
})

// 详情弹窗
const detailVisible = ref(false)
const currentRecord = ref<any>(null)

// 状态映射
const statusMap: Record<string, string> = {
  NORMAL: '正常',
  ABNORMAL: '异常',
  NOT_INSTALLED: '未安装',
  JOINED: '已入域',
  NOT_JOINED: '未入域',
  NOT_APPLICABLE: '不适用'
}

// 加载厂区字典
const loadDict = async () => {
  const res = await getPlantDictTree()
  plantOptions.value = res.map((p: any) => ({
    value: p.id,
    label: `${p.code} - ${p.name}`,
    children: p.children
  }))
}

const onPlantChange = (val: string) => {
  query.plant_id = val
  query.line_id = ''
  query.station_id = ''
  lineOptions.value = []
  stationOptions.value = []
  
  const plant = plantOptions.value.find(p => p.value === val)
  if (plant && plant.children) {
    lineOptions.value = plant.children.map((l: any) => ({
      value: l.id,
      label: `${l.code} - ${l.name}`,
      children: l.children
    }))
  }
}

const onLineChange = (val: string) => {
  query.line_id = val
  query.station_id = ''
  stationOptions.value = []
  
  const line = lineOptions.value.find(l => l.value === val)
  if (line && line.children) {
    stationOptions.value = line.children.map((s: any) => ({
      value: s.id,
      label: `${s.code} - ${s.name}`
    }))
  }
}

// 查询列表
const fetchList = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (query.plant_id) params.plant_id = query.plant_id
    if (query.line_id) params.line_id = query.line_id
    if (query.station_id) params.station_id = query.station_id
    if (query.start_time) params.start_time = query.start_time
    if (query.end_time) params.end_time = query.end_time + ' 23:59:59'
    if (query.antivirus_status) params.antivirus_status = query.antivirus_status
    if (query.domain_status) params.domain_status = query.domain_status

    const res: any = await getInspectionList(params)
    tableData.value = res.list || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

// 重置查询
const resetQuery = () => {
  query.plant_id = ''
  query.line_id = ''
  query.station_id = ''
  query.start_time = ''
  query.end_time = ''
  query.antivirus_status = ''
  query.domain_status = ''
  lineOptions.value = []
  stationOptions.value = []
  pagination.page = 1
  fetchList()
}

// 查看详情
const showDetail = (row: any) => {
  currentRecord.value = row
  detailVisible.value = true
}

// 导出 Excel
const exportLoading = ref(false)
const handleExport = async () => {
  exportLoading.value = true
  try {
    const params: any = {}
    if (query.plant_id) params.plant_id = query.plant_id
    if (query.line_id) params.line_id = query.line_id
    if (query.station_id) params.station_id = query.station_id
    if (query.start_time) params.start_time = query.start_time
    if (query.end_time) params.end_time = query.end_time + ' 23:59:59'
    if (query.antivirus_status) params.antivirus_status = query.antivirus_status
    if (query.domain_status) params.domain_status = query.domain_status

    await exportInspections(params)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

onMounted(() => {
  loadDict()
  fetchList()
})
</script>

<template>
  <div class="records-page">
    <el-card>
      <template #header>
        <div class="page-header">巡检记录查询</div>
      </template>

      <!-- 筛选条件 -->
      <el-form :model="query" inline label-position="left">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="厂区">
              <el-select v-model="query.plant_id" placeholder="厂区" clearable style="width: 100%" @change="onPlantChange">
                <el-option v-for="opt in plantOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="线别">
              <el-select v-model="query.line_id" placeholder="线别" clearable style="width: 100%" :disabled="!query.plant_id" @change="onLineChange">
                <el-option v-for="opt in lineOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="站别">
              <el-select v-model="query.station_id" placeholder="站别" clearable style="width: 100%" :disabled="!query.line_id">
                <el-option v-for="opt in stationOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="开始日期">
              <el-date-picker v-model="query.start_time" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="结束日期">
              <el-date-picker v-model="query.end_time" type="date" placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="防毒状态">
              <el-select v-model="query.antivirus_status" placeholder="全部" clearable style="width: 100%">
                <el-option label="正常" value="NORMAL" />
                <el-option label="异常" value="ABNORMAL" />
                <el-option label="未安装" value="NOT_INSTALLED" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="入域状态">
              <el-select v-model="query.domain_status" placeholder="全部" clearable style="width: 100%">
                <el-option label="已入域" value="JOINED" />
                <el-option label="未入域" value="NOT_JOINED" />
                <el-option label="不适用" value="NOT_APPLICABLE" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
          <el-button type="success" :loading="exportLoading" @click="handleExport">导出 Excel</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="serial_no" label="巡检单号" width="160" />
        <el-table-column prop="ip_address" label="IP 地址" width="140" />
        <el-table-column label="防毒软件" width="120">
          <template #default="{ row }">
            <el-tag :type="row.antivirus_status === 'NORMAL' ? 'success' : 'danger'">
              {{ statusMap[row.antivirus_status] || row.antivirus_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="入域情况" width="120">
          <template #default="{ row }">
            <el-tag :type="row.domain_status === 'JOINED' ? 'success' : 'info'">
              {{ statusMap[row.domain_status] || row.domain_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="inspect_time" label="巡检时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="巡检详情" width="60%">
      <div v-if="currentRecord">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="巡检单号">{{ currentRecord.serial_no }}</el-descriptions-item>
          <el-descriptions-item label="IP 地址">{{ currentRecord.ip_address }}</el-descriptions-item>
          <el-descriptions-item label="防毒软件">{{ statusMap[currentRecord.antivirus_status] }}</el-descriptions-item>
          <el-descriptions-item label="入域情况">{{ statusMap[currentRecord.domain_status] }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ currentRecord.remark || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="image-section">
          <h4>巡检证据</h4>
          <div class="image-list">
            <el-image
              v-for="(img, index) in currentRecord.images"
              :key="index"
              :src="img.url"
              :preview-src-list="currentRecord.images.map((i: any) => i.url)"
              fit="cover"
              class="detail-image"
            />
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.records-page {
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
.image-section {
  margin-top: 20px;
}
.image-section h4 {
  margin-bottom: 12px;
}
.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.detail-image {
  width: 120px;
  height: 120px;
  border-radius: 6px;
  border: 1px solid #eee;
}
</style>
