<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getPlantDictTree, createInspection, batchImportInspections } from '@/api/inspection'
import ImageUploader from '@/components/ImageUploader.vue'
import { Upload, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const plantOptions = ref<any[]>([])
const lineOptions = ref<any[]>([])
const stationOptions = ref<any[]>([])

// Tab 控制
const activeTab = ref('single')

const form = reactive({
  plant_id: '',
  line_id: '',
  station_id: '',
  ip_address: '',
  machine_name: '',
  antivirus_status: 'NORMAL',
  domain_status: 'JOINED',
  inspect_time: '',
  inspector_name: '',
  remark: '',
  status: 'SUBMITTED',
  images: [] as any[]
})

// 批量导入
const batchFile = ref<File | null>(null)
const batchLoading = ref(false)

// IP 正则
const ipRegex = /^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$/

const fetchDict = async () => {
  const res = await getPlantDictTree()
  plantOptions.value = res.map((p: any) => ({
    value: p.id,
    label: `${p.code} - ${p.name}`,
    children: p.children
  }))
}

const onPlantChange = (val: string) => {
  form.plant_id = val
  form.line_id = ''
  form.station_id = ''
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
  form.line_id = val
  form.station_id = ''
  stationOptions.value = []

  const line = lineOptions.value.find(l => l.value === val)
  if (line && line.children) {
    stationOptions.value = line.children.map((s: any) => ({
      value: s.id,
      label: `${s.code} - ${s.name}`
    }))
  }
}

const submit = async () => {
  if (!form.plant_id || !form.line_id || !form.station_id) {
    ElMessage.error('请选择厂区、线别、站别')
    return
  }
  if (!form.ip_address || !ipRegex.test(form.ip_address)) {
    ElMessage.error('请输入正确的 IP 地址')
    return
  }

  loading.value = true
  try {
    await createInspection({
      ...form,
      images: form.images.map(img => ({
        name: img.name,
        storage_key: img.storage_key,
        mime_type: 'image/jpeg'
      }))
    })
    ElMessage.success('巡检提交成功')
    // 清空表单
    form.plant_id = ''
    form.line_id = ''
    form.station_id = ''
    form.ip_address = ''
    form.antivirus_status = 'NORMAL'
    form.domain_status = 'JOINED'
    form.remark = ''
    form.images = []
    lineOptions.value = []
    stationOptions.value = []
  } finally {
    loading.value = false
  }
}

// 批量导入处理
const handleBatchFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  batchFile.value = target.files?.[0] || null
}

const handleBatchImport = async () => {
  if (!batchFile.value) {
    ElMessage.warning('请先选择 ZIP 文件')
    return
  }
  batchLoading.value = true
  try {
    const res: any = await batchImportInspections(batchFile.value)
    ElMessage.success(res.message || '批量导入成功')
    batchFile.value = null
    // 清空 file input
    const input = document.querySelector('.batch-file-input') as HTMLInputElement
    if (input) input.value = ''
  } catch {
    ElMessage.error('批量导入失败，请检查文件格式')
  } finally {
    batchLoading.value = false
  }
}

const triggerBatchInput = () => {
  const input = document.querySelector('.batch-file-input') as HTMLInputElement
  if (input) input.click()
}

