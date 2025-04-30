<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// 状态管理
const currentCourses = ref([
  {
    id: 1,
    name: '高等数学 (II)',
    teacher: '张教授',
    location: '理科楼 A304',
    time: '10:00 - 11:40',
    date: '2025-04-30',
    isActive: true,
    checkInCode: '853421',
    expiresAt: new Date(Date.now() + 15 * 60 * 1000) // 15分钟后过期
  },
  {
    id: 2,
    name: '线性代数',
    teacher: '李教授',
    location: '综合楼 B201',
    time: '14:30 - 16:10',
    date: '2025-04-30',
    isActive: true,
    checkInCode: '284695',
    expiresAt: new Date(Date.now() + 5 * 60 * 1000) // 5分钟后过期
  }
]);

const upcomingCourses = ref([
  {
    id: 3,
    name: '概率论与数理统计',
    teacher: '王教授',
    location: '理科楼 A201',
    time: '08:00 - 09:40',
    date: '2025-05-01',
  },
  {
    id: 4,
    name: '数据结构',
    teacher: '陈教授',
    location: '计算机楼 C305',
    time: '10:00 - 11:40',
    date: '2025-05-01',
  }
]);

const historyCheckIns = ref([
  {
    id: 101,
    courseName: '高等数学 (II)',
    checkInTime: '2025-04-28 10:05',
    status: 'success',
    location: '理科楼 A304'
  },
  {
    id: 102,
    courseName: '线性代数',
    checkInTime: '2025-04-28 14:32',
    status: 'success',
    location: '综合楼 B201'
  },
  {
    id: 103,
    courseName: '高等数学 (II)',
    checkInTime: '2025-04-23 10:12',
    status: 'success',
    location: '理科楼 A304'
  },
  {
    id: 104,
    courseName: '数据结构',
    checkInTime: '2025-04-23 10:00',
    status: 'late',
    location: '计算机楼 C305'
  },
  {
    id: 105,
    courseName: '概率论与数理统计',
    checkInTime: '2025-04-20 08:15',
    status: 'late',
    location: '理科楼 A201'
  }
]);

// 签到码输入
const checkInCode = ref('');
const showCheckInDialog = ref(false);
const selectedCourse = ref(null);
const isSubmitting = ref(false);
const checkInResult = ref({ show: false, success: false, message: '' });

// 检查是否当前日期课程
const isToday = (dateString) => {
  const today = new Date().toISOString().slice(0, 10);
  return dateString === today;
};

// 计算剩余签到时间
const getTimeLeft = (expiresAt) => {
  const now = new Date();
  const diff = expiresAt - now;
  
  if (diff <= 0) return '已过期';
  
  const minutes = Math.floor(diff / (1000 * 60));
  const seconds = Math.floor((diff % (1000 * 60)) / 1000);
  
  return `${minutes}分${seconds}秒`;
};

// 打开签到对话框
const openCheckInDialog = (course) => {
  selectedCourse.value = course;
  checkInCode.value = '';
  showCheckInDialog.value = true;
};

// 提交签到
const submitCheckIn = async () => {
  isSubmitting.value = true;
  
  // 模拟签到验证过程
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 检查签到码是否正确
  if (checkInCode.value === selectedCourse.value.checkInCode) {
    // 签到成功
    checkInResult.value = {
      show: true,
      success: true,
      message: '签到成功！'
    };
    
    // 添加到签到历史
    historyCheckIns.value.unshift({
      id: Date.now(),
      courseName: selectedCourse.value.name,
      checkInTime: new Date().toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }).replace(/\//g, '-'),
      status: 'success',
      location: selectedCourse.value.location
    });
  } else {
    // 签到失败
    checkInResult.value = {
      show: true,
      success: false,
      message: '签到码错误，请重新输入！'
    };
  }
  
  isSubmitting.value = false;
  
  // 3秒后关闭结果提示
  setTimeout(() => {
    if (checkInResult.value.success) {
      showCheckInDialog.value = false;
      checkInResult.value.show = false;
    } else {
      checkInResult.value.show = false;
    }
  }, 3000);
};

// 关闭签到对话框
const closeCheckInDialog = () => {
  showCheckInDialog.value = false;
  selectedCourse.value = null;
};

// 返回主页
const goToHome = () => {
  router.push('/');
};

