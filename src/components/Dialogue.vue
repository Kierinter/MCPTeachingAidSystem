<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue';
import { marked } from 'marked';
import { useRouter } from 'vue-router';

// 配置 marked 以支持数学公式
const renderer = new marked.Renderer();
const originalCodeRenderer = renderer.code.bind(renderer);

renderer.code = function(code, language) {
  // 处理数学公式块
  if (language === 'math' || language === 'tex') {
    return `<div class="math-block">\\[${code}\\]</div>`;
  }
  // 使用原始渲染器处理其他代码块
  return originalCodeRenderer(code, language);
};

// 自定义渲染器解析并渲染标记的内容
const customMarkdownRenderer = (content) => {
  if (!content) return '';
  
  // 首先使用marked处理markdown内容
  const html = marked(content, { renderer });
  return html;
};

// MathJax 配置和渲染函数
const configureMathJax = () => {
  // 在全局范围内定义MathJax配置
  window.MathJax = {
    tex: {
      inlineMath: [['$', '$']],
      displayMath: [['$$', '$$']],
      processEscapes: true,
      processEnvironments: true
    },
    options: {
      skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
      ignoreHtmlClass: 'no-mathjax'
    },
    startup: {
      typeset: false
    }
  };
};

// 延迟加载 MathJax 脚本
const loadMathJax = () => {
  return new Promise((resolve) => {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js';
    script.async = true;
    script.onload = resolve;
    document.head.appendChild(script);
  });
};

// 渲染页面中的数学公式
const renderMathJax = () => {
  nextTick(() => {
    if (window.MathJax && window.MathJax.typesetPromise) {
      try {
        window.MathJax.typesetPromise();
      } catch (error) {
        console.error('MathJax 渲染错误:', error);
      }
    }
  });
};

// 初始化 MathJax
const initMathJax = async () => {
  // 配置 MathJax
  configureMathJax();
  
  // 加载 MathJax 脚本
  await loadMathJax();
  
  // 首次渲染
  renderMathJax();
};

const router = useRouter();
const query = ref('');
const messages = ref([]);
const isLoading = ref(false);
const currentResponse = ref('');
const isStreaming = ref(false);
const hasAddedToMessages = ref(false);
const chatHistory = ref([]);
const showHistory = ref(false);
const messagesContainer = ref(null); // 引用聊天消息容器

// 组织历史记录按日期分组
const groupedHistory = computed(() => {
  const groups = {};
  
  chatHistory.value.forEach(item => {
    if (!groups[item.date]) {
      groups[item.date] = [];
    }
    groups[item.date].push(item);
  });
  
  return groups;
});

// 预定义的话题建议
const suggestedTopics = ref([
  "高等数学中的极限概念如何理解？",
  "线性代数的特征值和特征向量有什么作用？",
  "如何解决难度较大的微分方程？",
  "概率论中的贝叶斯公式应用场景？",
  "数据结构中哈希表的工作原理是什么？",
  "C编程语言中的内存管理机制？"
]);

// 生成新的建议话题
async function generateTopics() {
  isLoading.value = true;

  try {
    const response = await fetch('http://localhost:5000/api/topics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: "生成一些适合大学生学习的数学、物理或编程相关话题"
      }),
    });

    if (!response.ok) {
      throw new Error('获取话题失败');
    }

    const data = await response.json();
    suggestedTopics.value = data.topics;
  } catch (error) {
    console.error('获取话题失败:', error);
    // 使用备用话题
    suggestedTopics.value = [
      "物理学中的四大基本力是什么？",
      "化学键的类型及其特点？",
      "编程中递归算法的应用场景有哪些？",
      "如何分析古典文学作品的主题？",
      "人工智能中的神经网络是如何工作的？",
      "计算机网络基础协议有哪些？"
    ];
  } finally {
    isLoading.value = false;
  }
}

// 使用建议话题
function useTopicAsQuery(topic) {
  query.value = topic;
}

// 保存对话到历史记录
function saveToHistory() {
  if (messages.value.length === 0) return;
  
  const now = new Date();
  const timeString = now.toLocaleTimeString();
  const dateString = now.toLocaleDateString();
  
  // 提取对话的第一条消息作为标题，最多30个字符
  let title = messages.value[0].content;
  if (title.length > 30) {
    title = title.substring(0, 30) + "...";
  }
  
  chatHistory.value.unshift({
    id: Date.now(),
    title: title,
    time: timeString,
    date: dateString,
    messages: [...messages.value]
  });
  
  // 保存到本地存储
  localStorage.setItem('chatHistory', JSON.stringify(chatHistory.value));
}

// 自动滚动到底部的函数
const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 监听消息列表变化和流式响应内容变化，自动滚动到底部并渲染公式
watch([messages, currentResponse], () => {
  scrollToBottom();
  renderMathJax(); // 使用 MathJax 渲染
}, { deep: true });

// 从本地存储加载历史记录
onMounted(async () => {
  const savedHistory = localStorage.getItem('chatHistory');
  if (savedHistory) {
    chatHistory.value = JSON.parse(savedHistory);
  }
  
  // 不再初始时生成话题，使用预定义的话题
  // generateTopics();
  
  // 初始化 MathJax
  await initMathJax();
});

// 加载对话时滚动到底部
function loadConversation(conversation) {
  messages.value = [...conversation.messages];
  showHistory.value = false;
  
  // 加载对话后滚动到底部
  scrollToBottom();
}

