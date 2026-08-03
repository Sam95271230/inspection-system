<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  getPlantDictTree,
  importDict,
  createPlant,
  updatePlant,
  deletePlant,
  createLine,
  updateLine,
  deleteLine,
  createStation,
  updateStation,
  deleteStation,
} from '@/api/inspection'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Download, Edit, Delete, Plus } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'

const treeData = ref<any[]>([])
const treeLoading = ref(false)
const uploadLoading = ref(false)
const previewData = ref<any[]>([])
const previewShow = ref(false)
const pendingFile = ref<File | null>(null)

const columnLabels = ['厂区代码', '厂区名称', '线别代码', '线别名称', '站别代码', '站别名称']

// ─────── 新增 / 编辑弹窗 ───────
const dialogVisible = ref(false)
const dialogType = ref<'plant' | 'line' | 'station'>('plant')
const isCreate = ref(false)
const dialogId = ref('')
const dialogParentId = ref('')  // 新增线别/站别时的父级 ID
const dialogParentLabel = ref('')
const dialogForm = reactive({ code: '', name: '' })
const dialogSaving = ref(false)

const dialogTitle = () => {
  const typeMap: Record<string, string> = { plant: '厂区', line: '线别', station: '站别' }
  const prefix = isCreate.value ? '新增' : '编辑'
  return prefix + typeMap[dialogType.value]
}

// ── 新增 ──
const openCreatePlant = () => {
  dialogType.value = 'plant'; isCreate.value = true
  dialogId.value = ''; dialogParentId.value = ''; dialogParentLabel.value = ''
  dialogForm.code = ''; dialogForm.name = ''
  dialogVisible.value = true
}
const openCreateLine = (plantId: string, plantLabel: string) => {
  dialogType.value = 'line'; isCreate.value = true
  dialogId.value = ''; dialogParentId.value = plantId; dialogParentLabel.value = plantLabel
  dialogForm.code = ''; dialogForm.name = ''
  dialogVisible.value = true
}
const openCreateStation = (lineId: string, lineLabel: string) => {
  dialogType.value = 'station'; isCreate.value = true
  dialogId.value = ''; dialogParentId.value = lineId; dialogParentLabel.value = lineLabel
  dialogForm.code = ''; dialogForm.name = ''
  dialogVisible.value = true
}

// ── 编辑 ──
const openEditPlant = (plant: any) => {
  dialogType.value = 'plant'; isCreate.value = false
  dialogId.value = plant.id; dialogParentId.value = ''; dialogParentLabel.value = ''
  dialogForm.code = plant.code; dialogForm.name = plant.name
  dialogVisible.value = true
}
const openEditLine = (line: any, plantName: string) => {
  dialogType.value = 'line'; isCreate.value = false
  dialogId.value = line.id; dialogParentId.value = ''; dialogParentLabel.value = plantName
  dialogForm.code = line.code; dialogForm.name = line.name
  dialogVisible.value = true
}
const openEditStation = (station: any, lineName: string) => {
  dialogType.value = 'station'; isCreate.value = false
  dialogId.value = station.id; dialogParentId.value = ''; dialogParentLabel.value = lineName
  dialogForm.code = station.code; dialogForm.name = station.name
  dialogVisible.value = true
}

const handleDialogSave = async () => {
  if (!dialogForm.code || !dialogForm.name) {
    ElMessage.error('代码和名称不能为空')
    return
  }
  dialogSaving.value = true
  try {
    const payload = { code: dialogForm.code, name: dialogForm.name }
    if (isCreate.value) {
      if (dialogType.value === 'plant') {
        await createPlant(payload)
      } else if (dialogType.value === 'line') {
        await createLine({ ...payload, plant_id: dialogParentId.value })
      } else {
        await createStation({ ...payload, line_id: dialogParentId.value })
      }
    } else {
      if (dialogType.value === 'plant') {
        await updatePlant(dialogId.value, payload)
      } else if (dialogType.value === 'line') {
        await updateLine(dialogId.value, payload)
      } else {
        await updateStation(dialogId.value, payload)
      }
    }
    ElMessage.success(isCreate.value ? '新增成功' : '修改成功')
    dialogVisible.value = false
    await loadTree()
  } catch {
    // error handled by interceptor
  } finally {
    dialogSaving.value = false
  }
}