// 实时更新剩余时间
const startTimeCountdown = () => {
  setInterval(() => {
    // 强制更新组件
    currentCourses.value = [...currentCourses.value];
  }, 1000);
};

onMounted(() => {
  startTimeCountdown();
});
</script>

<template>
  <div class="min-h-screen bg-gray-100 py-8">
    <div class="max-w-4xl mx-auto px-4">
      <!-- 顶部导航 -->
      <div class="flex justify-between items-center mb-8">
        <h1 class="text-2xl font-bold text-gray-800">课堂签到</h1>
        <button @click="goToHome" class="text-primary-600 hover:text-primary-800 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clip-rule="evenodd" />
          </svg>
          返回首页
        </button>
      </div>

      <!-- 当日课程 -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">今日课程</h2>
        
        <div v-if="currentCourses.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="course in currentCourses" :key="course.id" 
              class="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-lg font-semibold text-gray-800">{{ course.name }}</h3>
                <p class="text-gray-600 text-sm mt-1">{{ course.teacher }} | {{ course.location }}</p>
                <p class="text-gray-600 text-sm mt-1">{{ course.time }}</p>
                
                <div class="mt-4 flex items-center">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    签到码有效时间: {{ getTimeLeft(course.expiresAt) }}
                  </span>
                </div>
              </div>
              
              <button @click="openCheckInDialog(course)" 
                  class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700 transition-colors">
                立即签到
              </button>
            </div>
          </div>
        </div>
        
        <div v-else class="bg-white rounded-xl shadow-sm p-6 text-center">
          <p class="text-gray-600">今日没有需要签到的课程</p>
        </div>
      </div>
      
      <!-- 即将到来的课程 -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">即将到来的课程</h2>
        
        <div class="bg-white rounded-xl shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    课程名称
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    教师
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    地点
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    时间
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    日期
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="course in upcomingCourses" :key="course.id">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ course.name }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ course.teacher }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ course.location }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ course.time }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ course.date }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <!-- 签到历史 -->
      <div>
        <h2 class="text-xl font-semibold text-gray-800 mb-4">签到历史</h2>
        
        <div class="bg-white rounded-xl shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    课程名称
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    签到时间
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    地点
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="record in historyCheckIns" :key="record.id">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ record.courseName }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ record.checkInTime }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ record.location }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span v-if="record.status === 'success'" 
                          class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      正常
                    </span>
                    <span v-else-if="record.status === 'late'" 
                          class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                      迟到
                    </span>
                    <span v-else-if="record.status === 'absent'" 
                          class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                      缺勤
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 签到对话框 -->
    <div v-if="showCheckInDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4">
        <div class="text-center mb-4">
          <h3 class="text-xl font-bold text-gray-800">
            {{ selectedCourse ? selectedCourse.name : '' }} 课程签到
          </h3>
          <p class="text-gray-600 mt-1">请输入教师提供的签到码</p>
        </div>
        
        <div class="mb-6">
          <input type="text" v-model="checkInCode" 
                 class="w-full px-4 py-3 border border-gray-300 rounded-lg text-center text-2xl tracking-widest focus:outline-none focus:ring-2 focus:ring-primary-500"
                 placeholder="请输入6位数字签到码"
                 maxlength="6"
                 pattern="[0-9]*"
                 inputmode="numeric"
                 :disabled="isSubmitting" />
        </div>
        
        <div class="flex space-x-3">
          <button @click="closeCheckInDialog" 
                  class="w-1/2 py-3 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-100 transition-colors"
                  :disabled="isSubmitting">
            取消
          </button>
          <button @click="submitCheckIn" 
                  class="w-1/2 bg-primary-600 text-white py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors"
                  :disabled="isSubmitting || checkInCode.length !== 6">
            {{ isSubmitting ? '提交中...' : '确认签到' }}
          </button>
        </div>
        
        <!-- 签到结果提示 -->
        <div v-if="checkInResult.show" 
             :class="[
               'mt-4 p-3 rounded-lg text-center',
               checkInResult.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
             ]">
          {{ checkInResult.message }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 确保表格在小屏幕上可以滚动 */
.overflow-x-auto {
  -webkit-overflow-scrolling: touch;
}

/* 输入框聚焦效果 */
input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}
</style>