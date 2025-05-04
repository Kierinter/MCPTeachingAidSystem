<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getCurrentUser, getAuthHeaders } from '../utils/auth';

const router = useRouter();

// 获取用户信息
const currentUser = ref(null);
const userRole = computed(() => currentUser.value?.role || 'student');
const isTeacher = computed(() => userRole.value === 'teacher');

// API基础URL
const API_BASE_URL = 'http://localhost:8080/api';

// 状态管理
const currentCourses = ref([]);
const upcomingCourses = ref([]);
const historyCheckIns = ref([]);

// 签到码输入
const checkInCode = ref('');
const showCheckInDialog = ref(false);
const selectedCourse = ref(null);
const isSubmitting = ref(false);
const checkInResult = ref({ show: false, success: false, message: '' });

// 添加教师相关数据和功能
const teacherCourses = ref([]);
const showCreateCheckInModal = ref(false);
const currentTeacherCourse = ref(null);
const newCheckInData = ref({
  courseId: null,
  courseName: '',
  checkInCode: '',
  validMinutes: 15,
  customCode: false,
  description: '',
});

// 添加加载状态
const isLoading = ref(false);
const loadingError = ref(null);

// 生成随机签到码
const generateRandomCode = () => {
  return Math.floor(100000 + Math.random() * 900000).toString();
};

// 打开创建签到模态框
const openCreateCheckInModal = (course) => {
  currentTeacherCourse.value = course;
  newCheckInData.value = {
    courseId: course.id,
    courseName: course.name,
    checkInCode: generateRandomCode(),
    validMinutes: 15,
    customCode: false,
    description: '',
  };
  showCreateCheckInModal.value = true;
};

// 切换是否使用自定义签到码
const toggleCustomCode = () => {
  newCheckInData.value.customCode = !newCheckInData.value.customCode;
  if (!newCheckInData.value.customCode) {
    newCheckInData.value.checkInCode = generateRandomCode();
  } else {
    newCheckInData.value.checkInCode = '';
  }
};

// 创建签到
const createCheckIn = async () => {
  isSubmitting.value = true;

  try {
    // 向后端API发送创建签到的请求
    const response = await fetch(`${API_BASE_URL}/courses/check-in/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        courseId: currentTeacherCourse.value.id,
        checkInCode: newCheckInData.value.checkInCode,
        validMinutes: newCheckInData.value.validMinutes,
        description: newCheckInData.value.description
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '创建签到失败');
    }

    const data = await response.json();

    // 更新当前课程的签到信息
    await loadActiveCourses();

    // 提示创建成功
    alert(`签到已创建成功！签到码: ${newCheckInData.value.checkInCode}`);

    // 关闭模态框
    showCreateCheckInModal.value = false;
  } catch (error) {
    console.error('创建签到失败:', error);
    alert('创建签到失败，请稍后重试: ' + error.message);
  } finally {
    isSubmitting.value = false;
  }
};

// 检查是否当前日期课程
const isToday = (dateString) => {
  const today = new Date().toISOString().slice(0, 10);
  return dateString === today;
};

// 计算剩余签到时间
const getTimeLeft = (expiresAt) => {
  const now = new Date();
  const expireDate = new Date(expiresAt);
  const diff = expireDate - now;

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

  try {
    // 调用后端签到API
    const response = await fetch(`${API_BASE_URL}/courses/check-in/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        courseId: selectedCourse.value.id,
        checkInCode: checkInCode.value
      }),
    });

    // 处理响应
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '签到失败');
    }

    const data = await response.json();

    // 签到成功
    checkInResult.value = {
      show: true,
      success: true,
      message: '签到成功！'
    };

    // 更新签到历史
    await loadCheckInHistory();

    // 3秒后关闭结果提示并关闭对话框
    setTimeout(() => {
      showCheckInDialog.value = false;
      checkInResult.value.show = false;
    }, 3000);
  } catch (error) {
    console.error('签到失败:', error);

    // 签到失败
    checkInResult.value = {
      show: true,
      success: false,
      message: `签到失败：${error.message}`
    };

    // 3秒后关闭结果提示
    setTimeout(() => {
      checkInResult.value.show = false;
    }, 3000);
  } finally {
    isSubmitting.value = false;
  }
};

// 关闭签到对话框
const closeCheckInDialog = () => {
  showCheckInDialog.value = false;
  selectedCourse.value = null;
};

// 返回主页
const goToHome = () => {
  router.push('/index');
};

// 实时更新剩余时间
const startTimeCountdown = () => {
  setInterval(() => {
    // 强制更新组件
    currentCourses.value = [...currentCourses.value];
  }, 1000);
};

