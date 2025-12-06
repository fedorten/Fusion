<template>
  <div class="home-container">
    <header class="header">
      <h1>Fusion</h1>
      <div class="header-actions">
        <router-link to="/profile" class="profile-link">Профиль</router-link>
        <button @click="handleLogout" class="logout-btn">Выйти</button>
      </div>
    </header>

    <div class="content">
      <div class="search-section">
        <div class="section-header">
          <h2>Поиск пользователей</h2>
          <button @click="showCreateGroup = true" class="create-group-btn" title="Создать групповой чат">
            <span>+</span> Группа
          </button>
        </div>
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Введите email или имя..."
            @input="handleSearch"
          />
          <div v-if="searching" class="loading">Поиск...</div>
          <div v-if="searchResults.length > 0" class="search-results">
            <div
              v-for="user in searchResults"
              :key="user.id"
              class="user-item"
              @click="startChat(user)"
            >
              <div class="user-info">
                <strong>{{ user.full_name || user.email }}</strong>
                <span class="user-email">{{ user.email }}</span>
              </div>
              <button class="chat-btn">Написать</button>
            </div>
          </div>
          <div v-if="searchQuery && !searching && searchResults.length === 0" class="no-results">
            Пользователи не найдены
          </div>
        </div>
      </div>

      <div class="chats-section">
        <h2>Мои чаты</h2>
        <div v-if="loadingChats" class="loading">Загрузка чатов...</div>
        <div v-else-if="chats.length === 0" class="no-chats">
          У вас пока нет чатов. Найдите пользователя и начните переписку!
        </div>
        <div v-else class="chats-list">
          <div
            v-for="chat in chats"
            :key="chat.id"
            class="chat-item"
            :class="{ 'group-chat': chat.chat_type === 'group' }"
            @click="openChat(chat.id)"
          >
            <div class="chat-info">
              <div class="chat-name-row">
                <strong>{{ getChatName(chat) }}</strong>
                <span v-if="chat.chat_type === 'group'" class="group-badge">Группа</span>
              </div>
              <span v-if="chat.last_message" class="last-message">
                {{ chat.last_message.content }}
              </span>
            </div>
            <span v-if="chat.last_message" class="chat-time">
              {{ formatTime(chat.last_message.created_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно создания группового чата -->
    <div v-if="showCreateGroup" class="modal-overlay" @click.self="showCreateGroup = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Создать групповой чат</h3>
          <button @click="showCreateGroup = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Название группы:</label>
            <input
              v-model="newGroupName"
              type="text"
              placeholder="Введите название группы"
              maxlength="50"
            />
          </div>
          <div class="form-group">
            <label>Поиск участников:</label>
            <input
              v-model="groupMemberSearch"
              type="text"
              placeholder="Начните вводить имя или email..."
              @input="handleGroupMemberSearch"
            />
            <div v-if="groupSearchResults.length > 0" class="member-search-results">
              <div
                v-for="user in groupSearchResults"
                :key="user.id"
                class="member-item"
                @click="toggleGroupMember(user)"
              >
                <div class="member-info">
                  <strong>{{ user.full_name || user.email }}</strong>
                  <span class="member-email">{{ user.email }}</span>
                </div>
                <div class="checkbox" :class="{ checked: isMemberSelected(user.id) }">
                  {{ isMemberSelected(user.id) ? '✓' : '' }}
                </div>
              </div>
            </div>
          </div>
          <div v-if="selectedMembers.length > 0" class="selected-members">
            <div class="selected-label">Выбранные участники ({{ selectedMembers.length }}):</div>
            <div class="selected-tags">
              <span
                v-for="member in selectedMembers"
                :key="member.id"
                class="member-tag"
              >
                {{ member.full_name || member.email }}
                <button @click="removeMember(member.id)" class="remove-member">×</button>
              </span>
            </div>
          </div>
          <div v-if="groupError" class="error">{{ groupError }}</div>
        </div>
        <div class="modal-footer">
          <button @click="showCreateGroup = false" class="cancel-btn">Отмена</button>
          <button
            @click="createGroupChat"
            :disabled="!newGroupName.trim() || selectedMembers.length === 0 || creatingGroup"
            class="create-btn"
          >
            {{ creatingGroup ? 'Создание...' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usersAPI, chatsAPI } from '../services/api'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    const searchQuery = ref('')
    const searchResults = ref([])
    const searching = ref(false)
    const chats = ref([])
    const loadingChats = ref(false)
    const currentUser = ref(null)
    const showCreateGroup = ref(false)
    const newGroupName = ref('')
    const groupMemberSearch = ref('')
    const groupSearchResults = ref([])
    const selectedMembers = ref([])
    const creatingGroup = ref(false)
    const groupError = ref('')

    const handleSearch = async () => {
      if (!searchQuery.value.trim()) {
        searchResults.value = []
        return
      }

      searching.value = true
      try {
        const response = await usersAPI.search(searchQuery.value)
        searchResults.value = response.data || []
      } catch (error) {
        console.error('Search error:', error)
        searchResults.value = []
      } finally {
        searching.value = false
      }
    }

    const startChat = async (user) => {
      try {
        const chat = await chatsAPI.createPrivateChat(user.id)
        router.push(`/chat/${chat.id}`)
      } catch (error) {
        console.error('Error creating chat:', error)
        alert('Ошибка создания чата')
      }
    }

    const openChat = (chatId) => {
      router.push(`/chat/${chatId}`)
    }

    const getChatName = (chat) => {
      if (chat.name) return chat.name
      if (chat.members && chat.members.length > 0) {
        const otherMember = chat.members.find(m => m.user_id !== currentUser.value?.id)
        if (otherMember) {
          return otherMember.user?.full_name || otherMember.user?.email || 'Пользователь'
        }
      }
      return 'Чат'
    }

    const formatTime = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      const diff = now - date
      const minutes = Math.floor(diff / 60000)
      
      if (minutes < 1) return 'только что'
      if (minutes < 60) return `${minutes} мин назад`
      const hours = Math.floor(minutes / 60)
      if (hours < 24) return `${hours} ч назад`
      return date.toLocaleDateString()
    }

    const loadChats = async () => {
      loadingChats.value = true
      try {
        const response = await chatsAPI.getChats()
        chats.value = response.data || []
        // Сортируем по времени последнего сообщения
        chats.value.sort((a, b) => {
          const timeA = a.last_message?.created_at || a.updated_at
          const timeB = b.last_message?.created_at || b.updated_at
          return new Date(timeB) - new Date(timeA)
        })
      } catch (error) {
        console.error('Error loading chats:', error)
      } finally {
        loadingChats.value = false
      }
    }

    const handleGroupMemberSearch = async () => {
      if (!groupMemberSearch.value.trim()) {
        groupSearchResults.value = []
        return
      }
      try {
        const response = await usersAPI.search(groupMemberSearch.value)
        // Исключаем текущего пользователя и уже выбранных
        const excludeIds = [currentUser.value?.id, ...selectedMembers.value.map(m => m.id)].filter(Boolean)
        groupSearchResults.value = (response.data || []).filter(u => !excludeIds.includes(u.id))
      } catch (error) {
        console.error('Group member search error:', error)
        groupSearchResults.value = []
      }
    }

    const toggleGroupMember = (user) => {
      const index = selectedMembers.value.findIndex(m => m.id === user.id)
      if (index === -1) {
        selectedMembers.value.push(user)
      } else {
        selectedMembers.value.splice(index, 1)
      }
    }

    const isMemberSelected = (userId) => {
      return selectedMembers.value.some(m => m.id === userId)
    }

    const removeMember = (userId) => {
      const index = selectedMembers.value.findIndex(m => m.id === userId)
      if (index !== -1) {
        selectedMembers.value.splice(index, 1)
      }
    }

    const createGroupChat = async () => {
      if (!newGroupName.value.trim() || selectedMembers.value.length === 0) {
        groupError.value = 'Заполните название и выберите хотя бы одного участника'
        return
      }

      creatingGroup.value = true
      groupError.value = ''

      try {
        const memberIds = selectedMembers.value.map(m => m.id)
        const chat = await chatsAPI.createGroupChat(newGroupName.value, memberIds)
        
        // Сброс формы
        showCreateGroup.value = false
        newGroupName.value = ''
        groupMemberSearch.value = ''
        groupSearchResults.value = []
        selectedMembers.value = []
        
        // Обновляем список чатов и переходим в новый чат
        await loadChats()
        router.push(`/chat/${chat.id}`)
      } catch (error) {
        console.error('Error creating group chat:', error)
        groupError.value = error.response?.data?.detail || 'Ошибка создания группового чата'
      } finally {
        creatingGroup.value = false
      }
    }

    const handleLogout = () => {
      localStorage.removeItem('access_token')
      router.push('/login')
    }

    onMounted(async () => {
      try {
        const { authAPI } = await import('../services/api')
        currentUser.value = await authAPI.getCurrentUser()
      } catch (error) {
        console.error('Error loading user:', error)
      }
      await loadChats()
    })

    return {
      searchQuery,
      searchResults,
      searching,
      chats,
      loadingChats,
      showCreateGroup,
      newGroupName,
      groupMemberSearch,
      groupSearchResults,
      selectedMembers,
      creatingGroup,
      groupError,
      handleSearch,
      startChat,
      openChat,
      getChatName,
      formatTime,
      handleGroupMemberSearch,
      toggleGroupMember,
      isMemberSelected,
      removeMember,
      createGroupChat,
      handleLogout,
    }
  },
}
</script>

<style scoped>
.home-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem;
  min-height: 100vh;
  background: var(--bg-dark);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: var(--bg-card);
  border-radius: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
}

