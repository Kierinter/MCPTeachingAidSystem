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
</script>

<template>
  <div>
    <header>
      <h1>AI 教辅系统</h1>
      <nav>
        <a href="#">功能</a>
        <a href="#" @click.prevent="goToLogin">登录</a>
        <a href="#" @click.prevent="goToRegister">注册</a>
      </nav>
    </header>

    <section class="hero">
      <h2>让学习更轻松高效</h2>
      <p>基于AI的对话式辅导系统，精准识别知识盲点，智能生成解题方案，陪伴你的每一步学习之旅。</p>
      <button @click="goToDialogue">立即开始对话</button>
    </section>

    <section class="features">
      <div class="feature-card">
        <h3>个性化学习路径</h3>
        <p>根据学习情况自动调整课程节奏与内容。</p>
      </div>
      <div class="feature-card">
        <h3>实时对话解题</h3>
        <p>支持语音或文字提问，AI即时解析与指导。</p>
      </div>
      <div class="feature-card">
        <h3>作业批改与反馈</h3>
        <p>上传作业，系统自动批改并生成分析报告。</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
body {
  margin: 0;
  font-family: "Helvetica Neue", sans-serif;
  background-color: #f9f9f9;
  color: #333;
}

header {
  background-color: #1e40af;
  color: white;
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

header h1 {
  font-size: 24px;
  margin: 0;
}

nav a {
  margin-left: 20px;
  color: white;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
}

.hero {
  text-align: center;
  padding: 80px 20px;
  background: linear-gradient(to right, #3b82f6, #60a5fa);
  color: white;
}

.hero h2 {
  font-size: 36px;
  margin-bottom: 20px;
}

.hero p {
  font-size: 18px;
  max-width: 600px;
  margin: 0 auto 30px;
}

.hero button {
  padding: 12px 24px;
  font-size: 16px;
  background-color: #fff;
  color: #1e40af;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 40px;
  padding: 60px 20px;
  background-color: #ffffff;
}

.feature-card {
  background-color: #f1f5f9;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.05);
  max-width: 300px;
  text-align: center;
}

.feature-card h3 {
  margin-bottom: 10px;
}
</style> 