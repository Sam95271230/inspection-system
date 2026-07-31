<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadImage } from '@/api/inspection'

const props = defineProps<{
  modelValue: any[]
}>()

const emit = defineEmits(['update:modelValue'])

const uploading = ref(false)

const handleUpload = async (file: any) => {
  const rawFile = file.raw as File
  if (!rawFile.type.startsWith('image/')) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (rawFile.size > 5 * 1024 * 1024) {
    ElMessage.error('单张图片不能超过 5MB')
    return false
  }

  uploading.value = true
  try {
    const res = await uploadImage(rawFile)
    const list = [...props.modelValue, res]
    emit('update:modelValue', list)
    ElMessage.success('上传成功')
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
  return false
}

const removeImage = (index: number) => {
  const list = [...props.modelValue]
  list.splice(index, 1)
  emit('update:modelValue', list)
}
</script>

<template>
  <div>
    <el-upload
      :show-file-list="false"
      :auto-upload="false"
      :on-change="handleUpload"
      accept="image/*"
    >
      <el-button type="primary" :loading="uploading">上传/拍照</el-button>
    </el-upload>

    <div class="preview-list">
      <div
        v-for="(img, index) in modelValue"
        :key="index"
        class="preview-item"
      >
        <el-image :src="img.url" fit="cover" />
        <span class="delete-btn" @click="removeImage(index)">×</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}
.preview-item {
  width: 120px;
  height: 120px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}
.preview-item .el-image {
  width: 100%;
  height: 100%;
}
.delete-btn {
  position: absolute;
  top: 2px;
  right: 6px;
  color: #fff;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  cursor: pointer;
}
</style>
