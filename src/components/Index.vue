<script setup>
import { useRouter } from 'vue-router';
import { ref, onMounted } from 'vue';

const router = useRouter();
const userRole = ref('student'); // 默认为学生身份，可以是'student'或'teacher'
const userName = ref('张三'); // 用户名，实际应用中应从登录状态获取
const isCheckedIn = ref(false); // 签到状态
const isAuthenticated = ref(true); // 是否已登录，实际应用中应从状态管理获取

// 学生专属数据
const studentData = {
  todayAssignments: [
    { id: 1, title: '高等数学作业', deadline: '今天 23:59', subject: '数学' },
    { id: 2, title: '物理实验报告', deadline: '明天 18:00', subject: '物理' }
  ],
  recentTopics: [
    { id: 1, name: '微积分基础', progress: 75 },
    { id: 2, name: '线性代数', progress: 45 },
    { id: 3, name: '概率论', progress: 30 }
  ]
};

// 教师专属数据
const teacherData = {
  classesList: [
    { id: 1, name: '高等数学A班', students: 45 },
    { id: 2, name: '微积分B班', students: 38 },
    { id: 3, name: '线性代数C班', students: 42 }
  ],
  pendingTasks: [
    { id: 1, title: '批改期中考试', count: 83, deadline: '3天后' },
    { id: 2, title: '审核学生作业', count: 24, deadline: '今天' }
  ]
};

const goToDialogue = () => {
  router.push('/dialogue');
};

const goToLogin = () => {
  router.push('/login');
};

const goToCheckIn = () => {
  router.push('/checkin');
};

const goToPracticeProblem = () => {
  router.push('/practiceproblem');
};

const handleCheckIn = () => {
  // 实际应用中这里应该调用API进行签到
  isCheckedIn.value = true;
  alert('签到成功！');
};

const switchRole = () => {
  // 仅用于演示，切换身份
  userRole.value = userRole.value === 'student' ? 'teacher' : 'student';
};

const logout = () => {
  // 实际应用中应该清除登录状态
  router.push('/login');
};

