<template>
  <div class="chat-container">
    <header class="chat-header">
      <button @click="goBack" class="back-btn">← Назад</button>
      <h2>{{ chatName }}</h2>
      <div class="header-actions">
        <button
          v-if="isGroupChat"
          @click="showAddMembers = true"
          class="add-members-btn"
          title="Добавить участников"
        >
          + Участники
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="chat-content">
      <div ref="messagesContainer" class="messages-container" @scroll="handleScroll">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message', { 'own-message': message.sender_id === currentUserId }]"
        >
          <div class="message-header">
            <strong>{{ getSenderName(message) }}</strong>
            <span class="message-time">{{ formatTime(message.created_at) }}</span>
          </div>
          <div class="message-content">{{ message.content }}</div>
        </div>
      </div>

      <div class="input-container">
        <input
          v-model="newMessage"
          type="text"
          placeholder="Введите сообщение..."
          @keyup.enter="sendMessage"
          @input="handleTyping"
        />
        <button @click="sendMessage" :disabled="!newMessage.trim()">
          Отправить
        </button>
      </div>
    </div>

    <!-- Модальное окно добавления участников -->
    <div v-if="showAddMembers" class="modal-overlay" @click.self="showAddMembers = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Добавить участников</h3>
          <button @click="showAddMembers = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Поиск пользователей:</label>
            <input
              v-model="memberSearchQuery"
              type="text"
              placeholder="Начните вводить имя или email..."
              @input="handleMemberSearch"
            />
            <div v-if="memberSearchResults.length > 0" class="member-search-results">
              <div
                v-for="user in memberSearchResults"
                :key="user.id"
                class="member-item"
                @click="toggleAddMember(user)"
              >
                <div class="member-info">
                  <strong>{{ user.full_name || user.email }}</strong>
                  <span class="member-email">{{ user.email }}</span>
                </div>
                <div class="checkbox" :class="{ checked: isAddMemberSelected(user.id) }">
                  {{ isAddMemberSelected(user.id) ? '✓' : '' }}
                </div>
              </div>
            </div>
          </div>
          <div v-if="membersToAdd.length > 0" class="selected-members">
            <div class="selected-label">Выбранные участники ({{ membersToAdd.length }}):</div>
            <div class="selected-tags">
              <span
                v-for="member in membersToAdd"
                :key="member.id"
                class="member-tag"
              >
                {{ member.full_name || member.email }}
                <button @click="removeAddMember(member.id)" class="remove-member">×</button>
              </span>
            </div>
          </div>
          <div v-if="addMemberError" class="error">{{ addMemberError }}</div>
        </div>
        <div class="modal-footer">
          <button @click="showAddMembers = false" class="cancel-btn">Отмена</button>
          <button
            @click="addMembersToGroup"
            :disabled="membersToAdd.length === 0 || addingMembers"
            class="create-btn"
          >
            {{ addingMembers ? 'Добавление...' : 'Добавить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { chatsAPI, messagesAPI, authAPI } from '../services/api'
import { ChatWebSocket } from '../services/websocket'

export default {
  name: 'Chat',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const chatId = parseInt(route.params.chatId)
    const messages = ref([])
    const loading = ref(true)
    const newMessage = ref('')
    const chatName = ref('Чат')
    const currentUserId = ref(null)
    const messagesContainer = ref(null)
    const ws = ref(null)
    const shouldAutoScroll = ref(true)
    const isGroupChat = ref(false)
    const showAddMembers = ref(false)
    const memberSearchQuery = ref('')
    const memberSearchResults = ref([])
    const membersToAdd = ref([])
    const addingMembers = ref(false)
    const addMemberError = ref('')
    const currentChat = ref(null)

    const loadChat = async () => {
      try {
        const chat = await chatsAPI.getChat(chatId)
        currentChat.value = chat
        chatName.value = getChatName(chat)
        isGroupChat.value = chat.chat_type === 'group'
      } catch (error) {
        console.error('Error loading chat:', error)
      }
    }

    const getChatName = (chat) => {
      if (chat.name) return chat.name
      if (chat.members && chat.members.length > 0) {
        const otherMember = chat.members.find(m => m.user_id !== currentUserId.value)
        if (otherMember) {
          return otherMember.user?.full_name || otherMember.user?.email || 'Пользователь'
        }
      }
      return 'Чат'
    }

    const loadMessages = async () => {
      try {
        const response = await chatsAPI.getMessages(chatId)
        messages.value = response.data || []
        // Устанавливаем флаг автоматической прокрутки
        shouldAutoScroll.value = true
      } catch (error) {
        console.error('Error loading messages:', error)
      } finally {
        loading.value = false
        // Прокручиваем вниз после того, как loading станет false и DOM обновится
        await nextTick()
        // Используем несколько попыток для надежной прокрутки
        setTimeout(() => {
          scrollToBottom(true)
        }, 100)
        setTimeout(() => {
          scrollToBottom(true)
        }, 300)
      }
    }

    const getSenderName = (message) => {
      if (message.sender_id === currentUserId.value) {
        return 'Вы'
      }
      return message.sender?.full_name || message.sender?.email || 'Пользователь'
    }

    const formatTime = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    }

    const scrollToBottom = async (force = false) => {
      if (!force && !shouldAutoScroll.value) return
      
      await nextTick()
      if (messagesContainer.value) {
        const container = messagesContainer.value
        // Используем несколько попыток для надежной прокрутки
        const scroll = () => {
          if (container) {
            const maxScroll = container.scrollHeight - container.clientHeight
            container.scrollTop = maxScroll > 0 ? maxScroll : container.scrollHeight
          }
        }
        // Прокручиваем сразу
        scroll()
        // И еще раз через небольшую задержку для надежности
        requestAnimationFrame(() => {
          scroll()
          // И еще раз после следующего кадра
          requestAnimationFrame(() => {
            scroll()
            // И еще раз для полной уверенности
            setTimeout(() => {
              scroll()
            }, 50)
          })
        })
      }
    }
    
    // Отслеживаем скролл, чтобы определить, нужно ли автоматически прокручивать
    const handleScroll = () => {
      if (!messagesContainer.value) return
      const container = messagesContainer.value
      const threshold = 100 // пикселей от низа
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < threshold
      shouldAutoScroll.value = isNearBottom
    }

    const sendMessage = async () => {
      if (!newMessage.value.trim()) return

      const content = newMessage.value.trim()
      newMessage.value = ''

      // Отправляем через WebSocket если подключен, иначе через API
      if (ws.value && ws.value.ws && ws.value.ws.readyState === WebSocket.OPEN) {
        // Оптимистично добавляем сообщение сразу
        const tempId = `temp-${Date.now()}-${Math.random()}`
        const tempMessage = {
          id: tempId,
          chat_id: chatId,
          sender_id: currentUserId.value,
          sender: { id: currentUserId.value, email: '', full_name: 'Вы' },
          content: content,
          created_at: new Date().toISOString(),
          edited_at: null,
          isTemp: true, // Флаг для временного сообщения
          tempId: tempId, // Уникальный идентификатор для замены
        }
        messages.value.push(tempMessage)
        scrollToBottom()
        
        // Отправляем через WebSocket
        try {
        ws.value.sendMessage(content)
        } catch (error) {
          // Если отправка не удалась, удаляем временное сообщение
          const index = messages.value.findIndex(m => m.tempId === tempId)
          if (index !== -1) {
            messages.value.splice(index, 1)
          }
          console.error('Error sending message via WebSocket:', error)
          // Пытаемся отправить через API как fallback
          try {
            const message = await messagesAPI.sendMessage(chatId, content)
            messages.value.push(message)
            scrollToBottom()
          } catch (apiError) {
            console.error('Error sending message via API:', apiError)
            alert('Ошибка отправки сообщения')
          }
        }
      } else {
        // Если WebSocket не подключен, используем API
        try {
          const message = await messagesAPI.sendMessage(chatId, content)
          messages.value.push(message)
          scrollToBottom()
        } catch (error) {
          console.error('Error sending message:', error)
          alert('Ошибка отправки сообщения')
        }
      }
    }

    const handleTyping = () => {
      if (ws.value) {
        ws.value.sendTyping()
      }
    }

    const setupWebSocket = () => {
      const token = localStorage.getItem('access_token')
      if (!token) return

      ws.value = new ChatWebSocket(
        chatId,
        token,
        (data) => {
          console.log('WebSocket callback received data:', data)
          if (data.type === 'new_message') {
            const message = data.message
            console.log('Processing new message:', message)
            
            // Используем nextTick для обеспечения реактивности Vue
            nextTick(() => {
              // Проверяем, нет ли уже такого сообщения по ID (чтобы избежать дубликатов)
              const existingIndex = messages.value.findIndex(m => m.id === message.id)
              if (existingIndex !== -1) {
                // Сообщение уже есть, обновляем его
                console.log('Updating existing message at index:', existingIndex)
                // Создаем новый массив для правильного обновления реактивности Vue
                const newMessages = [...messages.value]
                newMessages[existingIndex] = message
                messages.value = newMessages
              } else {
                // Ищем временное сообщение с таким же содержимым и отправителем
                // Проверяем, что это наше сообщение (от нас же)
                const isOurMessage = message.sender_id === currentUserId.value
                const tempIndex = messages.value.findIndex(
                  m => m.isTemp && 
                       m.content === message.content && 
                       m.sender_id === message.sender_id &&
                       isOurMessage // Только для наших сообщений
                )
                
                if (tempIndex !== -1) {
                  // Заменяем временное сообщение на реальное
                  console.log('Replacing temp message at index:', tempIndex)
                  // Создаем новый массив для правильного обновления реактивности Vue
                  const newMessages = [...messages.value]
                  newMessages[tempIndex] = message
                  messages.value = newMessages
                } else {
                  // Это новое сообщение от другого пользователя или наше, но без временного
                  console.log('Adding new message', isOurMessage ? 'from us (no temp found)' : 'from other user')
                  // Создаем новый массив для принудительного обновления реактивности
                  messages.value = [...messages.value, message]
                }
              }
              // Прокручиваем вниз после обновления сообщений
            scrollToBottom()
            })
          } else {
            console.log('Received WebSocket message with type:', data.type)
          }
        },
        (error) => {
          console.error('WebSocket error:', error)
        }
      )

      ws.value.connect()
    }

    const handleMemberSearch = async () => {
      if (!memberSearchQuery.value.trim()) {
        memberSearchResults.value = []
        return
      }
      try {
        const { usersAPI } = await import('../services/api')
        const response = await usersAPI.search(memberSearchQuery.value)
        // Исключаем текущего пользователя и уже существующих участников
        const existingMemberIds = currentChat.value?.members?.map(m => m.user_id) || []
        const excludeIds = [currentUserId.value, ...existingMemberIds].filter(Boolean)
        memberSearchResults.value = (response.data || []).filter(u => !excludeIds.includes(u.id))
      } catch (error) {
        console.error('Member search error:', error)
        memberSearchResults.value = []
      }
    }

    const toggleAddMember = (user) => {
      const index = membersToAdd.value.findIndex(m => m.id === user.id)
      if (index === -1) {
        membersToAdd.value.push(user)
      } else {
        membersToAdd.value.splice(index, 1)
      }
    }

    const isAddMemberSelected = (userId) => {
      return membersToAdd.value.some(m => m.id === userId)
    }

    const removeAddMember = (userId) => {
      const index = membersToAdd.value.findIndex(m => m.id === userId)
      if (index !== -1) {
        membersToAdd.value.splice(index, 1)
      }
    }

    const addMembersToGroup = async () => {
      if (membersToAdd.value.length === 0) {
        addMemberError.value = 'Выберите хотя бы одного участника'
        return
      }

      addingMembers.value = true
      addMemberError.value = ''

      try {
        const memberIds = membersToAdd.value.map(m => m.id)
        await chatsAPI.addMembersToGroup(chatId, memberIds)
        
        // Сброс формы и обновление чата
        showAddMembers.value = false
        memberSearchQuery.value = ''
        memberSearchResults.value = []
        membersToAdd.value = []
        await loadChat()
      } catch (error) {
        console.error('Error adding members:', error)
        addMemberError.value = error.response?.data?.detail || 'Ошибка добавления участников'
      } finally {
        addingMembers.value = false
      }
    }

    const goBack = () => {
      router.push('/')
    }

    onMounted(async () => {
      try {
        const user = await authAPI.getCurrentUser()
        currentUserId.value = user.id
        await loadChat()
        await loadMessages()
        setupWebSocket()
        // Дополнительная прокрутка после полной загрузки компонента
        await nextTick()
        setTimeout(() => {
          scrollToBottom(true)
        }, 500)
      } catch (error) {
        console.error('Error initializing chat:', error)
        router.push('/')
      }
    })

    onUnmounted(() => {
      if (ws.value) {
        ws.value.disconnect()
      }
    })

    watch(() => route.params.chatId, async (newChatId) => {
      if (ws.value) {
        ws.value.disconnect()
      }
      loading.value = true
      messages.value = []
      shouldAutoScroll.value = true
      currentChat.value = null
      await loadChat()
      await loadMessages()
      setupWebSocket()
      // Дополнительная прокрутка после переключения чата
      await nextTick()
      setTimeout(() => {
        scrollToBottom(true)
      }, 500)
    })
    
    // Отслеживаем изменения в messages для автоматической прокрутки
    watch(messages, () => {
      if (shouldAutoScroll.value) {
        scrollToBottom()
      }
    }, { deep: true })

    return {
      messages,
      loading,
      newMessage,
      chatName,
      currentUserId,
      messagesContainer,
      isGroupChat,
      showAddMembers,
      memberSearchQuery,
      memberSearchResults,
      membersToAdd,
      addingMembers,
      addMemberError,
      sendMessage,
      handleTyping,
      getSenderName,
      formatTime,
      handleMemberSearch,
      toggleAddMember,
      isAddMemberSelected,
      removeAddMember,
      addMembersToGroup,
      goBack,
    }
  },
}
</script>

