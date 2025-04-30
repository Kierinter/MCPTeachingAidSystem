<script setup>
import { ref, onMounted, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// 页面状态
const loading = ref(false);
const activeTab = ref('recommended');
const selectedTopic = ref(null);
const userStats = ref(null);
const currentProblem = ref(null);
const showExplanation = ref(false);
const userAnswer = ref('');
const startTime = ref(null);
const submitResult = ref(null);
const problems = reactive({
  recommended: [],
  byTopic: [],
  history: []
});

// 知识点列表
const topics = ref([]);

// 获取用户统计数据
const fetchUserStats = async () => {
  loading.value = true;
  try {
    // 从localStorage获取用户信息
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const userId = user.id || 1; // 默认用户ID为1
    
    const response = await fetch(`http://localhost:5000/api/problems/user-stats/${userId}`, {
      headers: {
        'Authorization': `Token ${localStorage.getItem('authToken') || ''}`
      }
    });
    
    if (response.ok) {
      userStats.value = await response.json();
    }
  } catch (error) {
    console.error('获取用户统计数据失败:', error);
  } finally {
    loading.value = false;
  }
};

// 获取推荐题目
const fetchRecommendedProblems = async () => {
  loading.value = true;
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const userId = user.id || 1;
    
    const response = await fetch(`http://localhost:5000/api/problems/recommend/${userId}?count=10`, {
      headers: {
        'Authorization': `Token ${localStorage.getItem('authToken') || ''}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      problems.recommended = data.problems;
    }
  } catch (error) {
    console.error('获取推荐题目失败:', error);
  } finally {
    loading.value = false;
  }
};

// 获取知识点列表
const fetchTopics = async () => {
  try {
    const response = await fetch(`http://localhost:5000/api/problems/topics`, {
      headers: {
        'Authorization': `Token ${localStorage.getItem('authToken') || ''}`
      }
    });
    
    if (response.ok) {
      topics.value = await response.json();
    }
  } catch (error) {
    console.error('获取知识点列表失败:', error);
  }
};

// 按知识点获取题目
const fetchProblemsByTopic = async (topicId) => {
  loading.value = true;
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const userId = user.id || 1;
    
    const response = await fetch(`http://localhost:5000/api/problems/by-topic/${topicId}?user_id=${userId}`, {
      headers: {
        'Authorization': `Token ${localStorage.getItem('authToken') || ''}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      problems.byTopic = data.problems;
    }
  } catch (error) {
    console.error('获取知识点题目失败:', error);
  } finally {
    loading.value = false;
  }
};

// 获取历史作答记录
const fetchUserHistory = async () => {
  loading.value = true;
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const userId = user.id || 1;
    
    const response = await fetch(`http://localhost:5000/api/problems/history/${userId}`, {
      headers: {
        'Authorization': `Token ${localStorage.getItem('authToken') || ''}`
      }
    });
    
    if (response.ok) {
      problems.history = await response.json();
    }
  } catch (error) {
    console.error('获取历史记录失败:', error);
  } finally {
    loading.value = false;
  }
};

// 选择题目进行练习
const selectProblem = (problem) => {
  currentProblem.value = problem;
  userAnswer.value = '';
  showExplanation.value = false;
  submitResult.value = null;
  startTime.value = Date.now();
};

// 提交答案
const submitAnswer = async () => {
  if (!userAnswer.value.trim()) {
    alert('请输入你的答案');
    return;
  }
  
  const timeSpent = Math.floor((Date.now() - startTime.value) / 1000);
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const userId = user.id || 1;
  
  try {
    const response = await fetch(`http://localhost:5000/api/problems/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${localStorage.getItem('authToken') || ''}`
      },
      body: JSON.stringify({
        user_id: userId,
        problem_id: currentProblem.value.id,
        user_answer: userAnswer.value,
        time_spent: timeSpent
      })
    });
    
    if (response.ok) {
      submitResult.value = await response.json();
      showExplanation.value = true;
      
      // 刷新数据
      if (activeTab.value === 'history') {
        fetchUserHistory();
      }
    }
  } catch (error) {
    console.error('提交答案失败:', error);
  }
};

