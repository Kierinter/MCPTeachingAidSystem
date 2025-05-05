<script setup>
import { ref, onMounted, computed ,onUnmounted} from 'vue';
import { getAuthHeaders } from '../utils/auth';

// 数据状态
const subjects = ref([]);
const topics = ref([]);
const problems = ref([]);
const selectedSubject = ref(null);
const selectedTopic = ref(null);
const selectedDifficulty = ref(null);
const currentProblem = ref(null);
const userAnswer = ref('');
const timeSpent = ref(0);
const loading = ref(false);
const submitLoading = ref(false);
const showAnswer = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

// 推荐相关
const studentProfile = ref(null);
const recommendReason = ref('');

// 计时器
const timer = ref(null);

// 难度选项
const difficultyOptions = [
  { value: '简单', label: '简单' },
  { value: '中等', label: '中等' },
  { value: '较难', label: '较难' },
  { value: '困难', label: '困难' }
];

// 计算属性
const filteredTopics = computed(() => {
  if (!selectedSubject.value) return topics.value;
  return topics.value.filter(topic => topic.subject === selectedSubject.value);
});

// 获取学科列表
const fetchSubjects = async () => {
  try {
    const response = await fetch('http://localhost:8080/api/problems/subjects/', {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) throw new Error('获取学科失败');
    const data = await response.json();
    subjects.value = data;
  } catch (error) {
    console.error('获取学科列表错误:', error);
    errorMessage.value = '获取学科列表失败，请刷新重试';
  }
};

// 获取知识点列表
const fetchTopics = async () => {
  try {
    const response = await fetch('http://localhost:8080/api/problems/topics/', {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) throw new Error('获取知识点失败');
    const data = await response.json();
    topics.value = data;
  } catch (error) {
    console.error('获取知识点列表错误:', error);
    errorMessage.value = '获取知识点列表失败，请刷新重试';
  }
};

// 根据条件获取题目列表
const fetchProblems = async () => {
  loading.value = true;
  errorMessage.value = '';
  problems.value = [];
  
  try {
    // 构建查询参数
    const params = new URLSearchParams();
    if (selectedSubject.value) params.append('subject', selectedSubject.value);
    if (selectedTopic.value) params.append('topic', selectedTopic.value);
    if (selectedDifficulty.value) params.append('difficulty', selectedDifficulty.value);
    
    const response = await fetch(`http://localhost:8080/api/problems/problems/?${params.toString()}`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) throw new Error('获取题目失败');
    const data = await response.json();
    problems.value = data;
    
    if (data.length === 0) {
      errorMessage.value = '没有找到匹配的题目';
    }
  } catch (error) {
    console.error('获取题目列表错误:', error);
    errorMessage.value = '获取题目列表失败，请刷新重试';
  } finally {
    loading.value = false;
  }
};

// 获取题目详情
const fetchProblemDetail = async (problemId) => {
  loading.value = true;
  currentProblem.value = null;
  userAnswer.value = '';
  showAnswer.value = false;
  
  try {
    const response = await fetch(`http://localhost:8080/api/problems/problems/${problemId}/`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) throw new Error('获取题目详情失败');
    const data = await response.json();
    currentProblem.value = data;
    
    // 启动计时器
    startTimer();
    
  } catch (error) {
    console.error('获取题目详情错误:', error);
    errorMessage.value = '获取题目详情失败，请重试';
  } finally {
    loading.value = false;
  }
};

// 提交答案
const submitAnswer = async () => {
  // 停止计时
  stopTimer();
  
  submitLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  
  try {
    const response = await fetch('http://localhost:8080/api/problems/records/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        problem: currentProblem.value.id,
        user_answer: userAnswer.value,
        time_spent: timeSpent.value
      })
    });
    
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || '提交答案失败');
    }
    
    // 提交成功
    successMessage.value = '答案已提交';
    showAnswer.value = true;
    
  } catch (error) {
    console.error('提交答案错误:', error);
    errorMessage.value = error.message || '提交答案失败，请重试';
  } finally {
    submitLoading.value = false;
  }
};

// 格式化时间
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
};

