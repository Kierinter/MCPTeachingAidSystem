<script setup>
import { ref, onMounted} from 'vue';
import { getAuthHeaders, getCurrentUser } from '../utils/auth';
import { useRouter } from 'vue-router';

const router = useRouter();
const user = getCurrentUser();
if (!user || user.role !== 'teacher') {
  router.push('/index');
}

const courses = ref([]);
const loading = ref(false);
const error = ref('');
const activeCheckIn = ref(null);
const classList = ref([]);
const form = ref({
  class_name: '',
  check_in_code: '',
  valid_minutes: 10,
  description: ''
});
const timeLeft = ref(0);
let timer = null;

const fetchClassList = async () => {
  loading.value = true;
  try {
    const res = await fetch('http://localhost:8080/api/students/profiles/', {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('加载班级信息失败');
    const data = await res.json();
    // 提取所有班级名并去重
    const set = new Set();
    data.forEach(stu => {
      if (stu.class_name) set.add(stu.class_name);
    });
    classList.value = Array.from(set);
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};

const fetchActiveCheckIn = async () => {
  try {
    const res = await fetch('http://localhost:8080/api/checkin/courses/active/', {
      headers: getAuthHeaders()
    });
    if (!res.ok) {
      activeCheckIn.value = null;
      return;
    }
    const data = await res.json();
    // 只取第一个有签到码的活动
    activeCheckIn.value = (data.find(c => c.check_in_code) || null);
    if (activeCheckIn.value && activeCheckIn.value.expires_at) {
      updateTimeLeft();
      if (timer) clearInterval(timer);
      timer = setInterval(updateTimeLeft, 1000);
    } else {
      timeLeft.value = 0;
      if (timer) clearInterval(timer);
    }
  } catch (e) {
    activeCheckIn.value = null;
  }
};

function updateTimeLeft() {
  if (!activeCheckIn.value || !activeCheckIn.value.expires_at) return;
  const expire = new Date(activeCheckIn.value.expires_at).getTime();
  const now = Date.now();
  timeLeft.value = Math.max(0, Math.floor((expire - now) / 1000));
  if (timeLeft.value === 0 && timer) clearInterval(timer);
}

function randomCode() {
  // 生成6位字母数字签到码
  form.value.check_in_code = Math.random().toString(36).slice(-6).toUpperCase();
}

const handleCreateCheckIn = async () => {
  if (!form.value.class_name || !form.value.check_in_code) {
    error.value = '请选择班级并生成签到码';
    return;
  }
  loading.value = true;
  error.value = '';
  try {
    const res = await fetch('http://localhost:8080/api/checkin/create/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(form.value)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || '发起签到失败');
    await fetchActiveCheckIn();
    // 重置表单
    form.value = { class_name: '', check_in_code: '', valid_minutes: 10, description: '' };
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};

const handleEndCheckIn = async () => {
  if (!activeCheckIn.value) return;
  loading.value = true;
  try {
    const res = await fetch(`http://localhost:8080/api/checkin/end/${activeCheckIn.value.id}/`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    await fetchActiveCheckIn();
  } catch (e) {
    error.value = '结束签到失败';
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await fetchClassList();
  await fetchActiveCheckIn();
});
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <header class="bg-primary-800 text-white px-6 py-4 shadow-md">
      <div class="container mx-auto flex justify-between items-center">
        <h1 class="text-2xl font-bold">课堂签到管理</h1>
        <router-link to="/index" class="text-white hover:text-primary-200 transition-colors">
          返回主页
        </router-link>
      </div>
    </header>
    <div class="container mx-auto px-6 py-8 flex-grow">
      <div v-if="error" class="bg-red-100 text-red-800 p-3 rounded mb-4">{{ error }}</div>
      <div v-if="activeCheckIn" class="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 class="text-lg font-semibold mb-2">当前签到进行中</h2>
        <div class="mb-2">签到码：<span class="font-mono text-xl text-primary-600">{{ activeCheckIn.check_in_code }}</span></div>
        <div class="mb-2">剩余时间：<span class="text-orange-600">{{ timeLeft }} 秒</span></div>
        <div class="mb-2">签到说明：{{ activeCheckIn.description || '无' }}</div>
        <button @click="handleEndCheckIn" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">结束签到</button>
      </div>
      <div v-else class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-lg font-semibold mb-4">发起新的签到</h2>
        <form @submit.prevent="handleCreateCheckIn" class="space-y-4">
          <div>
            <label class="block text-gray-700 text-sm mb-1">选择班级</label>
            <select v-model="form.class_name" class="w-full border border-gray-300 rounded px-3 py-2">
              <option value="">请选择</option>
              <option v-for="c in classList" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div>
            <label class="block text-gray-700 text-sm mb-1">签到码</label>
            <div class="flex gap-2">
              <input v-model="form.check_in_code" class="border border-gray-300 rounded px-3 py-2 flex-1" maxlength="6" />
              <button type="button" @click="randomCode" class="px-3 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">生成</button>
            </div>
          </div>
          <div>
            <label class="block text-gray-700 text-sm mb-1">有效时长（分钟）</label>
            <input v-model.number="form.valid_minutes" type="number" min="1" max="180" class="border border-gray-300 rounded px-3 py-2 w-32" />
          </div>
          <div>
            <label class="block text-gray-700 text-sm mb-1">签到说明</label>
            <textarea v-model="form.description" class="w-full border border-gray-300 rounded px-3 py-2"></textarea>
          </div>
          <div class="flex justify-end">
            <button type="submit" class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700" :disabled="loading">发起签到</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bg-primary-800 { background-color: #1e293b; }
.bg-primary-600 { background-color: #2563eb; }
.text-primary-600 { color: #2563eb; }
.text-primary-200 { color: #bfdbfe; }
.hover\:bg-primary-700:hover { background-color: #1d4ed8; }
.hover\:text-primary-200:hover { color: #bfdbfe; }
</style>
