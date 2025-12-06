// WebSocket сервис для чата
export class ChatWebSocket {
  constructor(chatId, token, onMessage, onError) {
    this.chatId = chatId
    this.token = token
    this.onMessage = onMessage
    this.onError = onError
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
  }

  connect() {
    // Всегда используем относительный путь через nginx прокси
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/${this.chatId}?token=${this.token}`
    
    console.log('Connecting to WebSocket:', wsUrl)
    
    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('WebSocket message received:', data)
          if (this.onMessage) {
            this.onMessage(data)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        if (this.onError) {
          this.onError(error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        // Попытка переподключения
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          setTimeout(() => {
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`)
            this.connect()
          }, 1000 * this.reconnectAttempts)
        }
      }
    } catch (error) {
      console.error('Error creating WebSocket:', error)
      if (this.onError) {
        this.onError(error)
      }
    }
  }

  sendMessage(content) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'message',
        content: content,
      }))
    } else {
      console.error('WebSocket is not connected')
    }
  }

  sendTyping() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'typing',
      }))
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}
