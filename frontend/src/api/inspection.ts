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