// 加载活动课程数据
const loadActiveCourses = async () => {
  isLoading.value = true;
  loadingError.value = null;

  try {
    // 调用后端API获取当前课程
    const response = await fetch(`${API_BASE_URL}/courses/active`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('加载当前课程失败');
    }

    const data = await response.json();

    // 格式化数据，确保expiresAt是Date对象
    currentCourses.value = data.map(course => ({
      ...course,
      expiresAt: course.expiresAt ? new Date(course.expiresAt) : null
    }));

  } catch (error) {
    console.error('加载活动课程失败:', error);
    loadingError.value = '加载活动课程失败，请刷新页面重试';

    // 使用模拟数据（仅在开发环境）
    if (process.env.NODE_ENV === 'development') {
      currentCourses.value = [
        {
          id: 1,
          name: '高等数学 (II)',
          teacher: '张教授',
          location: '理科楼 A304',
          time: '10:00 - 11:40',
          date: '2025-04-30',
          isActive: true,
          checkInCode: '853421',
          expiresAt: new Date(Date.now() + 15 * 60 * 1000)
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
          expiresAt: new Date(Date.now() + 5 * 60 * 1000)
        }
      ];
    }
  } finally {
    isLoading.value = false;
  }
};

// 加载即将到来的课程数据
const loadUpcomingCourses = async () => {
  try {
    // 调用后端API获取即将到来的课程
    const response = await fetch(`${API_BASE_URL}/courses/upcoming`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('加载即将到来的课程失败');
    }

    const data = await response.json();
    upcomingCourses.value = data;
  } catch (error) {
    console.error('加载即将到来的课程失败:', error);

    // 使用模拟数据（仅在开发环境）
    if (process.env.NODE_ENV === 'development') {
      upcomingCourses.value = [
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
      ];
    }
  }
};

// 加载签到历史记录
const loadCheckInHistory = async () => {
  try {
    // 调用后端API获取签到历史
    const response = await fetch(`${API_BASE_URL}/courses/check-in/history`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('加载签到历史失败');
    }

    const data = await response.json();
    historyCheckIns.value = data;
  } catch (error) {
    console.error('加载签到历史失败:', error);

    // 使用模拟数据（仅在开发环境）
    if (process.env.NODE_ENV === 'development') {
      historyCheckIns.value = [
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
      ];
    }
  }
};

// 加载教师课程数据
const loadTeacherCourses = async () => {
  try {
    // 调用后端API获取教师课程
    const response = await fetch(`${API_BASE_URL}/courses/teacher`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('加载教师课程失败');
    }

    const data = await response.json();
    teacherCourses.value = data;

    // 更新当前课程
    currentCourses.value = teacherCourses.value.filter(course => isToday(course.date));
  } catch (error) {
    console.error('加载教师课程失败:', error);

    // 使用模拟数据（仅在开发环境）
    if (process.env.NODE_ENV === 'development') {
      teacherCourses.value = [
        {
          id: 1,
          name: '高等数学 (II)',
          location: '理科楼 A304',
          time: '10:00 - 11:40',
          date: '2025-04-30',
          studentCount: 45,
          checkInStatus: '未开始'
        },
        {
          id: 2,
          name: '线性代数',
          location: '综合楼 B201',
          time: '14:30 - 16:10',
          date: '2025-04-30',
          studentCount: 38,
          checkInStatus: '未开始'
        },
        {
          id: 3,
          name: '概率论与数理统计',
          location: '理科楼 A201',
          time: '08:00 - 09:40',
          date: '2025-05-01',
          studentCount: 40,
          checkInStatus: '未开始'
        },
      ];

      // 更新当前课程
      currentCourses.value = teacherCourses.value.filter(course => isToday(course.date));
    }
  }
};

// 查看签到详情（教师功能）
const viewCheckInDetails = async (courseId) => {
  try {
    // 跳转到签到详情页面
    router.push(`/checkin-details/${courseId}`);
  } catch (error) {
    console.error('导航到签到详情页失败:', error);
    alert('无法查看签到详情，请稍后重试');
  }
};

// 根据用户角色加载数据
const loadUserData = async () => {
  try {
    if (isTeacher.value) {
      // 加载教师课程数据
      await loadTeacherCourses();
    } else {
      // 加载学生数据
      await loadActiveCourses();
      await loadUpcomingCourses();
      await loadCheckInHistory();
    }
  } catch (error) {
    console.error('加载数据失败:', error);
  }
};

