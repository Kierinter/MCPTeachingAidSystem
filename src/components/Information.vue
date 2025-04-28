<script setup>
import { ref } from 'vue';

const userInfo = ref({
  name: '张三',
  email: 'zhangsan@example.com',
  avatar: 'https://randomuser.me/api/portraits/men/44.jpg',
  school: '示例大学',
  major: '计算机科学',
  joinDate: '2023-09-01'
});

const learningData = ref({
  totalHours: 120,
  completedCourses: 8,
  averageScore: 85,
  problemSolved: 432
});

const recentActivity = ref([
  { type: '完成课程', name: '高等数学', date: '2025-04-25', score: '92分' },
  { type: '练习题目', name: '线性代数习题集', date: '2025-04-23', count: '15题' },
  { type: '观看视频', name: '数据结构基础', date: '2025-04-20', duration: '45分钟' }
]);
</script>

<template>
  <div class="min-h-screen bg-gray-100 py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- 用户信息卡片 -->
        <div class="bg-white rounded-xl shadow-sm p-6">
          <div class="flex flex-col items-center text-center">
            <img :src="userInfo.avatar" alt="用户头像" class="w-32 h-32 rounded-full object-cover border-4 border-primary-100 mb-4" />
            <h2 class="text-2xl font-bold text-gray-800">{{ userInfo.name }}</h2>
            <p class="text-gray-600 mb-4">{{ userInfo.email }}</p>
            
            <div class="w-full border-t border-gray-200 my-4 pt-4">
              <div class="flex justify-between mb-2">
                <span class="text-gray-600">学校:</span>
                <span class="font-medium">{{ userInfo.school }}</span>
              </div>
              <div class="flex justify-between mb-2">
                <span class="text-gray-600">专业:</span>
                <span class="font-medium">{{ userInfo.major }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">加入日期:</span>
                <span class="font-medium">{{ userInfo.joinDate }}</span>
              </div>
            </div>
            
            <button class="mt-4 w-full bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700 transition-colors">
              编辑资料
            </button>
          </div>
        </div>
        
        <!-- 学习数据 -->
        <div class="bg-white rounded-xl shadow-sm p-6 md:col-span-2">
          <h3 class="text-xl font-bold text-gray-800 mb-4">学习统计</h3>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-primary-50 rounded-lg p-4 text-center">
              <p class="text-2xl font-bold text-primary-700">{{ learningData.totalHours }}</p>
              <p class="text-sm text-gray-600">学习小时</p>
            </div>
            
            <div class="bg-green-50 rounded-lg p-4 text-center">
              <p class="text-2xl font-bold text-green-700">{{ learningData.completedCourses }}</p>
              <p class="text-sm text-gray-600">完成课程</p>
            </div>
            
            <div class="bg-yellow-50 rounded-lg p-4 text-center">
              <p class="text-2xl font-bold text-yellow-700">{{ learningData.averageScore }}</p>
              <p class="text-sm text-gray-600">平均分数</p>
            </div>
            
            <div class="bg-purple-50 rounded-lg p-4 text-center">
              <p class="text-2xl font-bold text-purple-700">{{ learningData.problemSolved }}</p>
              <p class="text-sm text-gray-600">解决问题数</p>
            </div>
          </div>
          
          <h3 class="text-xl font-bold text-gray-800 mt-8 mb-4">最近活动</h3>
          
          <div class="space-y-4">
            <div v-for="(activity, index) in recentActivity" :key="index" 
                class="bg-gray-50 rounded-lg p-4 flex justify-between items-center">
              <div>
                <p class="font-medium text-gray-800">{{ activity.type }}: {{ activity.name }}</p>
                <p class="text-sm text-gray-600">{{ activity.date }}</p>
              </div>
              <div>
                <span v-if="activity.score" class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                  {{ activity.score }}
                </span>
                <span v-else-if="activity.count" class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                  {{ activity.count }}
                </span>
                <span v-else-if="activity.duration" class="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
                  {{ activity.duration }}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 学习建议 -->
        <div class="bg-white rounded-xl shadow-sm p-6 md:col-span-3">
          <h3 class="text-xl font-bold text-gray-800 mb-4">AI 学习建议</h3>
          
          <div class="bg-gray-50 rounded-lg p-5 border-l-4 border-primary-500">
            <p class="text-gray-700 leading-relaxed">
              根据您的学习数据分析，建议您在接下来的学习中专注于提高"数据结构与算法"方面的知识。
              您在这方面的练习题正确率稍低，可以尝试观看我们的视频系列并完成相关练习。
              另外，您的高等数学表现优秀，可以考虑尝试更具挑战性的进阶内容。
            </p>
            <div class="mt-4 flex space-x-3">
              <button class="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors text-sm">
                查看推荐课程
              </button>
              <button class="bg-white border border-primary-600 text-primary-600 px-4 py-2 rounded-lg hover:bg-primary-50 transition-colors text-sm">
                查看练习题
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>