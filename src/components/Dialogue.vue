<script setup>
import { ref } from 'vue';
import { marked } from 'marked';

const query = ref('');
const messages = ref([]);
const isLoading = ref(false);
const currentResponse = ref('');
const isStreaming = ref(false);
const hasAddedToMessages = ref(false); // 用于标记是否已将响应添加到消息列表

async function handleSendMessage() {
  if (!query.value.trim()) return;
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: query.value
  });
  
  isLoading.value = true;
  isStreaming.value = true;
  currentResponse.value = ''; // 重置当前响应
  hasAddedToMessages.value = false; // 重置标记
  
  try {
    console.log('开始发送请求...');
    const response = await fetch('http://localhost:5000/api/weather', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        query: query.value,
        streaming: true,
      }),
    });

    console.log('收到响应:', response);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('响应错误:', errorText);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        console.log('流式响应结束');
        break;
      }
      
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;
      
      // 按行处理缓冲区
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // 保留最后一个不完整的行
      
      for (const line of lines) {
        if (!line.trim()) continue;
        
        try {
          const data = JSON.parse(line);
          console.log('解析后的数据:', data);
          
          if (data.error) {
            throw new Error(data.error);
          }
          if (data.response) {
            currentResponse.value += data.response;
          }
        } catch (e) {
          console.error('解析数据块时出错:', e);
          console.error('原始数据:', line);
        }
      }
    }

    // 处理缓冲区中剩余的数据
    if (buffer.trim()) {
      try {
        const data = JSON.parse(buffer);
        if (data.response) {
          currentResponse.value += data.response;
        }
      } catch (e) {
        console.error('解析最后的数据块时出错:', e);
      }
    }

  }  
  finally {
    isLoading.value = false;
    isStreaming.value = false;
    if (currentResponse.value && !hasAddedToMessages.value) {
      messages.value.push({
        role: 'assistant',
        content: currentResponse.value
      });
      hasAddedToMessages.value = true;
    }
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
      <div v-if="isStreaming && currentResponse && !hasAddedToMessages" class="message assistant">
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
  min-height: 300px;
}

.message {
  margin-bottom: 16px;
  max-width: 80%;
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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
  white-space: pre-wrap;
  word-break: break-word;
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