onMounted(() => {
  // 获取当前用户信息
  currentUser.value = getCurrentUser();

  // 启动倒计时更新
  startTimeCountdown();

  // 根据角色加载不同数据
  loadUserData();
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
            <path fill-rule="evenodd"
              d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
              clip-rule="evenodd" />
          </svg>
          返回首页
        </button>
      </div>

      <!-- 教师界面 -->
      <div v-if="isTeacher">
        <!-- 教师当日课程 -->
        <div class="mb-8">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold text-gray-800">今日课程</h2>
          </div>

          <div v-if="currentCourses.length > 0" class="grid grid-cols-1 gap-4">
            <div v-for="course in currentCourses" :key="course.id"
              class="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
              <div class="flex justify-between items-start">
                <div>
                  <h3 class="text-lg font-semibold text-gray-800">{{ course.name }}</h3>
                  <p class="text-gray-600 text-sm mt-1">{{ course.location }}</p>
                  <p class="text-gray-600 text-sm mt-1">{{ course.time }} | 学生人数: {{ course.studentCount || 0 }}人</p>

                  <!-- 显示签到状态 -->
                  <div v-if="course.isActive" class="mt-3">
                    <div class="flex items-center space-x-2">
                      <span
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <span class="w-2 h-2 bg-green-600 rounded-full mr-1"></span>签到中
                      </span>
                      <span class="text-sm text-gray-600">
                        签到码: <span class="font-medium">{{ course.checkInCode }}</span>
                      </span>
                      <span class="text-sm text-gray-600">
                        剩余: {{ getTimeLeft(course.expiresAt) }}
                      </span>
                    </div>
                  </div>
                </div>

                <button v-if="!course.isActive" @click="openCreateCheckInModal(course)"
                  class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700 transition-colors">
                  发起签到
                </button>
                <button v-else @click="viewCheckInDetails(course.id)"
                  class="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm hover:bg-gray-300 transition-colors">
                  查看签到情况
                </button>
              </div>
            </div>
          </div>

          <div v-else class="bg-white rounded-xl shadow-sm p-6 text-center">
            <p class="text-gray-600">今日没有您的授课</p>
          </div>
        </div>

        <!-- 教师即将到来的课程 -->
        <div class="mb-8">
          <h2 class="text-xl font-semibold text-gray-800 mb-4">即将到来的课程</h2>

          <div class="bg-white rounded-xl shadow-sm overflow-hidden">
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      课程名称
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      地点
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      时间
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      日期
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      学生人数
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="course in teacherCourses.filter(c => !isToday(c.date))" :key="course.id">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {{ course.name }}
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
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {{ course.studentCount }} 人
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 历史签到记录 -->
        <div>
          <h2 class="text-xl font-semibold text-gray-800 mb-4">历史签到统计</h2>

          <div class="bg-white rounded-xl shadow-sm overflow-hidden p-6">
            <p class="text-gray-600 text-center">此功能正在开发中...</p>
          </div>
        </div>
      </div>

      <!-- 学生界面 -->
      <div v-else>
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

                  <div v-if="course.isActive" class="mt-4 flex items-center">
                    <span
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      签到码有效时间: {{ getTimeLeft(course.expiresAt) }}
                    </span>
                  </div>
                </div>

                <button v-if="course.isActive" @click="openCheckInDialog(course)"
                  class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700 transition-colors">
                  立即签到
                </button>
                <span v-else class="px-3 py-1 bg-gray-200 text-gray-600 rounded text-sm">
                  暂未开始签到
                </span>
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
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      课程名称
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      教师
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      地点
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      时间
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
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
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      课程名称
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      签到时间
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      地点
                    </th>
                    <th scope="col"
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
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
    </div>

    <!-- 学生签到对话框 -->
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
            placeholder="请输入6位数字签到码" maxlength="6" pattern="[0-9]*" inputmode="numeric" :disabled="isSubmitting" />
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
        <div v-if="checkInResult.show" :class="[
          'mt-4 p-3 rounded-lg text-center',
          checkInResult.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        ]">
          {{ checkInResult.message }}
        </div>
      </div>
    </div>

    <!-- 教师创建签到模态框 -->
    <div v-if="showCreateCheckInModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4">
        <div class="text-center mb-4">
          <h3 class="text-xl font-bold text-gray-800">
            创建课堂签到
          </h3>
          <p class="text-gray-600 mt-1">{{ newCheckInData.courseName }}</p>
        </div>

        <div class="space-y-4">
          <!-- 签到码 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">签到码</label>
            <div class="flex items-center">
              <input v-if="newCheckInData.customCode" type="text" v-model="newCheckInData.checkInCode"
                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-lg tracking-wider"
                placeholder="请输入自定义签到码" maxlength="6" />
              <input v-else type="text" v-model="newCheckInData.checkInCode"
                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-lg tracking-wider bg-gray-50"
                readonly />

              <button @click="toggleCustomCode"
                class="ml-2 px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm">
                {{ newCheckInData.customCode ? '随机生成' : '自定义' }}
              </button>
            </div>
          </div>

          <!-- 有效时长 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">有效时长(分钟)</label>
            <input type="number" v-model.number="newCheckInData.validMinutes"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              min="1" max="60" />
          </div>

          <!-- 签到说明 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">签到说明(可选)</label>
            <textarea v-model="newCheckInData.description"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
              rows="3" placeholder="例如：请在教室第一排签到"></textarea>
          </div>
        </div>

        <div class="flex space-x-3 mt-6">
          <button @click="showCreateCheckInModal = false"
            class="w-1/2 py-2 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-100 transition-colors"
            :disabled="isSubmitting">
            取消
          </button>
          <button @click="createCheckIn"
            class="w-1/2 bg-primary-600 text-white py-2 rounded-lg font-medium hover:bg-primary-700 transition-colors"
            :disabled="isSubmitting || (newCheckInData.customCode && !newCheckInData.checkInCode)">
            {{ isSubmitting ? '创建中...' : '创建签到' }}
          </button>
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