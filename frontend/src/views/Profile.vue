<template>
  <div class="profile-container">
    <header class="header">
      <button @click="goBack" class="back-btn">← Назад</button>
      <h1>Профиль</h1>
      <div></div>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="profile-content">
      <div class="profile-card">
        <h2>Информация о пользователе</h2>
        <div class="profile-info">
          <div class="info-item">
            <label>Email:</label>
            <span>{{ user.email }}</span>
          </div>
          <div class="info-item">
            <label>Имя:</label>
            <span>{{ user.full_name || 'Не указано' }}</span>
          </div>
          <div class="info-item">
            <label>ID:</label>
            <span>{{ user.id }}</span>
          </div>
        </div>

        <div class="danger-zone">
          <h3>Опасная зона</h3>
          <p>Удаление аккаунта необратимо. Все ваши данные будут удалены.</p>
          <button @click="handleDelete" class="delete-btn" :disabled="deleting">
            {{ deleting ? 'Удаление...' : 'Удалить аккаунт' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../services/api'

export default {
  name: 'Profile',
  setup() {
    const router = useRouter()
    const user = ref(null)
    const loading = ref(true)
    const deleting = ref(false)

    const loadUser = async () => {
      try {
        user.value = await authAPI.getCurrentUser()
      } catch (error) {
        console.error('Error loading user:', error)
        router.push('/login')
      } finally {
        loading.value = false
      }
    }

    const handleDelete = async () => {
      if (!confirm('Вы уверены, что хотите удалить свой аккаунт? Это действие необратимо.')) {
        return
      }

      deleting.value = true
      try {
        await authAPI.deleteAccount()
        localStorage.removeItem('access_token')
        alert('Аккаунт успешно удален')
        router.push('/login')
      } catch (error) {
        console.error('Error deleting account:', error)
        alert(error.response?.data?.detail || 'Ошибка удаления аккаунта')
      } finally {
        deleting.value = false
      }
    }

    const goBack = () => {
      router.push('/')
    }

    onMounted(() => {
      loadUser()
    })

    return {
      user,
      loading,
      deleting,
      handleDelete,
      goBack,
    }
  },
}
</script>

<style scoped>
.profile-container {
  max-width: 800px;
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

.header h1 {
  margin: 0;
  flex: 1;
  text-align: center;
  color: var(--text-primary);
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #9333ea 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.profile-content {
  background: var(--bg-card);
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
}

.profile-card h2 {
  margin-top: 0;
  color: var(--text-primary);
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
}

.profile-info {
  margin-bottom: 2rem;
}

.info-item {
  display: flex;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.3s ease;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item:hover {
  background: var(--bg-card-hover);
}

.info-item label {
  font-weight: 500;
  width: 150px;
  color: var(--text-secondary);
}

.info-item span {
  color: var(--text-primary);
}

.danger-zone {
  margin-top: 2rem;
  padding: 1.5rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.danger-zone h3 {
  margin-top: 0;
  color: var(--error);
  font-size: 1.25rem;
  font-weight: 600;
}

.danger-zone p {
  color: var(--text-secondary);
  margin-bottom: 1rem;
  line-height: 1.6;
}

.delete-btn {
  padding: 0.75rem 1.5rem;
  background: rgba(239, 68, 68, 0.2);
  color: var(--error);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.delete-btn:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.3);
  border-color: var(--error);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.delete-btn:disabled {
  background: var(--bg-card-hover);
  cursor: not-allowed;
  opacity: 0.5;
  transform: none;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}
</style>

