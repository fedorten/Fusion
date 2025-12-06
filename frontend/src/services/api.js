import axios from 'axios'

const API_BASE_URL = '/api/v1'

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Интерцептор для добавления токена к запросам
api.interceptors.request.use(
  (config) => {
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

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API методы
export const authAPI = {
  login: async (email, password) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    const response = await axios.post(`${API_BASE_URL}/login/access-token`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  
  register: async (email, password, fullName) => {
    const response = await api.post('/users/signup', {
      email,
      password,
      full_name: fullName || null,
    })
    return response.data
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/users/me')
    return response.data
  },
  
  deleteAccount: async () => {
    const response = await api.delete('/users/me')
    return response.data
  },
}

export const usersAPI = {
  search: async (query) => {
    const response = await api.get('/users/search', { params: { query } })
    return response.data
  },
}

export const chatsAPI = {
  getChats: async () => {
    const response = await api.get('/chats/')
    return response.data
  },
  
  getChat: async (chatId) => {
    const response = await api.get(`/chats/${chatId}`)
    return response.data
  },
  
  createPrivateChat: async (userId) => {
    const response = await api.post(`/chats/private/${userId}`)
    return response.data
  },
  
  createGroupChat: async (name, memberIds) => {
    const response = await api.post('/chats/group', {
      chat_type: 'group',
      name: name,
      member_ids: memberIds,
    })
    return response.data
  },
  
  addMembersToGroup: async (chatId, memberIds) => {
    const response = await api.post(`/chats/${chatId}/members`, {
      member_ids: memberIds,
    })
    return response.data
  },
  
  getMessages: async (chatId, skip = 0, limit = 50) => {
    const response = await api.get(`/chats/${chatId}/messages`, {
      params: { skip, limit },
    })
    return response.data
  },
}

export const messagesAPI = {
  sendMessage: async (chatId, content) => {
    const response = await api.post(`/messages/${chatId}`, { content })
    return response.data
  },
}

export default api

