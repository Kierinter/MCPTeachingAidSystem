<script setup>
import { useRouter } from 'vue-router';
import { ref } from 'vue';

const router = useRouter();

const goToDialogue = () => {
  router.push('/dialogue');
};

const goToLogin = () => {
  router.push('/login');
};

const courses = ref([
  { 
    id: 1, 
    title: '高等数学基础', 
    description: '涵盖高等数学核心概念与应用',
    image: 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8bWF0aHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=500&q=60',
    level: '入门',
    lessons: 12
  },
  { 
    id: 2, 
    title: '线性代数进阶', 
    description: '深入理解矩阵计算与向量空间',
    image: 'https://images.unsplash.com/photo-1509228627152-72ae9ae6848d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NXx8bWF0aHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=500&q=60',
    level: '中级',
    lessons: 10
  },
  { 
    id: 3, 
    title: '数据结构与算法', 
    description: '学习编程中的核心数据结构与算法',
    image: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8Y29kaW5nfGVufDB8fDB8fHww&auto=format&fit=crop&w=500&q=60',
    level: '中级',
    lessons: 15
  },
]);

const features = ref([
  {
    title: '智能对话辅导',
    description: 'AI助手可以回答各种学术问题，提供清晰的解释和引导。'
  },
  {
    title: '个性化学习路径',
    description: '系统分析你的学习情况，推荐最适合你的学习内容和进度。'
  },
  {
    title: '实时反馈评估',
    description: '完成练习后获得即时反馈，了解你的掌握程度和需要改进的地方。'
  },
  {
    title: '多媒体学习资源',
    description: '提供视频、图表和互动内容，满足不同学习风格的需求。'
  },
]);
</script>

<template>
  <div class="min-h-screen w-screen max-w-full overflow-x-hidden bg-gray-50">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm w-full">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <span class="text-xl font-bold text-primary-800">AI教辅系统</span>
          </div>
          <div class="flex items-center space-x-4">
            <a href="#features" class="text-gray-600 hover:text-primary-700 px-3 py-2">功能</a>
            <a href="#courses" class="text-gray-600 hover:text-primary-700 px-3 py-2">课程</a>
            <button @click="goToLogin" class="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
              登录 / 注册
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- 英雄区 -->
    <section class="bg-gradient-to-r from-primary-700 via-primary-800 to-primary-900 text-white py-20 w-full">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col md:flex-row items-center">
          <div class="md:w-1/2 mb-8 md:mb-0">
            <h1 class="text-4xl md:text-5xl font-bold mb-4">让学习更高效、更有趣</h1>
            <p class="text-xl mb-6 opacity-90">
              利用人工智能技术，提供个性化学习体验，助你轻松掌握知识。
            </p>
            <div class="flex space-x-4">
              <button @click="goToDialogue" class="bg-white text-primary-800 px-6 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors">
                开始对话
              </button>
              <a href="#features" class="border border-white text-white px-6 py-3 rounded-lg font-medium hover:bg-white hover:bg-opacity-10 transition-colors">
                了解更多
              </a>
            </div>
          </div>
          <div class="md:w-1/2">
            <img src="https://img.freepik.com/free-vector/online-learning-isometric-concept_1284-17947.jpg?size=626&ext=jpg" alt="AI教育" class="rounded-lg shadow-xl max-w-full">
          </div>
        </div>
      </div>
    </section>

    <!-- 特点 -->
    <section id="features" class="py-16 w-full">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-center mb-12 text-gray-800">我们的特点</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div v-for="(feature, index) in features" :key="index" class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
            <div class="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center text-primary-700 mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold mb-2 text-gray-800">{{ feature.title }}</h3>
            <p class="text-gray-600">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 课程 -->
    <section id="courses" class="py-16 bg-gray-100 w-full">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-center mb-12 text-gray-800">热门课程</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div v-for="course in courses" :key="course.id" 
               class="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
            <img :src="course.image" :alt="course.title" class="w-full h-48 object-cover">
            <div class="p-6">
              <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium px-2 py-1 bg-primary-100 text-primary-800 rounded">{{ course.level }}</span>
                <span class="text-sm text-gray-600">{{ course.lessons }} 课时</span>
              </div>
              <h3 class="text-xl font-semibold mb-2 text-gray-800">{{ course.title }}</h3>
              <p class="text-gray-600 mb-4">{{ course.description }}</p>
              <button class="w-full bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700 transition-colors">
                了解详情
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA区域 -->
    <section class="bg-primary-800 text-white py-16 w-full">
      <div class="max-w-4xl mx-auto px-4 text-center">
        <h2 class="text-3xl font-bold mb-6">准备好开始学习之旅了吗？</h2>
        <p class="text-xl mb-8 opacity-90">加入我们，体验AI驱动的个性化学习体验。</p>
        <div class="flex justify-center space-x-4">
          <button @click="goToDialogue" class="bg-white text-primary-800 px-6 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors">
            开始对话
          </button>
          <button @click="goToLogin" class="border border-white text-white px-6 py-3 rounded-lg font-medium hover:bg-white hover:bg-opacity-10 transition-colors">
            注册账号
          </button>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="bg-gray-800 text-white py-12 w-full">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h4 class="text-xl font-bold mb-4">AI教辅系统</h4>
            <p class="text-gray-400">
              我们致力于通过AI技术，让学习变得更加高效、个性化和有趣。
            </p>
          </div>
          <div>
            <h4 class="text-lg font-semibold mb-4">快速链接</h4>
            <ul class="space-y-2">
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">首页</a></li>
              <li><a href="#features" class="text-gray-400 hover:text-white transition-colors">功能</a></li>
              <li><a href="#courses" class="text-gray-400 hover:text-white transition-colors">课程</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-lg font-semibold mb-4">联系我们</h4>
            <p class="text-gray-400">
              有任何问题或建议？请联系我们的客服团队。
            </p>
            <p class="text-gray-400 mt-2">
              Email: support@aiteachingsystem.com
            </p>
          </div>
        </div>
        <div class="mt-8 pt-8 border-t border-gray-700 text-center">
          <p class="text-gray-400">© 2025 AI教辅系统. 保留所有权利.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* 确保内容铺满屏幕 */
.min-h-screen {
  min-height: 100vh;
}

.w-screen {
  width: 100vw;
}

.max-w-full {
  max-width: 100%;
}

.overflow-x-hidden {
  overflow-x: hidden;
}
</style>