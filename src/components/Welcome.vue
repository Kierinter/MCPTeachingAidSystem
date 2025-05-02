<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goToDialogue = () => {
  router.push('/dialogue')
}

const goToLogin = () => {
  router.push('/login')
}

const goToRegister = () => {
  router.push('/register')
}

const goToMain = () => {
  router.push('/index')
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="bg-primary-800 text-white px-6 py-4 shadow-md">
      <div class="container mx-auto flex justify-between items-center">
        <h1 class="text-2xl font-bold">AI 教辅系统</h1>
        <nav class="flex items-center space-x-6">
          <a href="#" @click.prevent="goToMain" class="hover:text-primary-200 transition-colors">主页</a>
          <a href="#" @click.prevent="goToLogin" class="hover:text-primary-200 transition-colors">登录</a>
          <a href="#" @click.prevent="goToRegister" class="hover:text-primary-200 transition-colors">注册</a>
        </nav>
      </div>
    </header>

    <section class="py-20 px-6 bg-gradient-to-r from-primary-700 to-primary-500 text-white text-center">
      <div class="container mx-auto">
        <h2 class="text-4xl font-bold mb-6">让学习更轻松高效</h2>
        <p class="text-xl max-w-2xl mx-auto mb-8">基于AI的对话式辅导系统，精准识别知识盲点，智能生成解题方案，陪伴你的每一步学习之旅。</p>
        <button @click="goToDialogue" class="px-8 py-3 bg-white text-primary-800 font-medium rounded-lg hover:bg-primary-50 transition-colors shadow-lg">立即开始对话</button>
      </div>
    </section>

    <section class="py-16 px-6 bg-white">
      <div class="container mx-auto">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="bg-gray-50 p-8 rounded-xl shadow-sm hover:shadow-md transition-shadow">
            <h3 class="text-xl font-semibold mb-3 text-primary-800">个性化学习路径</h3>
            <p class="text-gray-600">根据学习情况自动调整课程节奏与内容。</p>
          </div>
          <div class="bg-gray-50 p-8 rounded-xl shadow-sm hover:shadow-md transition-shadow">
            <h3 class="text-xl font-semibold mb-3 text-primary-800">实时对话解题</h3>
            <p class="text-gray-600">支持直接向AI文字提问，AI即时解析与指导。</p>
          </div>
          <div class="bg-gray-50 p-8 rounded-xl shadow-sm hover:shadow-md transition-shadow">
            <h3 class="text-xl font-semibold mb-3 text-primary-800">作业批改与反馈</h3>
            <p class="text-gray-600">上传作业，系统自动批改并生成分析报告。</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>