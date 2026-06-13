import axios from 'axios'
import { onUnauthorized } from '../composables/authState.js'

export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      onUnauthorized()
    }
    return Promise.reject(error)
  },
)

export function isUnauthorizedResponse(response) {
  return response?.status === 401
}
