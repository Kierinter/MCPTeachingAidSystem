<script setup>
import { ref } from 'vue';
import { marked } from 'marked';

const query = ref('');
const messages = ref([]);
const isLoading = ref(false);
const currentResponse = ref('');

async function handleSendMessage() {
  if (!query.value.trim()) return;
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: query.value
  });
  
  isLoading.value = true;
  currentResponse.value = ''; // 重置当前响应
  
  try {
    const response = await fetch('http://localhost:5000/api/weather', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query.value,
        streaming: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      try {
        const data = JSON.parse(chunk);
        if (data.error) {
          throw new Error(data.error);
        }
        if (data.response) {
          currentResponse.value += data.response;
        }
      } catch (e) {
        console.error('Error parsing chunk:', e);
      }
    }

    // 添加完整的助手回复
    messages.value.push({
      role: 'assistant',
      content: currentResponse.value
    });
  } catch (error) {
    console.error('Error:', error);
    messages.value.push({
      role: 'error',
      content: `发送消息时出错: ${error.message}`
    });
  } finally {
    isLoading.value = false;
    currentResponse.value = '';
    query.value = ''; // 清空输入框
  }
}
</script>

<template>
  <div class="chat-container">
    <div class="messages-container">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.role]">
        <div class="message-content" v-html="marked(message.content)"></div>
      </div>
      <div v-if="isLoading" class="message assistant">
        <div class="message-content" v-html="marked(currentResponse)"></div>
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

/* Markdown 样式 */
.message-content :deep(pre) {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
}

.message-content :deep(code) {
  background: #f6f8fa;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
}

.message-content :deep(blockquote) {
  border-left: 4px solid #dfe2e5;
  padding-left: 16px;
  margin-left: 0;
  color: #6a737d;
}

.message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

.message-content :deep(th),
.message-content :deep(td) {
  border: 1px solid #dfe2e5;
  padding: 6px 13px;
}

.message-content :deep(th) {
  background: #f6f8fa;
}
</style>