<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { getAuthHeaders, getCurrentUser } from '../utils/auth';
import { useRouter } from 'vue-router';

const router = useRouter();
const user = getCurrentUser();
const checkInCode = ref('');
const message = ref('');
const status = ref('');
const loading = ref(false);
const activeCheckIns = ref([]);
const studentProfile = ref(null);
const hasCheckedIn = ref(false); // 添加已签到状态标记

// 获取可用的签到活动
const fetchActiveCheckIns = async () => {
  try {
    // 先获取用户的签到历史
    const historyRes = await fetch('http://localhost:8080/api/checkin/history/', {
      headers: getAuthHeaders()
    });
    let userCheckedInIDs = [];
    
    if (historyRes.ok) {
      const historyData = await historyRes.json();
      // 提取已签到的活动ID
      userCheckedInIDs = historyData.map(record => record.check_in_id).filter(Boolean);
    }
    
    // 获取活动的签到
    const res = await fetch('http://localhost:8080/api/checkin/active/', {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const data = await res.json();
      // 过滤掉已签到的活动
      activeCheckIns.value = data
        .filter(item => !userCheckedInIDs.includes(item.id))
        .map(item => ({
          ...item,
          time_left: Math.max(0, Math.floor(item.time_left))
        }));
    }
  } catch (e) {
    console.error('获取签到活动失败:', e);
  }
};

// 检查学生是否已经签到
const checkIfAlreadyCheckedIn = async () => {
  if (!user) return;
  try {
    // 获取当前用户的签到状态
    const res = await fetch('http://localhost:8080/api/checkin/history/', {
      headers: getAuthHeaders()
    });
    
    if (res.ok) {
      const data = await res.json();
      const today = new Date().toISOString().split('T')[0]; // 获取当天日期 YYYY-MM-DD
    }
  } catch (e) {
    console.error('获取签到历史记录失败:', e);
  }
};

const refreshInterval = ref(null);

const handleSubmit = async () => {
  if (!checkInCode.value) {
    message.value = '请输入签到码';
    status.value = 'error';
    return;
  }
  
  loading.value = true;
  message.value = '';
  status.value = '';
  try {
    const res = await fetch('http://localhost:8080/api/checkin/submit/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ 
        check_in_code: checkInCode.value,
        student_name: user?.real_name,
        class_name: user?.student_profile?.class_name,
        notes: '通过移动端签到'
      })
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      // 处理各种错误情况
      const errorMsg = data.check_in_code || data.detail || data.non_field_errors || '签到失败';
      message.value = errorMsg;
      status.value = 'error';
    } else {
      message.value = data.status === 'late' 
        ? '您已迟到签到，请注意下次准时签到' 
        : '签到成功！';
      status.value = 'success';
      checkInCode.value = ''; // 清空签到码输入框
      hasCheckedIn.value = true; // 更新签到状态
      
      // 刷新可用签到活动
      await fetchActiveCheckIns();
    }
  } catch (e) {
    console.error('签到请求出错:', e);
    message.value = '网络错误，签到失败';
    status.value = 'error';
  } finally {
    loading.value = false;
  }
};

// 计算剩余时间的格式化显示
const formatTimeLeft = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}分${secs}秒`;
};

onMounted(async () => {
  // 页面加载时获取可用签到活动
  await fetchActiveCheckIns();
  
  // 检查学生是否已经签到
  await checkIfAlreadyCheckedIn();
  
  // 每1秒刷新一次活动签到列表
  refreshInterval.value = setInterval(fetchActiveCheckIns, 1000);
  
  // 组件卸载时清除定时器
  onBeforeUnmount(() => {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value);
    }
  });
});
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <header class="bg-primary-800 text-white px-6 py-4 shadow-md">
      <div class="container mx-auto flex justify-between items-center">
        <h1 class="text-2xl font-bold">学生签到</h1>
        <router-link to="/index" class="text-white hover:text-primary-200 transition-colors">
          返回主页
        </router-link>
      </div>
    </header>
    
    <div class="container mx-auto px-6 py-8 flex-grow">
      <div class="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
        <h2 class="text-lg font-semibold mb-4">输入签到码进行签到</h2>
        
        <!-- 已签到状态显示 -->
        <div v-if="hasCheckedIn" class="mb-4 p-3 bg-green-100 text-green-800 rounded flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <span>您已完成签到</span>
        </div>
        
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <input v-model="checkInCode" maxlength="6" 
                 placeholder="请输入6位签到码" 
                 class="w-full border border-gray-300 rounded px-3 py-2"
                 autocapitalize="characters" />
          <button type="submit" 
                  class="w-full px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700" 
                  :disabled="loading || hasCheckedIn">
            {{ hasCheckedIn ? '已签到' : (loading ? '签到中...' : '签到') }}
          </button>
        </form>
        
        <div v-if="message" 
             :class="[
               'mt-4 p-3 rounded',
               status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
             ]">
          {{ message }}
        </div>
        
        <!-- 显示当前可用的签到活动 -->
        <div v-if="activeCheckIns.length > 0" class="mt-6">
          <h3 class="text-md font-medium mb-2">当前可签到活动:</h3>
          <div class="space-y-2">
            <div v-for="checkIn in activeCheckIns" :key="checkIn.id" 
                 class="border border-gray-200 rounded p-3 bg-gray-50">
              <div class="font-medium">{{ checkIn.class_name || '未指定班级' }}</div>
              <div class="text-sm text-gray-600">
                剩余时间: {{ formatTimeLeft(checkIn.time_left) }}
              </div>
              <div v-if="checkIn.description" class="text-xs text-gray-500 mt-1">
                {{ checkIn.description }}
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="!loading" class="mt-6 text-center text-gray-500">
          目前没有可用的签到活动
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bg-primary-800 { background-color: #1e293b; }
.bg-primary-600 { background-color: #2563eb; }
.hover\:bg-primary-700:hover { background-color: #1d4ed8; }
.hover\:text-primary-200:hover { color: #bfdbfe; }
</style>
