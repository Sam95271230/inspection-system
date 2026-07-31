<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getPlantDictTree, createInspection } from '@/api/inspection'
import ImageUploader from '@/components/ImageUploader.vue'

const loading = ref(false)
const plantOptions = ref<any[]>([])
const lineOptions = ref<any[]>([])
const stationOptions = ref<any[]>([])

const form = reactive({
  plant_id: '',
  line_id: '',
  station_id: '',
  ip_address: '',
  antivirus_status: 'NORMAL',
  domain_status: 'JOINED',
  remark: '',
  status: 'SUBMITTED',
  images: [] as any[]
})

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
</style>
