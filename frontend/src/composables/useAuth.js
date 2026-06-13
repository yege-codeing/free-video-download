import * as authApi from '../api/auth.js'
import {
  isAuthenticated,
  username,
  authEnabled,
  checking,
  sessionMessage,
  setAuthenticated,
  clearAuthenticated,
} from './authState.js'

export { onUnauthorized } from './authState.js'

export function useAuth() {
  async function checkAuth() {
    checking.value = true
    try {
      const data = await authApi.getMe()
      authEnabled.value = data.auth_enabled !== false
      if (data.authenticated) {
        setAuthenticated(data.username)
      } else {
        clearAuthenticated()
      }
    } catch {
      authEnabled.value = true
      clearAuthenticated()
    } finally {
      checking.value = false
    }
  }

  async function login(form) {
    sessionMessage.value = ''
    const data = await authApi.login(form)
    setAuthenticated(data.username || form.username)
    return data
  }

  async function logout() {
    await authApi.logout()
    clearAuthenticated()
  }

  return {
    isAuthenticated,
    username,
    authEnabled,
    checking,
    sessionMessage,
    checkAuth,
    login,
    logout,
  }
}
