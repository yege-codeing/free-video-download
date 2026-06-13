async function authRequest(path, options = {}) {
  let response
  try {
    response = await fetch(`/api${path}`, {
      credentials: 'include',
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new Error('无法连接后端，请确认服务已启动')
  }

  let data
  try {
    data = await response.json()
  } catch {
    if (response.status === 404) {
      throw new Error('认证接口不可用，请重启后端服务')
    }
    throw new Error('验证码加载失败')
  }

  if (response.status === 404) {
    throw new Error('认证接口不可用，请重启后端服务')
  }

  if (!response.ok && data?.code === undefined) {
    throw new Error(data?.detail || data?.message || '请求失败')
  }

  return data
}

export async function getCaptcha() {
  const data = await authRequest('/auth/captcha')
  if (data.code !== 0) {
    throw new Error(data.message || '验证码加载失败')
  }
  return data.data
}

export async function login({ username, password, captcha }) {
  const data = await authRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password, captcha }),
  })
  if (data.code !== 0) {
    throw new Error(data.message || '登录失败')
  }
  return data.data
}

export async function logout() {
  try {
    await authRequest('/auth/logout', { method: 'POST' })
  } catch {
    /* ignore network errors on logout */
  }
}

export async function getMe() {
  const data = await authRequest('/auth/me')
  return data.data
}