// 开始计时
const startTimer = () => {
  // 重置计时器
  timeSpent.value = 0;
  clearInterval(timer.value);
  
  // 启动新计时器
  timer.value = setInterval(() => {
    timeSpent.value += 1;
  }, 1000);
};

// 停止计时
const stopTimer = () => {
  clearInterval(timer.value);
};

// 下一题
const nextProblem = () => {
  if (!problems.value.length) return;
  
  const currentIndex = problems.value.findIndex(p => p.id === currentProblem.value.id);
  const nextIndex = (currentIndex + 1) % problems.value.length;
  fetchProblemDetail(problems.value[nextIndex].id);
};

// 上一题
const prevProblem = () => {
  if (!problems.value.length) return;
  
  const currentIndex = problems.value.findIndex(p => p.id === currentProblem.value.id);
  const prevIndex = (currentIndex - 1 + problems.value.length) % problems.value.length;
  fetchProblemDetail(problems.value[prevIndex].id);
};

// 获取当前学生档案
const fetchStudentProfile = async () => {
  try {
    const res = await fetch('http://localhost:8080/api/students/profiles/me/', {
      headers: getAuthHeaders()
    });
    if (!res.ok) return;
    const data = await res.json();
    studentProfile.value = data;
    // 推荐逻辑
    let reason = '';
    if (data.weak_subjects_list && data.weak_subjects_list.length > 0) {
      selectedSubject.value = null; // 先不限定学科
      selectedTopic.value = null;
      reason += `优先推荐薄弱学科：${data.weak_subjects_list.join('、')}`;
    }
    if (data.academic_level) {
      selectedDifficulty.value = academicLevelToDifficulty(data.academic_level);
      reason += (reason ? '，' : '') + `适合你的学业水平：${academicLevelLabel(data.academic_level)}`;
    }
    recommendReason.value = reason;
  } catch (e) {
    // 忽略
  }
};

function academicLevelToDifficulty(level) {
  switch(level) {
    case 'excellent': return '困难';
    case 'good': return '较难';
    case 'average': return '中等';
    case 'below_average': return '简单';
    case 'poor': return '简单';
    default: return null;
  }
}
function academicLevelLabel(level) {
  switch(level) {
    case 'excellent': return '优秀';
    case 'good': return '良好';
    case 'average': return '中等';
    case 'below_average': return '中下';
    case 'poor': return '薄弱';
    default: return level;
  }
}

// 页面初始化
onMounted(async () => {
  await fetchStudentProfile();
  await fetchSubjects();
  await fetchTopics();
  // 自动推荐题目
  await fetchRecommendedProblems();
});

