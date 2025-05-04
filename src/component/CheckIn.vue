<script setup>
import { ref, onMounted, computed, watch } from 'vue';
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

const studentList = ref([]);
const stats = ref({ total: 0, checked: 0, late: 0, absent: 0 });
const timerActive = ref(false);

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
    console.log('正在获取签到活动状态...');
    const res = await fetch('http://localhost:8080/api/checkin/active/', {
      headers: getAuthHeaders()
    });
    console.log('API响应状态码:', res.status);
    if (!res.ok) {
      console.error('获取签到活动失败，状态码:', res.status);
      activeCheckIn.value = null;
      return;
    }
    const data = await res.json();
    console.log('获取到的签到活动数据:', data);
    
    // 检查数据是否为空数组
    if (!data || data.length === 0) {
      console.log('没有活动的签到');
      activeCheckIn.value = null;
      return;
    }
    
    // 直接使用第一个签到活动
    activeCheckIn.value = data[0];
    console.log('设置当前活动签到:', activeCheckIn.value);
    
    if (activeCheckIn.value && activeCheckIn.value.expires_at) {
      updateTimeLeft();
      if (timer) clearInterval(timer);
      timer = setInterval(updateTimeLeft, 1000);
      timerActive.value = activeCheckIn.value.status === 'active';
    } else {
      timeLeft.value = 0;
      timerActive.value = false;
      if (timer) clearInterval(timer);
    }
  } catch (e) {
    console.error('获取签到信息异常:', e);
    activeCheckIn.value = null;
    error.value = '获取签到信息失败';
  }
};

const fetchCheckInStudents = async () => {
  if (!activeCheckIn.value) return;
  try {
    // 获取签到活动的班级
    const className = activeCheckIn.value.class_name;
    if (!className) return;

    // 获取这个班级的所有学生，用于计算总人数和展示缺勤学生
    const studentsRes = await fetch(`http://localhost:8080/api/students/profiles/?class_name=${encodeURIComponent(className)}`, {
      headers: getAuthHeaders()
    });
    
    let allClassStudents = [];
    
    if (studentsRes.ok) {
      const studentsData = await studentsRes.json();
      allClassStudents = studentsData.filter(s => s.class_name === className);
      stats.value.total = allClassStudents.length;
    }
    
    // 获取当前签到的学生列表
    const res = await fetch(`http://localhost:8080/api/checkin/${activeCheckIn.value.id}/students/`, {
      headers: getAuthHeaders()
    });
    
    if (!res.ok) return;
    
    const checkedInData = await res.json();
    
    // 标记已签到学生的ID
    const checkedInIds = new Set(checkedInData.map(s => s.student));
    
    // 创建完整的学生列表，包括已签到和未签到的
    studentList.value = [
      ...checkedInData,
      // 添加未签到（缺勤）的学生
      ...allClassStudents
        .filter(s => !checkedInIds.has(s.student?.id))
        .map(s => ({
          id: 'absent_' + s.student?.id,
          student: s.student?.id,
          student_name: s.student_name || s.real_name || s.student?.username,
          check_in_time: null,
          check_in_time_display: '-',
          status: 'absent',
          notes: '未签到',
          class_name: s.class_name
        }))
    ];
    
    // 更新签到统计
    stats.value.checked = checkedInData.filter(s => s.status === 'success').length;
    stats.value.late = checkedInData.filter(s => s.status === 'late').length;
    stats.value.absent = stats.value.total - stats.value.checked - stats.value.late;
  } catch (e) {
    console.error('获取签到学生信息失败:', e);
  }
};

watch(activeCheckIn, fetchCheckInStudents);

function updateTimeLeft() {
  if (!activeCheckIn.value || !activeCheckIn.value.expires_at) return;
  const expire = new Date(activeCheckIn.value.expires_at).getTime();
  const now = Date.now();
  timeLeft.value = Math.max(0, Math.floor((expire - now) / 1000));
  
  if (timeLeft.value > 0) {
    timerActive.value = true;
    
    // 每10秒刷新一次签到状态
    if (timeLeft.value % 10 === 0) {
      fetchCheckInStudents();
    }
  } else {
    timerActive.value = false;
    if (timer) clearInterval(timer);
    
    // 倒计时结束时更新签到活动状态
    if (activeCheckIn.value && activeCheckIn.value.status === 'active') {
      // 如果签到仍处于活动状态，自动标记为已过期，但不结束签到
      activeCheckIn.value.status = 'expired';
      // 刷新学生签到状态，显示迟到学生
      fetchCheckInStudents();
    }
  }
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
    
    // 重置表单
    form.value = { class_name: '', check_in_code: '', valid_minutes: 10, description: '' };
    
    // 获取创建的签到活动
    await fetchActiveCheckIn();
    
    // 获取学生签到状态
    await fetchCheckInStudents();
    
    // 启动倒计时
    if (timer) clearInterval(timer);
    updateTimeLeft();
    timer = setInterval(updateTimeLeft, 1000);
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
    await fetchCheckInStudents();
  } catch (e) {
    error.value = '结束签到失败';
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await fetchClassList();
  await fetchActiveCheckIn();
  await fetchCheckInStudents();
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
        <div class="mb-2">班级：{{ activeCheckIn.class_name }}</div>
        <div class="mb-2">剩余时间：<span class="text-orange-600">{{ timeLeft }} 秒</span></div>
        <div class="mb-2">签到说明：{{ activeCheckIn.description || '无' }}</div>
        <div class="mb-4 mt-4">
          <div class="font-semibold mb-2">签到统计：</div>
          <div class="flex gap-6 mb-2">
            <span>已签到：<span class="text-green-600">{{ stats.checked + stats.late }}</span></span>
            <span>待签到：<span class="text-gray-600">{{ stats.total - stats.checked - stats.late }}</span></span>
            <span>迟到：<span class="text-orange-600">{{ stats.late }}</span></span>
            <span>总人数：<span>{{ stats.total }}</span></span>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-sm border">
              <thead>
                <tr>
                  <th class="px-2 py-1 border">姓名</th>
                  <th class="px-2 py-1 border">学号</th>
                  <th class="px-2 py-1 border">签到时间</th>
                  <th class="px-2 py-1 border">状态</th>
                  <th class="px-2 py-1 border">备注</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="stu in studentList" :key="stu.id" 
                    :class="{'bg-orange-100': stu.status === 'late'}">
                  <td class="border px-2 py-1">{{ stu.student_name }}</td>
                  <td class="border px-2 py-1">{{ stu.student }}</td>
                  <td class="border px-2 py-1">{{ stu.check_in_time_display }}</td>
                  <td class="border px-2 py-1">
                    <span v-if="stu.status === 'success'" class="text-green-600">正常</span>
                    <span v-else-if="stu.status === 'late'" class="text-orange-600">迟到</span>
                    <span v-else class="text-red-600">缺勤</span>
                  </td>
                  <td class="border px-2 py-1">{{ stu.notes }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <button v-if="timerActive" @click="handleEndCheckIn" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">结束签到</button>
        <div v-else class="mt-4 text-orange-700 font-semibold">签到已到期，迟到学生已高亮显示</div>
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
