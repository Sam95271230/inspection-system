import request from './request'

export const getEmailConfig = () => request.get('/email-config')

export const updateEmailConfig = (data: any) => request.put('/email-config', data)

export const testEmailConfig = (data: { to_email: string }) => request.post('/email-config/test', data)