// 获取推荐题目
const fetchRecommendedProblems = async () => {
  loading.value = true;
  errorMessage.value = '';
  problems.value = [];
  try {
    const response = await fetch('http://localhost:8080/api/problems/problems/recommend/', {
      headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('获取推荐题目失败');
    const data = await response.json();
    problems.value = data;
    if (data.length === 0) {
      errorMessage.value = '没有推荐题目';
    }
  } catch (error) {
    console.error('获取推荐题目错误:', error);
    errorMessage.value = '获取推荐题目失败，请刷新重试';
  } finally {
    loading.value = false;
  }
};

// 组件销毁时清理计时器
onUnmounted(() => {
  clearInterval(timer.value);
});
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <header class="bg-primary-800 text-white px-6 py-4 shadow-md">
      <div class="container mx-auto flex justify-between items-center">
        <h1 class="text-2xl font-bold">题库练习</h1>
        <router-link to="/index" class="text-white hover:text-primary-200 transition-colors">
          返回主页
        </router-link>
      </div>
    </header>

    <div class="container mx-auto px-6 py-8 flex-grow">
      <!-- 筛选区域 -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label class="block text-gray-700 text-sm font-medium mb-2">学科</label>
            <select 
              v-model="selectedSubject" 
              class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option :value="null">所有学科</option>
              <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
                {{ subject.name }}
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-gray-700 text-sm font-medium mb-2">知识点</label>
            <select 
              v-model="selectedTopic" 
              class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option :value="null">所有知识点</option>
              <option v-for="topic in filteredTopics" :key="topic.id" :value="topic.id">
                {{ topic.name }}
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-gray-700 text-sm font-medium mb-2">难度</label>
            <select 
              v-model="selectedDifficulty" 
              class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option :value="null">所有难度</option>
              <option v-for="option in difficultyOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          
          <div class="flex items-end">
            <button 
              @click="fetchProblems" 
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors w-full"
              :disabled="loading"
            >
              {{ loading ? '加载中...' : '搜索题目' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 错误消息 -->
      <div v-if="errorMessage" class="bg-red-100 text-red-800 p-3 rounded-lg mb-4">
        {{ errorMessage }}
      </div>
      
      <!-- 成功消息 -->
      <div v-if="successMessage" class="bg-green-100 text-green-800 p-3 rounded-lg mb-4">
        {{ successMessage }}
      </div>

      <!-- 题库列表 -->
      <div v-if="problems.length && !currentProblem" class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">推荐练习 ({{ problems.length }} 题)</h2>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  标题
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  知识点
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  难度
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="problem in problems" :key="problem.id">
                <td class="px-6 py-4 whitespace-nowrap max-w-[300px]">
                  <div class="truncate" :title="problem.title">{{ problem.title }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ problem.topic_name }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span 
                    class="px-2 py-1 rounded text-xs font-medium"
                    :class="{
                      'bg-green-100 text-green-800': problem.difficulty === '简单',
                      'bg-yellow-100 text-yellow-800': problem.difficulty === '中等',
                      'bg-orange-100 text-orange-800': problem.difficulty === '较难',
                      'bg-red-100 text-red-800': problem.difficulty === '困难'
                    }"
                  >{{ problem.difficulty }}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <button 
                    @click="fetchProblemDetail(problem.id)" 
                    class="text-primary-600 hover:text-primary-800"
                  >
                    开始做题
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 题目详情 -->
      <div v-if="currentProblem" class="bg-white rounded-lg shadow-md p-6">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-semibold text-gray-800">
            {{ currentProblem.topic_name }} · {{ currentProblem.difficulty }}
          </h2>
          <div class="flex space-x-4 items-center">
            <span class="text-gray-600">计时: {{ formatTime(timeSpent) }}</span>
            <button 
              @click="() => { currentProblem = null; stopTimer(); }" 
              class="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
            >
              返回列表
            </button>
          </div>
        </div>
        
        <div class="mb-8">
          <h3 class="font-medium text-lg mb-2">题目内容:</h3>
          <div class="bg-gray-50 p-4 rounded-md">
            {{ currentProblem.content }}
          </div>
        </div>
        
        <div class="mb-8">
          <h3 class="font-medium text-lg mb-2">你的答案:</h3>
          <textarea 
            v-model="userAnswer"
            rows="4"
            class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            :disabled="showAnswer"
            placeholder="请在此输入你的答案..."
          ></textarea>
        </div>
        
        <div v-if="!showAnswer" class="flex justify-between">
          <div class="flex space-x-3">
            <button 
              @click="prevProblem"
              class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              :disabled="submitLoading"
            >
              上一题
            </button>
            <button 
              @click="nextProblem"
              class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              :disabled="submitLoading"
            >
              下一题
            </button>
          </div>
          <button 
            @click="submitAnswer"
            class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
            :disabled="submitLoading"
          >
            {{ submitLoading ? '提交中...' : '提交答案' }}
          </button>
        </div>
        
        <div v-if="showAnswer" class="space-y-6">
          <div>
            <h3 class="font-medium text-lg mb-2 text-green-600">参考答案:</h3>
            <div class="bg-green-50 p-4 rounded-md">
              {{ currentProblem.answer }}
            </div>
          </div>
          
          <div>
            <h3 class="font-medium text-lg mb-2 text-blue-600">解析:</h3>
            <div class="bg-blue-50 p-4 rounded-md whitespace-pre-wrap">
              {{ currentProblem.explanation }}
            </div>
          </div>
          
          <div class="flex justify-between pt-4">
            <div class="flex space-x-3">
              <button 
                @click="prevProblem"
                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                上一题
              </button>
              <button 
                @click="nextProblem"
                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                下一题
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!problems.length && !loading && !currentProblem" class="bg-white rounded-lg shadow-md p-6 text-center">
        <p class="text-gray-600">选择条件进行搜索，开始做题吧！</p>
      </div>
    </div>
  </div>
</template>