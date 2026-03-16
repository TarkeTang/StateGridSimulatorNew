import axios from 'axios'

// 创建 Axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 处理错误响应
    if (error.response) {
      const { status, data } = error.response
      
      // 401 未授权
      if (status === 401) {
        localStorage.removeItem('access_token')
        window.location.href = '/login'
      }
      
      // 返回错误信息
      return Promise.reject(data || { message: '请求失败' })
    }
    
    return Promise.reject({ message: '网络错误' })
  }
)

export default api