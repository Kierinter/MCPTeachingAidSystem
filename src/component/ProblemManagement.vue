<script setup>
import { ref, onMounted, computed } from 'vue';
import { getAuthHeaders, getCurrentUser } from '../utils/auth';
import { useRouter } from 'vue-router';

const router = useRouter();
const user = getCurrentUser();

// 检查是否为教师身份
if (!user || user.role !== 'teacher') {
  router.push('/index');
}

// 数据状态
const subjects = ref([]);
const topics = ref([]);
const problems = ref([]);
const loading = ref(false);
const formMode = ref('list'); // 'list', 'add', 'edit'
const errorMessage = ref('');
const successMessage = ref('');
const currentPage = ref(1);
const pageSize = ref(10);
const totalProblems = ref(0);

// 搜索条件
const searchTerm = ref('');
const filterSubject = ref(null);
const filterTopic = ref(null);
const filterDifficulty = ref(null);

// 表单数据
const problemForm = ref({
  topic: null,
  title: '',
  content: '',
  answer: '',
  explanation: '',
  difficulty: '中等'
});

// 当前编辑的题目ID
const currentEditId = ref(null);

// 难度选项
const difficultyOptions = [
  { value: '简单', label: '简单' },
  { value: '中等', label: '中等' },
  { value: '较难', label: '较难' },
  { value: '困难', label: '困难' }
];

// 计算属性
const filteredTopics = computed(() => {
  if (!filterSubject.value) return topics.value;
  return topics.value.filter(topic => topic.subject === filterSubject.value);
});

const totalPages = computed(() => {
  return Math.ceil(totalProblems.value / pageSize.value);
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

// 获取题目列表
const fetchProblems = async (page = 1) => {
  loading.value = true;
  errorMessage.value = '';
  currentPage.value = page;
  
  try {
    // 构建查询参数
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('page_size', pageSize.value);
    
    if (searchTerm.value) params.append('search', searchTerm.value);
    if (filterSubject.value) params.append('subject', filterSubject.value);
    if (filterTopic.value) params.append('topic', filterTopic.value);
    if (filterDifficulty.value) params.append('difficulty', filterDifficulty.value);
    
    const response = await fetch(`http://localhost:8080/api/problems/problems/?${params.toString()}`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) throw new Error('获取题目失败');
    const data = await response.json();
    
    problems.value = data.results || data;
    totalProblems.value = data.count || problems.value.length;
    
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
  errorMessage.value = '';
  
  try {
    const response = await fetch(`http://localhost:8080/api/problems/problems/${problemId}/`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) throw new Error('获取题目详情失败');
    const data = await response.json();
    
    // 填充表单数据
    problemForm.value = {
      topic: data.topic,
      title: data.title,
      content: data.content,
      answer: data.answer,
      explanation: data.explanation,
      difficulty: data.difficulty
    };
    
    currentEditId.value = data.id;
    formMode.value = 'edit';
    
  } catch (error) {
    console.error('获取题目详情错误:', error);
    errorMessage.value = '获取题目详情失败，请重试';
  } finally {
    loading.value = false;
  }
};

// 添加或更新题目
const saveProblem = async () => {
  // 表单验证
  if (!problemForm.value.topic || !problemForm.value.title || !problemForm.value.content || !problemForm.value.answer) {
    errorMessage.value = '请填写必填字段';
    return;
  }
  
  loading.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  
  try {
    let url = 'http://localhost:8080/api/problems/problems/';
    let method = 'POST';
    
    // 如果是编辑模式
    if (formMode.value === 'edit' && currentEditId.value) {
      url = `${url}${currentEditId.value}/`;
      method = 'PUT';
    }
    
    const response = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(problemForm.value)
    });
    
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || '保存题目失败');
    }
    
    // 保存成功
    successMessage.value = formMode.value === 'add' ? '添加题目成功' : '更新题目成功';
    
    // 重置表单并返回列表
    resetForm();
    formMode.value = 'list';
    fetchProblems(currentPage.value);
    
  } catch (error) {
    console.error('保存题目错误:', error);
    errorMessage.value = error.message || '保存题目失败，请重试';
  } finally {
    loading.value = false;
  }
};