// 清空当前对话
function startNewChat() {
  // 如果当前有对话，先保存
  if (messages.value.length > 0) {
    saveToHistory();
  }
  
  messages.value = [];
  currentResponse.value = '';
}

// 删除历史记录
function deleteHistoryItem(id) {
  chatHistory.value = chatHistory.value.filter(item => item.id !== id);
  localStorage.setItem('chatHistory', JSON.stringify(chatHistory.value));
}

async function handleSendMessage() {
  if (!query.value.trim()) return;
  
  messages.value.push({
    role: 'user',
    content: query.value
  });
  
  // 添加消息后滚动到底部
  scrollToBottom();
  
  isLoading.value = true;
  isStreaming.value = true;
  currentResponse.value = '';
  hasAddedToMessages.value = false;
  
  try {
    console.log('开始发送请求...');
    const response = await fetch('http://localhost:5000/api/query', {
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
  <div class="flex flex-col h-screen w-screen max-w-full">
    <!-- 顶部导航栏 -->
    <div class="bg-yellow-400 shadow-sm p-4 flex justify-between items-center">
      <div class="flex items-center space-x-4">
        <button 
          @click="showHistory = !showHistory" 
          class="text-gray-600 hover:text-primary-600 flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" />
          </svg>
          历史记录
        </button>
      </div>
      
      <button 
        @click="startNewChat" 
        class="bg-primary-500 text-white px-4 py-2 rounded-lg hover:bg-primary-600 transition-colors flex items-center"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
        </svg>
        新对话
      </button>
    </div>
    
    <div class="flex flex-1 overflow-hidden w-full">
      <!-- 历史记录侧边栏 -->
      <div 
        v-if="showHistory" 
        class="w-80 bg-blue-300 border-r border-gray-200 p-4 overflow-y-auto transition-all"
      >
        <h2 class="text-lg font-semibold text-gray-800 mb-4">历史对话</h2>
        
        <div v-if="chatHistory.length === 0" class="text-gray-500 text-center py-6">
          暂无历史对话
        </div>
        
        <div v-else>
          <div v-for="(conversations, date) in groupedHistory" :key="date" class="mb-6">
            <h3 class="text-sm font-medium text-gray-500 mb-2">{{ date }}</h3>
            <div 
              v-for="conversation in conversations" 
              :key="conversation.id"
              class="bg-white rounded-lg shadow-sm p-3 mb-2 cursor-pointer hover:bg-primary-50 transition-colors group"
            >
              <div class="flex justify-between">
                <div class="flex-1" @click="loadConversation(conversation)">
                  <p class="font-medium text-gray-800 truncate">{{ conversation.title }}</p>
                  <p class="text-sm text-gray-500">{{ conversation.time }}</p>
                </div>
                <button 
                  @click="deleteHistoryItem(conversation.id)"
                  class="text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 主聊天区域 -->
      <div class="flex-1 flex flex-col p-4 overflow-hidden w-full">
        <!-- 建议话题区 -->
        <div v-if="messages.length === 0" class="mb-6">
          <h2 class="text-xl font-semibold text-gray-800 mb-4 text-center">建议话题</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div 
              v-for="(topic, index) in suggestedTopics" 
              :key="index"
              @click="useTopicAsQuery(topic)"
              class="bg-white border border-gray-200 rounded-lg p-3 cursor-pointer hover:bg-primary-50 hover:border-primary-300 transition-colors"
            >
              <p class="text-gray-700">{{ topic }}</p>
            </div>
          </div>
          <div class="flex justify-center mt-4">
            <button 
              @click="generateTopics"
              :disabled="isLoading"
              class="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              <span v-if="isLoading">生成中...</span>
              <span v-else>换一批</span>
            </button>
          </div>
        </div>
        
        <!-- 消息区域 -->
        <div 
          ref="messagesContainer"
          class="flex-1 overflow-y-auto bg-zinc-50 rounded-lg p-4 mb-4 w-full"
        >
          <div class="flex flex-col">
            <div v-for="(message, index) in messages" :key="index" 
               :class="[

               'mb-4 animate-fade-in flex',
               message.role === 'user' ? 'justify-end' : 'justify-start'
               ]">
              <div :class="[

          'rounded-lg shadow-sm p-3 max-w-[85%] overflow-x-auto',
          message.role === 'user' ? 'bg-primary-600 text-white' : '',
          message.role === 'assistant' ? 'bg-white' : '',
          message.role === 'error' ? 'bg-red-50 text-red-500 border border-red-200' : ''
              ]">
          <div class="message-content" v-html="marked(message.content)"></div>
              </div>
            </div>
          </div>
          <div v-if="isStreaming" class="mr-auto mb-4 max-w-[85%] animate-fade-in">
            <div class="bg-white rounded-lg shadow-sm p-3" v-html="marked(currentResponse)"></div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="flex gap-3 w-full">
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
        
        <!-- 保存按钮 -->
        <div class="mt-2 text-right" v-if="messages.length > 0">
          <button 
            @click="saveToHistory"
            class="text-primary-600 text-sm hover:underline"
          >
            保存对话
          </button>
        </div>
      </div>
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

/* 添加全屏样式 */
.h-screen {
  height: 100vh;
}

.w-screen {
  width: 100vw;
}

/* 确保滚动区域正确显示 */
.overflow-y-auto {
  overflow-y: auto;
}

.overflow-hidden {
  overflow: hidden;
}
</style>