<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goToRegister = () => {
  router.push('/register')
}

const goToDialogue = () => {
  router.push('/dialogue')
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
          
          <div class="space-y-5">
            <div>
              <input 
                type="text" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="用户名" 
              />
            </div>
            
            <div>
              <input 
                type="password" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="密码" 
              />
            </div>
            
            <div class="flex items-center justify-between">
              <label class="flex items-center text-gray-600">
                <input type="checkbox" class="mr-2">
                记住我
              </label>
              <a href="#" class="text-primary-600 text-sm hover:underline">忘记密码？</a>
            </div>
            
            <button 
              @click="goToDialogue"
              class="w-full bg-primary-600 text-white py-3 rounded-lg hover:bg-primary-700 transition-colors"
            >
              登录
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
          </div>
        </div>
      </div>
    </div>
  </div>
</template>