<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goToRegister = () => {
  router.push('/register')
}
// 组件逻辑部分
</script>

<template>
  <div class="browser-frame">
    <div class="browser-controls">
      <div class="circle red"></div>
      <div class="circle yellow"></div>
      <div class="circle green"></div>
    </div>
    <div class="login-card">
      <h2>登录</h2>
      <input type="text" class="input-field" placeholder="用户名" />
      <input type="password" class="input-field" placeholder="密码" />
      <button class="login-button">登录</button>
      <p class="login-link">没有账号？<a href="#" @click.prevent="goToRegister">立即注册</a></p>
    </div>
  </div>
</template>

<style scoped>
body {
  margin: 0;
  font-family: Arial, sans-serif;
  background-color: #f5f5f5;
}

.browser-frame {
  width: 400px;
  margin: 80px auto;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.browser-controls {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
}

.circle {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.red { background-color: #ff5f56; }
.yellow { background-color: #ffbd2e; }
.green { background-color: #27c93f; }

.login-card {
  padding: 32px 24px;
}

.login-card h2 {
  margin: 0 0 24px;
  text-align: center;
}

.input-field {
  width: 94%;
  padding: 10px;
  margin-bottom: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.login-button {
  width: 100%;
  padding: 10px;
  background-color: #007bff;
  color: white;
  font-size: 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.login-button:hover {
  background-color: #0056b3;
}
</style> 