// 巡检/异常状态中文映射
export const STATUS_LABEL_MAP: Record<string, string> = {
  NORMAL: '正常',
  ABNORMAL: '异常',
  NOT_INSTALLED: '未安装',
  JOINED: '已入域',
  NOT_JOINED: '未入域',
  NOT_APPLICABLE: '不适用',
}

// 异常工单状态
export const EXCEPTION_STATUS_MAP: Record<string, { label: string; type: string }> = {
  PENDING: { label: '待分配', type: 'info' },
  PROCESSING: { label: '处理中', type: 'warning' },
  PENDING_SIGNOFF: { label: '待签核', type: 'primary' },
  CLOSED: { label: '已结案', type: 'success' },
  REJECTED: { label: '已驳回', type: 'danger' },
}
