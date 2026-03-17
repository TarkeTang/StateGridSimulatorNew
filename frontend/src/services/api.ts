import axios, { type AxiosRequestConfig } from 'axios'
import type { ApiResponse } from '@/types/api'

// 创建 Axios 实例
const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
axiosInstance.interceptors.request.use(
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
axiosInstance.interceptors.response.use(
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

// 封装 API 方法，返回正确的类型
const api = {
  get: <T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return axiosInstance.get(url, config) as Promise<ApiResponse<T>>
  },
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return axiosInstance.post(url, data, config) as Promise<ApiResponse<T>>
  },
  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return axiosInstance.put(url, data, config) as Promise<ApiResponse<T>>
  },
  delete: <T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return axiosInstance.delete(url, config) as Promise<ApiResponse<T>>
  },
}

export default api