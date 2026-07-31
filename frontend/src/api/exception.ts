import request from './request'

export const getExceptionList = (params: any) => request.get('/exceptions', { params })

export const getExceptionHistory = (ticketId: string) => request.get(`/exceptions/${ticketId}/history`)

export const assignException = (ticketId: string, data: any) => request.post(`/exceptions/${ticketId}/assign`, data)

export const processException = (ticketId: string, data: any) => request.post(`/exceptions/${ticketId}/process`, data)

export const approveException = (ticketId: string, data: any) => request.post(`/exceptions/${ticketId}/approve`, data)

export const rejectException = (ticketId: string, data: any) => request.post(`/exceptions/${ticketId}/reject`, data)

export const reprocessException = (ticketId: string, data: any) => request.post(`/exceptions/${ticketId}/reprocess`, data)