.header h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.75rem;
  font-weight: 700;
  background: linear-gradient(135deg, #9333ea 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.profile-link {
  color: var(--primary-purple-light);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.profile-link:hover {
  color: var(--primary-purple);
  text-decoration: underline;
}

.logout-btn {
  padding: 0.625rem 1.25rem;
  background: rgba(239, 68, 68, 0.2);
  color: var(--error);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  border-color: var(--error);
}

.content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.search-section,
.chats-section {
  background: var(--bg-card);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
}

.create-group-btn {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  box-shadow: 0 2px 10px rgba(147, 51, 234, 0.3);
}

.create-group-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
}

.create-group-btn span {
  font-size: 1.2rem;
  font-weight: 700;
}

.search-box input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 1rem;
  box-sizing: border-box;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.search-box input::placeholder {
  color: var(--text-muted);
}

.search-box input:focus {
  outline: none;
  border-color: var(--primary-purple);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
  background: rgba(10, 10, 10, 0.7);
}

.search-results {
  margin-top: 1rem;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(10, 10, 10, 0.3);
}

.user-item:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
  transform: translateX(4px);
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-info strong {
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.user-email {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.chat-btn {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.3s ease;
}

.chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(147, 51, 234, 0.4);
}

.chats-list {
  max-height: 600px;
  overflow-y: auto;
}

.chat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(10, 10, 10, 0.3);
}

