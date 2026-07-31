import request from './request'

export const getPlantDictTree = (): Promise<any[]> => request.get('/dict/tree')

export const createInspection = (data: any) => request.post('/inspections', data)

export const getInspectionList = (params: any) => request.get('/inspections', { params })

export const uploadImage = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/inspections/upload', formData)
}
