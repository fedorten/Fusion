<template>
  <div class="register-container">
    <div class="register-card">
      <h1>Регистрация</h1>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>Email:</label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="your@email.com"
          />
        </div>
        <div class="form-group">
          <label>Имя (необязательно):</label>
          <input
            v-model="fullName"
            type="text"
            placeholder="Ваше имя"
          />
        </div>
        <div class="form-group">
          <label>Пароль:</label>
          <input
            v-model="password"
            type="password"
            required
            minlength="8"
            placeholder="Минимум 8 символов"
          />
        </div>
        <div v-if="error" class="error">{{ error }}</div>
        <div v-if="success" class="success">{{ success }}</div>
        <button type="submit" :disabled="loading">
          {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>
        <p class="login-link">
          Уже есть аккаунт? <router-link to="/login">Войти</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../services/api'

export default {
  name: 'Register',
  setup() {
    const router = useRouter()
    const email = ref('')
    const fullName = ref('')
    const password = ref('')
    const error = ref('')
    const success = ref('')
    const loading = ref(false)

    const handleRegister = async () => {
      error.value = ''
      success.value = ''
      loading.value = true
      
      try {
        await authAPI.register(email.value, password.value, fullName.value || null)
        // Автоматически логиним пользователя после регистрации
        try {
          const tokenData = await authAPI.login(email.value, password.value)
          localStorage.setItem('access_token', tokenData.access_token)
          success.value = 'Регистрация успешна! Перенаправление...'
          setTimeout(() => {
            router.push('/')
          }, 500)
        } catch (loginErr) {
          // Если автоматический логин не удался, перенаправляем на страницу входа
          error.value = 'Регистрация успешна, но не удалось войти. Пожалуйста, войдите вручную.'
          setTimeout(() => {
            router.push('/login')
          }, 2000)
        }
      } catch (err) {
        error.value = err.response?.data?.detail || 'Ошибка регистрации'
      } finally {
        loading.value = false
      }
    }

    return {
      email,
      fullName,
      password,
      error,
      success,
      loading,
      handleRegister,
    }
  },
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 100%);
  position: relative;
  overflow: hidden;
}

.register-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(147, 51, 234, 0.1) 0%, transparent 70%);
  animation: pulse 20s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

.register-card {
  background: rgba(26, 26, 26, 0.95);
  backdrop-filter: blur(10px);
  padding: 3rem;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(147, 51, 234, 0.3), 0 0 0 1px rgba(147, 51, 234, 0.1);
  width: 100%;
  max-width: 420px;
  position: relative;
  z-index: 1;
}

h1 {
  margin-bottom: 2rem;
  text-align: center;
  color: var(--text-primary);
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #9333ea 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.9rem;
}

input {
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

input::placeholder {
  color: var(--text-muted);
}

input:focus {
  outline: none;
  border-color: var(--primary-purple);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
  background: rgba(10, 10, 10, 0.7);
}

button {
  width: 100%;
  padding: 0.875rem;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 1rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
}

button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(147, 51, 234, 0.5);
  background: linear-gradient(135deg, var(--primary-purple-light) 0%, var(--primary-purple) 100%);
}

button:active:not(:disabled) {
  transform: translateY(0);
}

button:disabled {
  background: var(--bg-card);
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.5;
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

.success {
  color: var(--success);
  margin-top: 0.5rem;
  font-size: 0.9rem;
  padding: 0.5rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.login-link {
  text-align: center;
  margin-top: 1.5rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.login-link a {
  color: var(--primary-purple-light);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.login-link a:hover {
  color: var(--primary-purple);
  text-decoration: underline;
}
</style>

