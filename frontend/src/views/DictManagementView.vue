<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getPlantDictTree, importDict } from '@/api/inspection'
import { ElMessage } from 'element-plus'
import { Upload, Download } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'

const treeData = ref<any[]>([])
const treeLoading = ref(false)
const uploadLoading = ref(false)
const previewData = ref<any[]>([])
const previewShow = ref(false)
const pendingFile = ref<File | null>(null)

const columnLabels = ['厂区代码', '厂区名称', '线别代码', '线别名称', '站别代码', '站别名称']

const triggerFileSelect = () => {
  const input = document.querySelector('.hidden-file-input') as HTMLInputElement
  if (input) input.click()
}

// 加载树形字典
const loadTree = async () => {
  treeLoading.value = true
  try {
    const res = await getPlantDictTree()
    treeData.value = res
  } finally {
    treeLoading.value = false
  }
}

// 解析 Excel 预览（使用 xlsx 库）
const handleFileChange = (file: File) => {
  pendingFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target?.result as ArrayBuffer)
      const workbook = XLSX.read(data, { type: 'array' })
      const sheet = workbook.Sheets[workbook.SheetNames[0]]
      const jsonData: any[][] = XLSX.utils.sheet_to_json(sheet, { header: 1 })

      if (jsonData.length < 2) {
        ElMessage.warning('Excel 文件中没有数据')
        return
      }

      previewData.value = jsonData.slice(1)
        .filter((row: any[]) => row.some((cell: any) => cell !== undefined && cell !== null && cell !== ''))
        .map((row: any[]) => ({
          plant_code: row[0]?.toString().trim() || '',
          plant_name: row[1]?.toString().trim() || '',
          line_code: row[2]?.toString().trim() || '',
          line_name: row[3]?.toString().trim() || '',
          station_code: row[4]?.toString().trim() || '',
          station_name: row[5]?.toString().trim() || '',
        }))

      previewShow.value = true
    } catch (err: any) {
      ElMessage.error('解析 Excel 失败：' + err.message)
    }
  }
  reader.readAsArrayBuffer(file)
}

// 执行导入
const handleImport = async () => {
  if (!pendingFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploadLoading.value = true
  try {
    const res: any = await importDict(pendingFile.value)
    ElMessage.success(res.message || '导入成功')
    cancelPreview()
    await loadTree()
  } catch {
    ElMessage.error('导入失败')
  } finally {
    uploadLoading.value = false
  }
}

// 取消预览
const cancelPreview = () => {
  previewShow.value = false
  previewData.value = []
  pendingFile.value = null
}

// 下载模板
const downloadTemplate = () => {
  const headers = columnLabels
  const sampleData = [
    ['F1', '一厂', 'A01', 'SMT线', 'S01', 'AOI站'],
    ['F1', '一厂', 'A01', 'SMT线', 'S02', '贴片站'],
    ['F1', '一厂', 'A02', '组装线', 'S03', '焊接站'],
    ['F2', '二厂', 'B01', '包装线', 'S04', '检验站'],
  ]

  const ws = XLSX.utils.aoa_to_sheet([headers, ...sampleData])
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
  ws['!cols'] = columnLabels.map(() => ({ wch: 14 }))
  XLSX.writeFile(wb, '厂区字典导入模板.xlsx')
}

onMounted(() => {
  loadTree()
})
</script>

<template>
  <div class="dict-management-page">
    <el-card>
      <template #header>
        <div class="page-header">厂区字典管理</div>
      </template>

      <!-- 上传区域 -->
      <div class="upload-area">
        <el-button type="primary" :loading="uploadLoading" @click="triggerFileSelect">
          <el-icon><Upload /></el-icon> 选择 Excel 文件
        </el-button>
        <input
          class="hidden-file-input"
          type="file"
          accept=".xlsx,.xls"
          style="display: none"
          @change="(e: Event) => {
            const target = e.target as HTMLInputElement
            const file = target.files?.[0]
            if (file) handleFileChange(file)
          }"
        />
        <span class="upload-tip">支持 .xlsx / .xls 格式，表头：厂区代码 | 厂区名称 | 线别代码 | 线别名称 | 站别代码 | 站别名称</span>
        <el-button type="success" plain @click="downloadTemplate">
          <el-icon><Download /></el-icon> 下载导入模板
        </el-button>
        <span v-if="pendingFile" class="file-name">已选择：{{ pendingFile.name }}</span>
      </div>

      <!-- 预览表格 -->
      <div v-if="previewShow && previewData.length > 0" class="preview-section">
        <h4>预览数据（共 {{ previewData.length }} 行）</h4>
        <el-table :data="previewData" border stripe max-height="400" size="small">
          <el-table-column prop="plant_code" label="厂区代码" width="120" />
          <el-table-column prop="plant_name" label="厂区名称" width="140" />
          <el-table-column prop="line_code" label="线别代码" width="120" />
          <el-table-column prop="line_name" label="线别名称" width="140" />
          <el-table-column prop="station_code" label="站别代码" width="120" />
          <el-table-column prop="station_name" label="站别名称" width="140" />
        </el-table>
        <div class="preview-actions">
          <el-button type="primary" :loading="uploadLoading" @click="handleImport">确认导入</el-button>
          <el-button @click="cancelPreview">取消</el-button>
        </div>
      </div>

      <!-- 现有字典树 -->
      <h4>已有厂区字典</h4>
      <div v-loading="treeLoading">
        <el-collapse v-if="treeData.length > 0" accordion>
          <el-collapse-item
            v-for="plant in treeData"
            :key="plant.id"
            :title="`${plant.code} - ${plant.name}`"
          >
            <div class="dict-level">
              <div v-for="line in plant.children" :key="line.id" class="line-item">
                <strong>{{ line.code }} - {{ line.name }}</strong>
                <div v-if="line.children && line.children.length > 0" class="station-list">
                  <el-tag
                    v-for="station in line.children"
                    :key="station.id"
                    size="small"
                    class="station-tag"
                  >
                    {{ station.code }} - {{ station.name }}
                  </el-tag>
                </div>
                <span v-else class="no-data">无站别</span>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
        <el-empty v-else description="暂无数据，请导入" />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.dict-management-page {
  padding: 16px;
}
.page-header {
  font-size: 18px;
  font-weight: 600;
}
.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.upload-tip {
  color: #999;
  font-size: 13px;
}
.file-name {
  color: #409eff;
  font-size: 13px;
}
.preview-section {
  margin: 20px 0;
}
.preview-section h4 {
  margin-bottom: 10px;
}
.preview-actions {
  margin-top: 12px;
  display: flex;
  gap: 12px;
}
.dict-level {
  padding: 8px 16px;
}
.line-item {
  margin-bottom: 12px;
}
.line-item strong {
  display: block;
  margin-bottom: 4px;
}
.station-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-left: 16px;
}
.station-tag {
  margin-bottom: 0;
}
.no-data {
  color: #ccc;
  font-size: 13px;
  margin-left: 16px;
}
</style>