<script setup>
import { ref } from 'vue';
import { marked } from 'marked';

const query = ref('');
const messages = ref([]);
const isLoading = ref(false);
const currentResponse = ref('');
const isStreaming = ref(false);
const hasAddedToMessages = ref(false);

async function handleSendMessage() {
  if (!query.value.trim()) return;
  
  messages.value.push({
    role: 'user',
    content: query.value
  });
  
  isLoading.value = true;
  isStreaming.value = true;
  currentResponse.value = '';
  hasAddedToMessages.value = false;
  
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
      
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
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

  } catch (error) {
    console.error('请求过程中出错:', error);
    let errorMessage = '发送消息时出错';
    if (error instanceof TypeError) {
      errorMessage = '网络连接错误,请检查网络设置';
    } else if (error.message.includes('timeout')) {
      errorMessage = '请求超时,请稍后重试';
    } else if (error.message.includes('HTTP error')) {
      errorMessage = '服务器响应错误,请联系管理员';
    } else {
      errorMessage = `${errorMessage}: ${error.message}`;
    }
    messages.value.push({
      role: 'error', 
      content: errorMessage
    });
  } finally {
    isLoading.value = false;
    isStreaming.value = false;
    if (currentResponse.value) {
      messages.value.push({
        role: 'assistant',
        content: currentResponse.value
      });
    }
    currentResponse.value = '';
    query.value = '';
  }
}
</script>

<template>
  <div class="flex flex-col h-full max-w-4xl mx-auto p-4 md:p-6">
    <div class="flex-1 overflow-y-auto bg-zinc-50 rounded-lg p-4 mb-4 min-h-[400px] shadow-sm">
      <div v-for="(message, index) in messages" :key="index" 
           :class="[
             'mb-4 max-w-[85%] animate-fade-in',
             message.role === 'user' ? 'ml-auto' : '',
             message.role === 'assistant' ? 'mr-auto' : '',
             message.role === 'error' ? 'mr-auto' : ''
           ]">
        <div :class="[
          'rounded-lg shadow-sm p-3 overflow-x-auto',
          message.role === 'user' ? 'bg-primary-600 text-white' : '',
          message.role === 'assistant' ? 'bg-white' : '',
          message.role === 'error' ? 'bg-red-50 text-red-500 border border-red-200' : ''
        ]" v-html="marked(message.content)"></div>
      </div>
      <div v-if="isStreaming" class="mr-auto mb-4 max-w-[85%] animate-fade-in">
        <div class="bg-white rounded-lg shadow-sm p-3" v-html="marked(currentResponse)"></div>
      </div>
    </div>
    
    <div class="flex gap-3">
      <textarea
        v-model="query"
        placeholder="输入您的问题"
        @keyup.enter.ctrl="handleSendMessage"
        class="flex-1 p-3 border border-gray-300 rounded-lg resize-none h-[60px] focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
      ></textarea>
      <button 
        @click="handleSendMessage"
        :disabled="isLoading || !query.trim()"
        class="px-6 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {{ isLoading ? '发送中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<style>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.3s ease-in-out;
}

/* Markdown 样式 */
.message-content pre {
  @apply bg-zinc-50 p-4 rounded-md overflow-x-auto my-2;
}

.message-content code {
  @apply bg-zinc-50 px-1 py-0.5 rounded-md font-mono text-sm;
}

.message-content blockquote {
  @apply border-l-4 border-gray-300 pl-4 ml-0 text-gray-600 my-2;
}

.message-content table {
  @apply w-full border-collapse my-4;
}

.message-content th,
.message-content td {
  @apply border border-gray-300 p-2 text-left;
}

.message-content th {
  @apply bg-zinc-50;
}
</style>