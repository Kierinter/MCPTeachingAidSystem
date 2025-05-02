<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ref } from 'vue'
import { setAuth } from '../utils/auth'

const router = useRouter()
const route = useRoute()

// 表单数据
const username = ref('')
const password = ref('')
const rememberMe = ref(false)

// 状态管理
const isSubmitting = ref(false)
const errorMessage = ref('')
const loginSuccess = ref(false)

const goToRegister = () => {
  router.push('/register')
}

const goToDialogue = () => {
  router.push('/dialogue')
}

const handleLogin = async () => {
  // 重置错误信息
  errorMessage.value = ''
  
  // 表单验证
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }
  
  // 设置提交状态
  isSubmitting.value = true
  
  try {
    // 调用登录API
    const response = await fetch('http://localhost:8080/api/users/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
      }),
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      // 处理错误响应
      errorMessage.value = data.detail || data.non_field_errors || '登录失败，请检查用户名和密码'
      return
    }
    
    // 登录成功，保存令牌和用户信息
    setAuth(data.token, data.user)
    
    // 如果有重定向，则跳转到原目标页面，否则跳转到主页
    const redirectPath = route.query.redirect || '/index'
    router.push(redirectPath)
    
  } catch (error) {
    console.error('登录请求错误:', error)
    errorMessage.value = '网络错误，请稍后重试'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex justify-center items-center p-4">
    <div class="w-full max-w-md">
      <div class="bg-white rounded-lg shadow-lg overflow-hidden">
        <div class="px-6 py-3 bg-gray-100 border-b border-gray-200 flex items-center space-x-2">
          <div class="w-3 h-3 rounded-full bg-red-500"></div>
          <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
          <div class="w-3 h-3 rounded-full bg-green-500"></div>
        </div>
        
        <div class="p-8">
          <h2 class="text-2xl font-bold text-center text-gray-800 mb-8">登录</h2>
          
          <!-- 成功消息 -->
          <div v-if="loginSuccess" class="mb-6 bg-green-100 text-green-800 p-3 rounded-lg text-center animate-fade-in">
            登录成功，正在跳转...
          </div>
          
          <!-- 错误消息 -->
          <div v-if="errorMessage" class="mb-6 bg-red-100 text-red-800 p-3 rounded-lg text-center animate-fade-in">
            {{ errorMessage }}
          </div>
          
          <form @submit.prevent="handleLogin" class="space-y-5">
            <div>
              <input 
                v-model="username"
                type="text" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="用户名" 
                :disabled="isSubmitting"
                required
              />
            </div>
            
            <div>
              <input 
                v-model="password"
                type="password" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="密码"
                :disabled="isSubmitting" 
                required
              />
            </div>
            
            <div class="flex items-center justify-between">
              <label class="flex items-center text-gray-600">
                <input v-model="rememberMe" type="checkbox" class="mr-2">
                记住我
              </label>
              <a href="#" class="text-primary-600 text-sm hover:underline">忘记密码？</a>
            </div>
            
            <button 
              type="submit"
              class="w-full bg-primary-600 text-white py-3 rounded-lg hover:bg-primary-700 transition-colors disabled:bg-gray-400"
              :disabled="isSubmitting"
            >
              {{ isSubmitting ? '登录中...' : '登录' }}
            </button>
            
            <p class="text-center text-gray-600 mt-4">
              没有账号？
              <a 
                href="#" 
                @click.prevent="goToRegister" 
                class="text-primary-600 hover:underline"
              >
                立即注册
              </a>
            </p>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}
</style>