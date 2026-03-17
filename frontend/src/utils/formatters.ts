/**
 * 格式化工具函数
 */

/**
 * 格式化 XML
 */
export const formatXml = (xml: string): string => {
  try {
    let formatted = ''
    let indent = ''
    const nodes = xml.replace(/>\s*</g, '><').split(/(<[^>]+>)/g)

    for (const node of nodes) {
      if (!node.trim()) continue

      if (node.startsWith('</')) {
        indent = indent.slice(2)
        formatted += indent + node + '\n'
      } else if (node.startsWith('<') && !node.startsWith('<?') && !node.endsWith('/>')) {
        formatted += indent + node + '\n'
        if (!node.includes('</')) {
          indent += '  '
        }
      } else if (node.startsWith('<?') || node.endsWith('/>')) {
        formatted += indent + node + '\n'
      } else {
        formatted += indent + node.trim() + '\n'
      }
    }

    return formatted.trim()
  } catch {
    return xml
  }
}

/**
 * 格式化 JSON
 */
export const formatJson = (json: string): string => {
  try {
    const obj = JSON.parse(json)
    return JSON.stringify(obj, null, 2)
  } catch {
    return json
  }
}

/**
 * 字符串转十六进制
 */
export const stringToHex = (str: string): string => {
  return str
    .split('')
    .map((char) => char.charCodeAt(0).toString(16).toUpperCase().padStart(2, '0'))
    .join(' ')
}

/**
 * 获取当前时间戳
 */
export const getTimestamp = (): string => {
  const now = new Date()
  return (
    now.toLocaleTimeString('zh-CN', { hour12: false }) +
    '.' +
    now.getMilliseconds().toString().padStart(3, '0')
  )
}

/**
 * 计算连接时长
 */
export const getConnectionDuration = (connectTime: string | null): string => {
  if (!connectTime) return '--'
  const start = new Date()
  const [h, m, s] = connectTime.split(':')
  start.setHours(parseInt(h), parseInt(m), parseInt(s))
  const now = new Date()
  const diff = Math.floor((now.getTime() - start.getTime()) / 1000)
  const hours = Math.floor(diff / 3600)
  const minutes = Math.floor((diff % 3600) / 60)
  const seconds = diff % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

/**
 * 获取状态样式
 */
export const getStatusStyle = (status: string): { color: string; label: string } => {
  switch (status) {
    case 'connected':
      return { color: 'text-signal-green', label: '已连接' }
    case 'connecting':
      return { color: 'text-signal-yellow', label: '连接中' }
    case 'reconnecting':
      return { color: 'text-signal-orange', label: '重连中' }
    case 'error':
      return { color: 'text-signal-red', label: '连接错误' }
    default:
      return { color: 'text-gray-400', label: '未连接' }
  }
}