.chat-item:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
  transform: translateX(4px);
}

.chat-item.group-chat {
  border-left: 3px solid var(--primary-purple);
}

.chat-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.chat-name-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.chat-name-row strong {
  color: var(--text-primary);
}

.group-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  background: rgba(147, 51, 234, 0.2);
  color: var(--primary-purple-light);
  border-radius: 4px;
  font-weight: 500;
}

.last-message {
  font-size: 0.875rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}

.chat-time {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.loading,
.no-results,
.no-chats {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

/* Модальное окно */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: var(--bg-card);
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(147, 51, 234, 0.3);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 2rem;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
  flex: 1;
}

.modal-body .form-group {
  margin-bottom: 1.5rem;
}

.modal-body label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.9rem;
}

.modal-body input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 1rem;
  box-sizing: border-box;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.modal-body input:focus {
  outline: none;
  border-color: var(--primary-purple);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
}

.member-search-results {
  margin-top: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: rgba(10, 10, 10, 0.5);
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.3s ease;
  border-bottom: 1px solid var(--border-color);
}

.member-item:last-child {
  border-bottom: none;
}

.member-item:hover {
  background: var(--bg-card-hover);
}

.member-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.member-info strong {
  color: var(--text-primary);
  font-size: 0.9rem;
}

.member-email {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.checkbox {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  font-weight: 700;
  transition: all 0.3s ease;
}

.checkbox.checked {
  background: var(--primary-purple);
  border-color: var(--primary-purple);
}

.selected-members {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.selected-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.member-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(147, 51, 234, 0.2);
  color: var(--primary-purple-light);
  border-radius: 6px;
  font-size: 0.875rem;
}

.remove-member {
  background: none;
  border: none;
  color: var(--primary-purple-light);
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.remove-member:hover {
  background: rgba(147, 51, 234, 0.3);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
}

.cancel-btn,
.create-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn {
  background: var(--bg-card-hover);
  color: var(--text-secondary);
}

.cancel-btn:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.create-btn {
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
}

.create-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(147, 51, 234, 0.5);
}

.create-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 768px) {
  .content {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    max-width: 100%;
    margin: 1rem;
  }
}
</style>