// 删除题目
const deleteProblem = async (problemId) => {
  if (!confirm('确定要删除这个题目吗？此操作不可撤销。')) {
    return;
  }
  
  loading.value = true;
  errorMessage.value = '';
  
  try {
    const response = await fetch(`http://localhost:8080/api/problems/problems/${problemId}/`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    if (!response.ok) throw new Error('删除题目失败');
    
    // 删除成功
    successMessage.value = '题目已成功删除';
    fetchProblems(currentPage.value);
    
  } catch (error) {
    console.error('删除题目错误:', error);
    errorMessage.value = '删除题目失败，请重试';
  } finally {
    loading.value = false;
  }
};

// 重置表单
const resetForm = () => {
  problemForm.value = {
    topic: null,
    title: '',
    content: '',
    answer: '',
    explanation: '',
    difficulty: '中等'
  };
  currentEditId.value = null;
  errorMessage.value = '';
  successMessage.value = '';
};

// 页面初始化
onMounted(async () => {
  await fetchSubjects();
  await fetchTopics();
  await fetchProblems();
});
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <header class="bg-primary-800 text-white px-6 py-4 shadow-md">
      <div class="container mx-auto flex justify-between items-center">
        <h1 class="text-2xl font-bold">题库管理</h1>
        <router-link to="/index" class="text-white hover:text-primary-200 transition-colors">
          返回主页
        </router-link>
      </div>
    </header>

    <div class="container mx-auto px-6 py-8 flex-grow">
      <!-- 错误消息 -->
      <div v-if="errorMessage" class="bg-red-100 text-red-800 p-3 rounded-lg mb-4">
        {{ errorMessage }}
      </div>
      
      <!-- 成功消息 -->
      <div v-if="successMessage" class="bg-green-100 text-green-800 p-3 rounded-lg mb-4">
        {{ successMessage }}
      </div>

      <!-- 题目列表视图 -->
      <div v-if="formMode === 'list'" class="space-y-6">
        <!-- 控制栏 -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
            <div class="flex flex-col md:flex-row gap-4">
              <input
                v-model="searchTerm"
                type="text"
                placeholder="搜索题目..."
                class="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              
              <select
                v-model="filterSubject"
                class="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option :value="null">所有学科</option>
                <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
                  {{ subject.name }}
                </option>
              </select>
              
              <select
                v-model="filterTopic"
                class="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option :value="null">所有知识点</option>
                <option v-for="topic in filteredTopics" :key="topic.id" :value="topic.id">
                  {{ topic.name }}
                </option>
              </select>
              
              <select
                v-model="filterDifficulty"
                class="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option :value="null">所有难度</option>
                <option v-for="option in difficultyOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              
              <button
                @click="fetchProblems(1)"
                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                筛选
              </button>
            </div>
            
            <button
              @click="formMode = 'add'; resetForm()"
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
            >
              添加题目
            </button>
          </div>
        </div>
        
        <!-- 题目列表 -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-800 mb-4">题目列表 ({{ totalProblems }})</h2>
          
          <div v-if="loading" class="text-center py-8">
            <p class="text-gray-600">加载中...</p>
          </div>
          
          <div v-else-if="problems.length === 0" class="text-center py-8">
            <p class="text-gray-600">没有找到符合条件的题目</p>
          </div>
          
          <div v-else class="overflow-x-auto">
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
                  <td class="px-6 py-4">
                    <div class="line-clamp-1">{{ problem.title }}</div>
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
                      class="text-primary-600 hover:text-primary-800 mr-4"
                    >
                      编辑
                    </button>
                    <button 
                      @click="deleteProblem(problem.id)" 
                      class="text-red-600 hover:text-red-800"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 分页 -->
          <div v-if="totalPages > 1" class="flex justify-center items-center space-x-2 mt-6">
            <button
              @click="fetchProblems(1)"
              class="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
              :disabled="currentPage === 1"
            >
              首页
            </button>
            <button
              @click="fetchProblems(currentPage - 1)"
              class="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
              :disabled="currentPage === 1"
            >
              上一页
            </button>
            <span class="text-gray-700">{{ currentPage }} / {{ totalPages }}</span>
            <button
              @click="fetchProblems(currentPage + 1)"
              class="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
              :disabled="currentPage === totalPages"
            >
              下一页
            </button>
            <button
              @click="fetchProblems(totalPages)"
              class="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
              :disabled="currentPage === totalPages"
            >
              末页
            </button>
          </div>
        </div>
      </div>

      <!-- 添加/编辑题目视图 -->
      <div v-else class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-6">
          {{ formMode === 'add' ? '添加新题目' : '编辑题目' }}
        </h2>
        
        <form @submit.prevent="saveProblem" class="space-y-6">
          <!-- 知识点选择 -->
          <div>
            <label class="block text-gray-700 text-sm font-medium mb-2">知识点 *</label>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-gray-600 text-xs mb-1">学科</label>
                <select
                  v-model="filterSubject"
                  class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option :value="null">选择学科</option>
                  <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
                    {{ subject.name }}
                  </option>
                </select>
              </div>
              
              <div>
                <label class="block text-gray-600 text-xs mb-1">知识点</label>
                <select
                  v-model="problemForm.topic"
                  class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option :value="null">选择知识点</option>
                  <option v-for="topic in filteredTopics" :key="topic.id" :value="topic.id">
                    {{ topic.name }}
                  </option>
                </select>
              </div>
            </div>
          </div>
          
          <!-- 题目标题 -->
          <div>
            <label class="block text-gray-700 text-sm font-medium mb-2">标题 *</label>
            <input
              v-model="problemForm.title"
              type="text"
              class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="输入题目标题"
              required
            />
          </div>
          
          <!-- 题目内容 -->
          <div>
            <label class="block text-gray-700 text-sm font-medium mb-2">题目内容 *</label>
            <textarea
              v-model="problemForm.content"
              rows="4"
              class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="输入题目内容"
              required
            ></textarea>
          </div>
          
          <!-- 答案 -->
          <div>
            <label class="block text-gray-700 text-sm font-medium mb-2">答案 *</label>
            <textarea
              v-model="problemForm.answer"
              rows="3"
              class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="输入参考答案"
              required
            ></textarea>
          </div>
          
          <!-- 解析 -->
          <div>
            <label class="block text-gray-700 text-sm font-medium mb-2">解析</label>
            <textarea
              v-model="problemForm.explanation"
              rows="6"
              class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="输入解析（可选）"
            ></textarea>
          </div>
          
          <!-- 难度 -->
          <div>
            <label class="block text-gray-700 text-sm font-medium mb-2">难度</label>
            <select
              v-model="problemForm.difficulty"
              class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option v-for="option in difficultyOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          
          <!-- 提交按钮 -->
          <div class="flex justify-end space-x-4">
            <button
              type="button"
              @click="formMode = 'list'"
              class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              :disabled="loading"
            >
              取消
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
              :disabled="loading"
            >
              {{ loading ? '保存中...' : '保存题目' }}
            </button>
          </div>
        </form>
      </div>

    </div>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>