// 返回题目列表
const backToList = () => {
  currentProblem.value = null;
  userAnswer.value = '';
  showExplanation.value = false;
  submitResult.value = null;
};

// 切换标签页
const changeTab = (tab) => {
  activeTab.value = tab;
  if (tab === 'recommended' && problems.recommended.length === 0) {
    fetchRecommendedProblems();
  } else if (tab === 'byTopic' && topics.value.length === 0) {
    fetchTopics();
  } else if (tab === 'history' && problems.history.length === 0) {
    fetchUserHistory();
  }
};

// 根据知识点筛选题目
const selectTopic = (topic) => {
  selectedTopic.value = topic;
  fetchProblemsByTopic(topic.id);
};

// 计算用户掌握程度
const masteryLevel = computed(() => {
  if (!userStats.value || !userStats.value.overall_stats) return 'N/A';
  
  const stats = userStats.value.overall_stats;
  const correctRate = stats.correct_problems / stats.total_problems;
  
  if (correctRate >= 0.9) return '精通';
  if (correctRate >= 0.7) return '熟练';
  if (correctRate >= 0.5) return '基础';
  return '入门';
});

onMounted(() => {
  fetchUserStats();
  fetchRecommendedProblems();
});
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <div class="max-w-7xl mx-auto px-4 py-8">
      <div class="flex justify-between items-center mb-8">
        <h1 class="text-2xl font-bold text-gray-800">练习题库</h1>
        <div>
          <button 
            @click="router.push('/dialogue')" 
            class="text-primary-600 hover:text-primary-800 font-medium"
          >
            返回对话
          </button>
        </div>
      </div>
      
      <!-- 用户统计信息 -->
      <div v-if="userStats" class="bg-white rounded-xl shadow-sm p-6 mb-8">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <h3 class="text-sm font-medium text-gray-500">总作答题目</h3>
            <p class="text-2xl font-bold text-gray-800">{{ userStats.overall_stats?.total_problems || 0 }}</p>
          </div>
          <div>
            <h3 class="text-sm font-medium text-gray-500">正确题目</h3>
            <p class="text-2xl font-bold text-green-600">{{ userStats.overall_stats?.correct_problems || 0 }}</p>
          </div>
          <div>
            <h3 class="text-sm font-medium text-gray-500">平均分数</h3>
            <p class="text-2xl font-bold text-primary-600">{{ userStats.overall_stats?.average_score?.toFixed(1) || 0 }}</p>
          </div>
          <div>
            <h3 class="text-sm font-medium text-gray-500">掌握程度</h3>
            <p class="text-2xl font-bold text-purple-600">{{ masteryLevel }}</p>
          </div>
        </div>
      </div>
      
      <!-- 题目详情页 -->
      <div v-if="currentProblem" class="bg-white rounded-xl shadow-sm overflow-hidden">
        <div class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold text-gray-800">
              {{ currentProblem.topic_name }} - {{ currentProblem.difficulty }}
            </h2>
            <button @click="backToList" class="text-gray-600 hover:text-gray-800">
              返回列表
            </button>
          </div>
          
          <div class="prose max-w-none mb-6">
            <p class="text-lg">{{ currentProblem.content }}</p>
          </div>
          
          <div class="mb-6">
            <label class="block text-gray-700 font-medium mb-2">你的答案:</label>
            <textarea 
              v-model="userAnswer" 
              :disabled="showExplanation"
              rows="4" 
              class="w-full px-4 py-2 border rounded-lg focus:ring-primary-500 focus:border-primary-500"
              placeholder="输入你的答案..."
            ></textarea>
          </div>
          
          <div v-if="!showExplanation" class="flex justify-end">
            <button 
              @click="submitAnswer" 
              class="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors"
            >
              提交答案
            </button>
          </div>
          
          <!-- 提交结果和解析 -->
          <div v-if="showExplanation" class="mt-8 space-y-6">
            <div :class="[
              'p-4 rounded-lg',
              submitResult.is_correct ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            ]">
              <div class="flex items-center">
                <div :class="[
                  'w-8 h-8 rounded-full flex items-center justify-center mr-3',
                  submitResult.is_correct ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                ]">
                  <span v-if="submitResult.is_correct">✓</span>
                  <span v-else>✗</span>
                </div>
                <div>
                  <p :class="[
                    'font-medium',
                    submitResult.is_correct ? 'text-green-800' : 'text-red-800'
                  ]">
                    {{ submitResult.is_correct ? '回答正确' : '回答错误' }}
                  </p>
                  <p class="text-sm text-gray-600">得分: {{ submitResult.score }}</p>
                </div>
              </div>
            </div>
            
            <div>
              <h3 class="font-medium text-gray-800 mb-2">标准答案:</h3>
              <div class="p-4 bg-gray-50 rounded-lg">
                <p>{{ submitResult.correct_answer }}</p>
              </div>
            </div>
            
            <div>
              <h3 class="font-medium text-gray-800 mb-2">解析:</h3>
              <div class="p-4 bg-gray-50 rounded-lg prose max-w-none">
                <p>{{ submitResult.explanation }}</p>
              </div>
            </div>
            
            <div class="flex justify-between">
              <button 
                @click="backToList" 
                class="text-gray-600 hover:text-gray-800 font-medium"
              >
                返回题目列表
              </button>
              <button 
                @click="fetchRecommendedProblems(); backToList();" 
                class="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors"
              >
                继续练习
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 题目列表 -->
      <div v-else>
        <!-- 标签页导航 -->
        <div class="bg-white rounded-t-xl shadow-sm border-b">
          <div class="flex">
            <button 
              @click="changeTab('recommended')" 
              class="px-6 py-3 text-center focus:outline-none"
              :class="{'text-primary-600 border-b-2 border-primary-600 font-medium': activeTab === 'recommended'}"
            >
              推荐题目
            </button>
            <button 
              @click="changeTab('byTopic')" 
              class="px-6 py-3 text-center focus:outline-none"
              :class="{'text-primary-600 border-b-2 border-primary-600 font-medium': activeTab === 'byTopic'}"
            >
              按知识点
            </button>
            <button 
              @click="changeTab('history')" 
              class="px-6 py-3 text-center focus:outline-none"
              :class="{'text-primary-600 border-b-2 border-primary-600 font-medium': activeTab === 'history'}"
            >
              历史记录
            </button>
          </div>
        </div>
        
        <div class="bg-white rounded-b-xl shadow-sm p-6">
          <!-- 加载状态 -->
          <div v-if="loading" class="py-20 text-center">
            <p class="text-gray-600">加载中...</p>
          </div>
          
          <!-- 推荐题目列表 -->
          <div v-else-if="activeTab === 'recommended'">
            <div v-if="problems.recommended.length === 0" class="py-10 text-center">
              <p class="text-gray-500">暂无推荐题目，请先完成一些练习</p>
            </div>
            <div v-else class="divide-y">
              <div 
                v-for="problem in problems.recommended" 
                :key="problem.id"
                @click="selectProblem(problem)"
                class="py-4 hover:bg-gray-50 cursor-pointer rounded-lg px-3"
              >
                <div class="flex justify-between items-start">
                  <div>
                    <h3 class="font-medium text-gray-800">{{ problem.content.substring(0, 100) + (problem.content.length > 100 ? '...' : '') }}</h3>
                    <p class="text-sm text-gray-500 mt-1">{{ problem.topic_name }}</p>
                  </div>
                  <span 
                    class="px-2 py-1 text-xs rounded-full"
                    :class="{
                      'bg-green-100 text-green-800': problem.difficulty === '简单',
                      'bg-blue-100 text-blue-800': problem.difficulty === '中等',
                      'bg-yellow-100 text-yellow-800': problem.difficulty === '较难',
                      'bg-red-100 text-red-800': problem.difficulty === '困难'
                    }"
                  >
                    {{ problem.difficulty }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 按知识点分类题目 -->
          <div v-else-if="activeTab === 'byTopic'">
            <div v-if="!selectedTopic" class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div 
                v-for="topic in topics" 
                :key="topic.id"
                @click="selectTopic(topic)"
                class="bg-gray-50 p-4 rounded-lg hover:bg-gray-100 cursor-pointer"
              >
                <h3 class="font-medium text-gray-800">{{ topic.name }}</h3>
                <p class="text-sm text-gray-500 mt-1">题目数量: {{ topic.problem_count }}</p>
              </div>
            </div>
            <div v-else>
              <div class="mb-4 flex justify-between items-center">
                <h3 class="font-medium text-gray-800">{{ selectedTopic.name }}</h3>
                <button 
                  @click="selectedTopic = null" 
                  class="text-gray-600 hover:text-gray-800"
                >
                  返回知识点列表
                </button>
              </div>
              
              <div v-if="problems.byTopic.length === 0" class="py-10 text-center">
                <p class="text-gray-500">该知识点下暂无题目</p>
              </div>
              <div v-else class="divide-y">
                <div 
                  v-for="problem in problems.byTopic" 
                  :key="problem.id"
                  @click="selectProblem(problem)"
                  class="py-4 hover:bg-gray-50 cursor-pointer rounded-lg px-3"
                >
                  <div class="flex justify-between items-start">
                    <div>
                      <h3 class="font-medium text-gray-800">{{ problem.content.substring(0, 100) + (problem.content.length > 100 ? '...' : '') }}</h3>
                    </div>
                    <span 
                      class="px-2 py-1 text-xs rounded-full"
                      :class="{
                        'bg-green-100 text-green-800': problem.difficulty === '简单',
                        'bg-blue-100 text-blue-800': problem.difficulty === '中等',
                        'bg-yellow-100 text-yellow-800': problem.difficulty === '较难',
                        'bg-red-100 text-red-800': problem.difficulty === '困难'
                      }"
                    >
                      {{ problem.difficulty }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 历史记录 -->
          <div v-else-if="activeTab === 'history'">
            <div v-if="problems.history.length === 0" class="py-10 text-center">
              <p class="text-gray-500">暂无做题记录</p>
            </div>
            <div v-else>
              <table class="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">题目</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">知识点</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">难度</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">分数</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">日期</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr 
                    v-for="record in problems.history" 
                    :key="record.id"
                    @click="selectProblem(record.problem)"
                    class="hover:bg-gray-50 cursor-pointer"
                  >
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="text-sm text-gray-900">{{ record.problem.content.substring(0, 30) + '...' }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="text-sm text-gray-500">{{ record.problem.topic_name }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span 
                        class="px-2 py-1 text-xs rounded-full"
                        :class="{
                          'bg-green-100 text-green-800': record.problem.difficulty === '简单',
                          'bg-blue-100 text-blue-800': record.problem.difficulty === '中等',
                          'bg-yellow-100 text-yellow-800': record.problem.difficulty === '较难',
                          'bg-red-100 text-red-800': record.problem.difficulty === '困难'
                        }"
                      >
                        {{ record.problem.difficulty }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span 
                        class="px-2 py-1 text-xs rounded-full"
                        :class="{
                          'bg-green-100 text-green-800': record.status === 'correct',
                          'bg-yellow-100 text-yellow-800': record.status === 'partially_correct',
                          'bg-red-100 text-red-800': record.status === 'incorrect'
                        }"
                      >
                        {{ record.status === 'correct' ? '正确' : 
                           record.status === 'partially_correct' ? '部分正确' : '错误' }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="text-sm font-medium" :class="{
                        'text-green-600': record.score >= 80,
                        'text-yellow-600': record.score >= 60 && record.score < 80,
                        'text-red-600': record.score < 60
                      }">
                        {{ record.score }}
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {{ new Date(record.attempted_at).toLocaleString() }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* 确保表格在小屏幕上可以滚动 */
table {
  @apply w-full;
}

@media (max-width: 640px) {
  table {
    @apply block overflow-x-auto;
  }
}
</style>