onMounted(() => {
  // 在实际应用中，这里应该检查用户是否已签到
  // 例如从后端API获取当天的签到状态
});
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <header class="bg-primary-800 text-white px-6 py-4 shadow-md">
      <div class="container mx-auto flex justify-between items-center">
        <h1 class="text-2xl font-bold">AI 教辅系统</h1>
        <nav class="flex items-center space-x-6">
          <div v-if="isAuthenticated" class="flex items-center">
            <span class="mr-4">欢迎，{{ userName }} ({{ userRole === 'student' ? '学生' : '教师' }})</span>
            <a href="#" @click.prevent="logout" class="hover:text-primary-200 transition-colors">退出</a>
          </div>
          <div v-else>
            <a href="#" @click.prevent="goToLogin" class="hover:text-primary-200 transition-colors">登录</a>
          </div>
        </nav>
      </div>
    </header>

    <div class="container mx-auto px-6 py-8 flex-grow">
      <!-- 签到卡片 -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-semibold text-gray-800">每日签到</h2>
          <div class="flex space-x-4">
            <button 
              @click="handleCheckIn" 
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
              :disabled="isCheckedIn"
            >
              {{ isCheckedIn ? '已签到' : '立即签到' }}
            </button>
            <button 
              @click="goToCheckIn" 
              class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              签到记录
            </button>
          </div>
        </div>
      </div>

      <!-- 学生视图 -->
      <div v-if="userRole === 'student'" class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- 快捷功能 -->
        <div class="col-span-3 bg-white rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-800 mb-4">快捷功能</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div @click="goToDialogue" class="bg-blue-50 p-4 rounded-lg text-center cursor-pointer hover:bg-blue-100 transition-colors">
              <div class="text-blue-600 text-lg font-medium">AI对话</div>
              <div class="text-sm text-gray-600">向AI提问解题</div>
            </div>
            <div @click="goToPracticeProblem" class="bg-green-50 p-4 rounded-lg text-center cursor-pointer hover:bg-green-100 transition-colors">
              <div class="text-green-600 text-lg font-medium">题库练习</div>
              <div class="text-sm text-gray-600">自主选题练习</div>
            </div>
            <div class="bg-purple-50 p-4 rounded-lg text-center cursor-pointer hover:bg-purple-100 transition-colors">
              <div class="text-purple-600 text-lg font-medium">错题本</div>
              <div class="text-sm text-gray-600">查看错题记录</div>
            </div>
            <div class="bg-orange-50 p-4 rounded-lg text-center cursor-pointer hover:bg-orange-100 transition-colors">
              <div class="text-orange-600 text-lg font-medium">学习报告</div>
              <div class="text-sm text-gray-600">查看学习情况</div>
            </div>
          </div>
        </div>

        <!-- 今日作业 -->
        <div class="col-span-3 md:col-span-2 bg-white rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-800 mb-4">今日作业</h2>
          <div v-if="studentData.todayAssignments.length > 0" class="space-y-4">
            <div v-for="assignment in studentData.todayAssignments" :key="assignment.id" class="border-l-4 border-primary-500 pl-4 py-2">
              <div class="flex justify-between items-center">
                <div>
                  <h3 class="font-medium">{{ assignment.title }}</h3>
                  <div class="text-sm text-gray-500">{{ assignment.subject }} · 截止: {{ assignment.deadline }}</div>
                </div>
                <button class="px-3 py-1 bg-primary-100 text-primary-700 rounded hover:bg-primary-200 transition-colors text-sm">
                  查看
                </button>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-gray-500">
            暂无待完成作业
          </div>
        </div>

        <!-- 学习进度 -->
        <div class="col-span-3 md:col-span-1 bg-white rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-800 mb-4">学习进度</h2>
          <div class="space-y-4">
            <div v-for="topic in studentData.recentTopics" :key="topic.id" class="space-y-1">
              <div class="flex justify-between text-sm">
                <span>{{ topic.name }}</span>
                <span>{{ topic.progress }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2.5">
                <div class="bg-primary-600 h-2.5 rounded-full" :style="`width: ${topic.progress}%`"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 教师视图 -->
      <div v-else-if="userRole === 'teacher'" class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- 快捷功能 -->
        <div class="col-span-3 bg-white rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-800 mb-4">教学工具</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-blue-50 p-4 rounded-lg text-center cursor-pointer hover:bg-blue-100 transition-colors">
              <div class="text-blue-600 text-lg font-medium">布置作业</div>
              <div class="text-sm text-gray-600">创建新的作业</div>
            </div>
            <div class="bg-green-50 p-4 rounded-lg text-center cursor-pointer hover:bg-green-100 transition-colors">
              <div class="text-green-600 text-lg font-medium">班级管理</div>
              <div class="text-sm text-gray-600">管理班级和学生</div>
            </div>
            <div class="bg-purple-50 p-4 rounded-lg text-center cursor-pointer hover:bg-purple-100 transition-colors">
              <div class="text-purple-600 text-lg font-medium">题库管理</div>
              <div class="text-sm text-gray-600">管理题目资源</div>
            </div>
            <div class="bg-orange-50 p-4 rounded-lg text-center cursor-pointer hover:bg-orange-100 transition-colors">
              <div class="text-orange-600 text-lg font-medium">统计分析</div>
              <div class="text-sm text-gray-600">班级学习情况</div>
            </div>
          </div>
        </div>

        <!-- 班级列表 -->
        <div class="col-span-3 md:col-span-2 bg-white rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-800 mb-4">我的班级</h2>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">班级名称</th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">学生人数</th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="cls in teacherData.classesList" :key="cls.id">
                  <td class="px-6 py-4 whitespace-nowrap">{{ cls.name }}</td>
                  <td class="px-6 py-4 whitespace-nowrap">{{ cls.students }} 人</td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <button class="text-primary-600 hover:text-primary-800">查看</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 待办任务 -->
        <div class="col-span-3 md:col-span-1 bg-white rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-800 mb-4">待办任务</h2>
          <div class="space-y-4">
            <div v-for="task in teacherData.pendingTasks" :key="task.id" class="border-l-4 border-yellow-500 pl-4 py-2">
              <h3 class="font-medium">{{ task.title }}</h3>
              <div class="text-sm text-gray-500">{{ task.count }} 项 · {{ task.deadline }}</div>
              <button class="mt-2 px-3 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition-colors text-sm">
                处理
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 调试按钮，仅用于演示 -->
      <div class="mt-6 text-center">
        <button @click="switchRole" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors">
          切换身份 (当前: {{ userRole === 'student' ? '学生' : '教师' }})
        </button>
      </div>
    </div>

    <footer class="bg-gray-800 text-white p-4 text-center">
      <div class="container mx-auto">
        <p>© 2023 AI教辅系统 版权所有</p>
      </div>
    </footer>
  </div>
</template>