// 下载批量导入模板
const downloadBatchTemplate = () => {
  // 模板说明的 Excel 内容
  const instructions = [
    '# ZIP 包结构',
    '文件名: 巡检记录批量导入模板.zip',
    '├── records.xlsx      (Excel 数据文件)',
    '└── images/           (可选，巡检证据图片)',
    '    ├── 2_1.jpg       (第2行第1张图)',
    '    ├── 2_2.jpg       (第2行第2张图)',
    '    └── 3_1.jpg       (第3行第1张图)',
    '',
    '# Excel 表头格式 (records.xlsx)',
    '厂区代码 | 线别代码 | 站别代码 | IP地址 | 机器名 | 防毒状态 | 入域状态 | 巡检时间 | 巡检人 | 备注 | 图片数量',
    '',
    '# 状态值说明',
    '防毒状态: NORMAL(正常) / ABNORMAL(异常) / NOT_INSTALLED(未安装)',
    '入域状态: JOINED(已入域) / NOT_JOINED(未入域) / NOT_APPLICABLE(不适用)',
    '',
    '# 图片命名规则',
    '行号_序号.jpg 例如 2_1.jpg 表示Excel第2行数据的第1张巡检证据图片',
  ].join('\n')

  const blob = new Blob(['\uFEFF' + instructions], { type: 'text/plain;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '批量导入使用说明.txt'
  a.click()
  window.URL.revokeObjectURL(url)

  ElMessage.success('使用说明已下载，请先导入厂区字典（厂区字典管理页面），然后按说明准备 ZIP 包')
}

onMounted(() => {
  fetchDict()
})
</script>

<template>
  <div class="inspection-form-page">
    <el-card>
      <template #header>
        <div class="page-header">产线电脑巡检录入</div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- 单个录入 Tab -->
        <el-tab-pane label="单个录入" name="single">
          <el-form :model="form" label-width="120px" label-position="top">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :lg="8">
                <el-form-item label="厂区" required>
                  <el-select v-model="form.plant_id" placeholder="请选择厂区" style="width: 100%" @change="onPlantChange">
                    <el-option
                      v-for="opt in plantOptions"
                      :key="opt.value"
                      :label="opt.label"
                      :value="opt.value"
                    />
                  </el-select>
                </el-form-item>
              </el-col>

              <el-col :xs="24" :sm="12" :lg="8">
                <el-form-item label="线别" required>
                  <el-select v-model="form.line_id" placeholder="请选择线别" style="width: 100%" :disabled="!form.plant_id" @change="onLineChange">
                    <el-option
                      v-for="opt in lineOptions"
                      :key="opt.value"
                      :label="opt.label"
                      :value="opt.value"
                    />
                  </el-select>
                </el-form-item>
              </el-col>

              <el-col :xs="24" :sm="12" :lg="8">
                <el-form-item label="站别" required>
                  <el-select v-model="form.station_id" placeholder="请选择站别" style="width: 100%" :disabled="!form.line_id">
                    <el-option
                      v-for="opt in stationOptions"
                      :key="opt.value"
                      :label="opt.label"
                      :value="opt.value"
                    />
                  </el-select>
                </el-form-item>
              </el-col>

              <el-col :xs="24" :sm="12" :lg="8">
                <el-form-item label="IP 地址" required>
                  <el-input v-model="form.ip_address" placeholder="例如：192.168.1.100" />
                </el-form-item>
              </el-col>

              <el-col :xs="24" :sm="12" :lg="8">
                <el-form-item label="机器名">
                  <el-input v-model="form.machine_name" placeholder="请输入机器名" />
                </el-form-item>
              </el-col>

              <el-col :xs="24" :sm="12" :lg="8">
                <el-form-item label="巡检时间">
                  <el-date-picker
                    v-model="form.inspect_time"
                    type="datetime"
                    placeholder="请选择巡检时间"
                    value-format="YYYY-MM-DDTHH:mm:ss"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>

              <el-col :xs="24" :sm="12" :lg="8">
                <el-form-item label="巡检人">
                  <el-input v-model="form.inspector_name" placeholder="请输入巡检人姓名" />
                </el-form-item>
              </el-col>

              <el-col :xs="24" :sm="12" :lg="8">
                <el-form-item label="防毒软件情况">
                  <el-select v-model="form.antivirus_status" style="width: 100%">
                    <el-option label="正常" value="NORMAL" />
                    <el-option label="异常" value="ABNORMAL" />
                    <el-option label="未安装" value="NOT_INSTALLED" />
                  </el-select>
                </el-form-item>
              </el-col>

              <el-col :xs="24" :sm="12" :lg="8">
                <el-form-item label="入域情况">
                  <el-select v-model="form.domain_status" style="width: 100%">
                    <el-option label="已入域" value="JOINED" />
                    <el-option label="未入域" value="NOT_JOINED" />
                    <el-option label="不适用" value="NOT_APPLICABLE" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="备注说明">
              <el-input v-model="form.remark" type="textarea" :rows="4" placeholder="请输入备注" />
            </el-form-item>

            <el-form-item label="巡检证据">
              <ImageUploader v-model="form.images" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="loading" @click="submit">提交巡检</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 批量导入 Tab -->
        <el-tab-pane label="批量导入" name="batch">
          <div class="batch-import-area">
            <el-alert
              title="ZIP 包结构说明"
              type="info"
              :closable="false"
              style="margin-bottom: 16px"
            >
              <template #default>
                <div style="font-size:13px; line-height:1.8">
                  <p><strong>ZIP 包结构：</strong></p>
                  <pre style="background:#f5f5f5;padding:8px;border-radius:4px">巡检记录批量导入.zip
├── records.xlsx    (数据文件)
└── images/         (巡检证据图片，可选)
    ├── 2_1.jpg     (第2行第1张图)
    ├── 2_2.jpg     (第2行第2张图)
    └── 3_1.jpg     (第3行第1张图)</pre>
                  <p><strong>Excel 表头：</strong>厂区代码 | 线别代码 | 站别代码 | IP地址 | 防毒状态 | 入域状态 | 备注 | 图片数量</p>
                  <p><strong>图片命名：</strong><code>行号_序号.jpg</code>（例如 <code>2_1.jpg</code> = 第2行第1张图）</p>
                </div>
              </template>
            </el-alert>

            <div class="batch-upload-row">
              <el-button type="primary" @click="triggerBatchInput" :loading="batchLoading">
                <el-icon><Upload /></el-icon> 选择 ZIP 文件
              </el-button>
              <input
                class="batch-file-input"
                type="file"
                accept=".zip"
                style="display: none"
                @change="handleBatchFileChange"
              />
              <el-button type="success" plain @click="downloadBatchTemplate">
                <el-icon><Download /></el-icon> 下载使用说明
              </el-button>
              <span v-if="batchFile" class="file-name">已选择：{{ batchFile.name }}</span>
            </div>

            <el-button
              v-if="batchFile"
              type="primary"
              :loading="batchLoading"
              size="large"
              style="margin-top: 16px"
              @click="handleBatchImport"
            >
              确认批量导入
            </el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.inspection-form-page {
  padding: 16px;
}
.page-header {
  font-size: 18px;
  font-weight: 600;
}
.batch-import-area {
  padding: 16px 0;
}
.batch-upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.file-name {
  color: #409eff;
  font-size: 13px;
}
</style>