import axios from 'axios'
import request from './request'

export const getPlantDictTree = (): Promise<any[]> => request.get('/dict/tree')

export const createInspection = (data: any) => request.post('/inspections', data)

export const getInspectionList = (params: any) => request.get('/inspections', { params })

export const uploadImage = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/inspections/upload', formData)
}

export const importDict = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/dict/import', formData)
}

export const batchImportInspections = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/inspections/batch-import', formData)
}

// 厂区字典增删改查
export const createPlant = (data: any) => request.post('/dict/plant', data)
export const updatePlant = (id: string, data: any) => request.put(`/dict/plant/${id}`, data)
export const deletePlant = (id: string) => request.delete(`/dict/plant/${id}`)
export const createLine = (data: any) => request.post('/dict/line', data)
export const updateLine = (id: string, data: any) => request.put(`/dict/line/${id}`, data)
export const deleteLine = (id: string) => request.delete(`/dict/line/${id}`)
export const createStation = (data: any) => request.post('/dict/station', data)
export const updateStation = (id: string, data: any) => request.put(`/dict/station/${id}`, data)
export const deleteStation = (id: string) => request.delete(`/dict/station/${id}`)

export const exportInspections = async (params: any) => {
  const response = await axios.get('/api/v1/inspections/export', {
    params,
    responseType: 'blob',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`
    }
  })
  // 从 Content-Disposition 头获取文件名
  const disposition = response.headers['content-disposition']
  let filename = '巡检记录.xlsx'
  if (disposition) {
    const match = disposition.match(/filename\*=UTF-8''(.+)/)
    if (match) {
      filename = decodeURIComponent(match[1])
    }
  }
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}