// ─────── 删除确认 ───────
const handleDeletePlant = async (plant: any) => {
  try {
    await ElMessageBox.confirm(
      `确认删除厂区 "${plant.code} - ${plant.name}" 吗？其下的线别和站别也将一并删除。`,
      '删除厂区',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deletePlant(plant.id)
    ElMessage.success('删除成功')
    await loadTree()
  } catch (e: any) {
    if (e !== 'cancel') { /* error handled by interceptor */ }
  }
}

const handleDeleteLine = async (line: any) => {
  try {
    await ElMessageBox.confirm(
      `确认删除线别 "${line.code} - ${line.name}" 吗？其下的站别也将一并删除。`,
      '删除线别',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteLine(line.id)
    ElMessage.success('删除成功')
    await loadTree()
  } catch (e: any) {
    if (e !== 'cancel') { /* error handled by interceptor */ }
  }
}

const handleDeleteStation = async (station: any) => {
  try {
    await ElMessageBox.confirm(
      `确认删除站别 "${station.code} - ${station.name}" 吗？`,
      '删除站别',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteStation(station.id)
    ElMessage.success('删除成功')
    await loadTree()
  } catch (e: any) {
    if (e !== 'cancel') { /* error handled by interceptor */ }
  }
}

// ─────── 文件导入（原有）───────
const triggerFileSelect = () => {
  const input = document.querySelector('.hidden-file-input') as HTMLInputElement
  if (input) input.click()
}

const loadTree = async () => {
  treeLoading.value = true
  try {
    const res = await getPlantDictTree()
    treeData.value = res
  } finally {
    treeLoading.value = false
  }
}

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

const cancelPreview = () => {
  previewShow.value = false
  previewData.value = []
  pendingFile.value = null
}

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

      <!-- 上传区域（原有） -->
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

      <!-- 预览表格（原有） -->
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

      <!-- 已有字典树 -->
      <div class="tree-header">
        <h4>已有厂区字典</h4>
        <el-button type="primary" size="small" :icon="Plus" @click="openCreatePlant">新增厂区</el-button>
      </div>
      <div v-loading="treeLoading">
        <div v-if="treeData.length > 0" class="dict-tree">
          <div v-for="plant in treeData" :key="plant.id" class="dict-plant">
            <div class="dict-item plant-item">
              <div class="item-info">
                <span class="item-code">{{ plant.code }}</span>
                <span class="item-sep">-</span>
                <span class="item-name">{{ plant.name }}</span>
                <el-tag size="small" type="success" class="item-type">厂区</el-tag>
              </div>
              <div class="item-actions">
                <el-button type="success" link size="small" :icon="Plus" @click="openCreateLine(plant.id, plant.code + ' - ' + plant.name)">新增线别</el-button>
                <el-button type="primary" link size="small" :icon="Edit" @click="openEditPlant(plant)">编辑</el-button>
                <el-button type="danger" link size="small" :icon="Delete" @click="handleDeletePlant(plant)">删除</el-button>
              </div>
            </div>

            <!-- 线别 -->
            <div v-if="plant.children && plant.children.length" class="dict-lines">
              <div v-for="line in plant.children" :key="line.id" class="dict-line">
                <div class="dict-item line-item">
                  <div class="item-info">
                    <span class="item-code">{{ line.code }}</span>
                    <span class="item-sep">-</span>
                    <span class="item-name">{{ line.name }}</span>
                    <el-tag size="small" type="warning" class="item-type">线别</el-tag>
                  </div>
                  <div class="item-actions">
                    <el-button type="success" link size="small" :icon="Plus" @click="openCreateStation(line.id, line.code + ' - ' + line.name)">新增站别</el-button>
                    <el-button type="primary" link size="small" :icon="Edit" @click="openEditLine(line, plant.code + ' - ' + plant.name)">编辑</el-button>
                    <el-button type="danger" link size="small" :icon="Delete" @click="handleDeleteLine(line)">删除</el-button>
                  </div>
                </div>

                <!-- 站别 -->
                <div v-if="line.children && line.children.length" class="dict-stations">
                  <div v-for="station in line.children" :key="station.id" class="dict-item station-item">
                    <div class="item-info">
                      <span class="item-code">{{ station.code }}</span>
                      <span class="item-sep">-</span>
                      <span class="item-name">{{ station.name }}</span>
                      <el-tag size="small" type="info" class="item-type">站别</el-tag>
                    </div>
                    <div class="item-actions">
                      <el-button type="primary" link size="small" :icon="Edit" @click="openEditStation(station, line.code + ' - ' + line.name)">编辑</el-button>
                      <el-button type="danger" link size="small" :icon="Delete" @click="handleDeleteStation(station)">删除</el-button>
                    </div>
                  </div>
                </div>
                <div v-else class="no-children">暂无站别</div>
              </div>
            </div>
            <div v-else class="no-children">暂无下属线别</div>
          </div>
        </div>
        <el-empty v-else description="暂无数据，请导入" />
      </div>
    </el-card>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle()" width="480px">
      <el-form :model="dialogForm" label-width="80px">
        <el-form-item v-if="dialogParentLabel" label="所属">
          <span class="parent-label">{{ dialogParentLabel }}</span>
        </el-form-item>
        <el-form-item label="代码">
          <el-input v-model="dialogForm.code" placeholder="请输入代码" />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="dialogForm.name" placeholder="请输入名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogSaving" @click="handleDialogSave">保存</el-button>
      </template>
    </el-dialog>
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

/* 树形字典 */
.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0 12px;
}
.tree-header h4 {
  margin: 0;
}
.dict-tree {
  margin-top: 12px;
}
.dict-plant {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}
.dict-lines {
  border-top: 1px solid #ebeef5;
  background: #fafafa;
}
.dict-line {
  border-bottom: 1px solid #ebeef5;
}
.dict-line:last-child {
  border-bottom: none;
}
.dict-stations {
  margin-left: 32px;
  border-top: 1px dashed #e4e7ed;
}
.dict-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  transition: background 0.15s;
}
.dict-item:hover {
  background: #f5f7fa;
}
.plant-item {
  background: #ecf5ff;
}
.line-item {
  background: #fdf6ec;
}
.station-item {
  padding-left: 32px;
}
.item-info {
  display: flex;
  align-items: center;
  gap: 6px;
}
.item-code {
  font-family: 'Consolas', 'Courier New', monospace;
  font-weight: 600;
  color: #303133;
}
.item-sep {
  color: #c0c4cc;
}
.item-name {
  color: #606266;
}
.item-type {
  margin-left: 6px;
  font-size: 11px;
}
.item-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.no-children {
  padding: 8px 16px 8px 48px;
  color: #c0c4cc;
  font-size: 13px;
}
.parent-label {
  color: #409eff;
  font-weight: 500;
}
</style>