<style scoped>
.chat-container {
  max-width: 1200px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-dark);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-card);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.back-btn {
  padding: 0.5rem 1rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-primary);
  font-weight: 500;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
  color: var(--primary-purple-light);
}

.chat-header h2 {
  margin: 0;
  flex: 1;
  text-align: center;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
}

.chat-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  background: var(--bg-dark);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  background: var(--bg-dark);
}

.messages-container::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track {
  background: var(--bg-card);
}

.messages-container::-webkit-scrollbar-thumb {
  background: var(--primary-purple);
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: var(--primary-purple-light);
}

.message {
  margin-bottom: 1rem;
  padding: 0.875rem 1rem;
  background: var(--bg-card);
  border-radius: 12px;
  max-width: 70%;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.message:hover {
  border-color: var(--primary-purple);
}

.own-message {
  margin-left: auto;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  border: none;
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.3);
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.message-header strong {
  color: var(--text-primary);
  font-weight: 600;
}

.own-message .message-header strong {
  color: rgba(255, 255, 255, 0.95);
}

.message-time {
  opacity: 0.7;
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.own-message .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.message-content {
  word-wrap: break-word;
  color: var(--text-primary);
  line-height: 1.5;
}

.own-message .message-content {
  color: white;
}

.input-container {
  display: flex;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
  background: var(--bg-card);
  gap: 0.75rem;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2);
}

.input-container input {
  flex: 1;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 1rem;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.input-container input::placeholder {
  color: var(--text-muted);
}

.input-container input:focus {
  outline: none;
  border-color: var(--primary-purple);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
  background: rgba(10, 10, 10, 0.7);
}

.input-container button {
  padding: 0.875rem 1.5rem;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
}

.input-container button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(147, 51, 234, 0.5);
}

.input-container button:disabled {
  background: var(--bg-card-hover);
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.5;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.add-members-btn {
  padding: 0.5rem 1rem;
  background: rgba(147, 51, 234, 0.2);
  border: 1px solid var(--primary-purple);
  border-radius: 8px;
  cursor: pointer;
  color: var(--primary-purple-light);
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.3s ease;
}

.add-members-btn:hover {
  background: rgba(147, 51, 234, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(147, 51, 234, 0.3);
}

/* Модальное окно (аналогично Home.vue) */
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

.error {
  color: var(--error);
  margin-top: 0.5rem;
  font-size: 0.9rem;
  padding: 0.5rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}
</style>

