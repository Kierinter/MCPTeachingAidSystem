<script setup>
import { useRouter } from 'vue-router'
import { ref } from 'vue'

const router = useRouter()

// 表单数据
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const email = ref('')
const school = ref('')
const major = ref('')

// 状态管理
const isSubmitting = ref(false)
const errorMessage = ref('')
const registerSuccess = ref(false)

const goToLogin = () => {
  router.push('/login')
}

const handleRegister = async () => {
  // 重置错误信息
  errorMessage.value = ''
  
  // 表单验证
  if (!username.value || !password.value || !confirmPassword.value) {
    errorMessage.value = '请填写必填字段'
    return
  }
  
  if (password.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }
  
  if (password.value.length < 8) {
    errorMessage.value = '密码长度不能少于8个字符'
    return
  }
  
  // 设置提交状态
  isSubmitting.value = true
  
  try {
    // 调用注册API
    const response = await fetch('http://localhost:8000/api/users/register/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
        email: email.value,
        school: school.value,
        major: major.value
      }),
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      // 处理错误响应
      if (data.username) {
        errorMessage.value = `用户名错误: ${data.username}`
      } else if (data.password) {
        errorMessage.value = `密码错误: ${data.password}`
      } else if (data.email) {
        errorMessage.value = `邮箱错误: ${data.email}`
      } else {
        errorMessage.value = '注册失败，请检查输入信息'
      }
      return
    }
    
    // 注册成功处理
    console.log('注册成功:', data)
    registerSuccess.value = true
    
    // 保存认证令牌和用户信息到本地存储
    localStorage.setItem('authToken', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    
    // 跳转到登录页面
    setTimeout(() => {
      router.push('/login')
    }, 1500)
    
  } catch (error) {
    console.error('注册请求错误:', error)
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
          <h2 class="text-2xl font-bold text-center text-gray-800 mb-8">注册</h2>
          
          <!-- 成功消息 -->
          <div v-if="registerSuccess" class="mb-6 bg-green-100 text-green-800 p-3 rounded-lg text-center animate-fade-in">
            注册成功，即将跳转到登录页面...
          </div>
          
          <!-- 错误消息 -->
          <div v-if="errorMessage" class="mb-6 bg-red-100 text-red-800 p-3 rounded-lg text-center animate-fade-in">
            {{ errorMessage }}
          </div>
          
          <form @submit.prevent="handleRegister" class="space-y-5">
            <div>
              <input 
                v-model="username"
                type="text" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="用户名 *" 
                :disabled="isSubmitting"
                required
              />
            </div>
            
            <div>
              <input 
                v-model="email"
                type="email" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="电子邮箱" 
                :disabled="isSubmitting"
              />
            </div>
            
            <div>
              <input 
                v-model="password"
                type="password" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="密码 *" 
                :disabled="isSubmitting"
                required
              />
              <p class="text-xs text-gray-500 mt-1">密码长度至少8个字符</p>
            </div>
            
            <div>
              <input 
                v-model="confirmPassword"
                type="password" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="确认密码 *"
                :disabled="isSubmitting" 
                required
              />
            </div>
            
            <div>
              <input 
                v-model="school"
                type="text" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="学校" 
                :disabled="isSubmitting"
              />
            </div>
            
            <div>
              <input 
                v-model="major"
                type="text" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="专业" 
                :disabled="isSubmitting"
              />
            </div>
            
            <button 
              type="submit"
              class="w-full bg-primary-600 text-white py-3 rounded-lg hover:bg-primary-700 transition-colors disabled:bg-gray-400"
              :disabled="isSubmitting"
            >
              {{ isSubmitting ? '注册中...' : '注册' }}
            </button>
            
            <p class="text-center text-gray-600 mt-4">
              已有账号？
              <a 
                href="#" 
                @click.prevent="goToLogin" 
                class="text-primary-600 hover:underline"
              >
                返回登录
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