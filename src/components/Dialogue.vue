<script setup>
import { ref } from 'vue';

const query = ref('');
const messages = ref([]);
const isLoading = ref(false);

async function handleSendMessage() {
  if (!query.value.trim()) return;
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: query.value
  });
  
  isLoading.value = true;
  try {
    const response = await fetch('http://localhost:5000/api/weather', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query.value,
        streaming: false, // 可选，是否启用流式输出
      }),
    });

    const data = await response.json();
    if (data.error) {
      throw new Error(data.error);
    }

    // 添加助手回复
    messages.value.push({
      role: 'assistant',
      content: data.response
    });
  } catch (error) {
    console.error('Error:', error);
    messages.value.push({
      role: 'error',
      content: '发送消息时出错，请重试。'
    });
  } finally {
    isLoading.value = false;
    query.value = ''; // 清空输入框
  }
}
</script>

<template>
  <div class="chat-container">
    <div class="messages-container">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.role]">
        <div class="message-content">
          {{ message.content }}
        </div>
      </div>
      <div v-if="isLoading" class="message assistant">
        <div class="message-content">
          正在思考...
        </div>
      </div>
    </div>
    
    <div class="input-container">
      <textarea
        v-model="query"
        placeholder="输入您的问题"
        @keyup.enter.ctrl="handleSendMessage"
      ></textarea>
      <button 
        @click="handleSendMessage"
        :disabled="isLoading || !query.trim()"
      >
        {{ isLoading ? '发送中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 20px;
}

.message {
  margin-bottom: 16px;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
}

.message.assistant {
  margin-right: auto;
}

.message.error {
  margin-right: auto;
  color: #ff4444;
}

.message-content {
  padding: 12px 16px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.message.user .message-content {
  background: #007AFF;
  color: white;
}

.message.assistant .message-content {
  background: white;
}

.message.error .message-content {
  background: #ffebee;
  color: #ff4444;
}

.input-container {
  display: flex;
  gap: 10px;
}

textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  height: 60px;
  font-family: inherit;
}

button {
  padding: 0 20px;
  background: #007AFF;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover {
  background: #0056b3;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>