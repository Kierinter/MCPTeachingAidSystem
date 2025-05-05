<script setup>
import { ref, onMounted } from 'vue';
import { getAuthHeaders } from '../utils/auth';
const wrongRecords = ref([]);
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const currentRecord = ref(null);
const redoAnswer = ref('');
const submitLoading = ref(false);
const showRedoResult = ref(false);

const fetchWrongBook = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const res = await fetch('http://localhost:8080/api/problems/records/wrongbook/', {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('获取错题本失败');
    const data = await res.json();
    wrongRecords.value = data;
  } catch (e) {
    errorMessage.value = '获取错题本失败，请刷新重试';
  } finally {
    loading.value = false;
  }
};

const startRedo = (rec) => {
  currentRecord.value = rec;
  redoAnswer.value = '';
  showRedoResult.value = false;
  successMessage.value = '';
};

const submitRedo = async () => {
  if (!currentRecord.value) return;
  submitLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  try {
    const res = await fetch('http://localhost:8080/api/problems/records/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        problem: currentRecord.value.problem_id,
        user_answer: redoAnswer.value,
        time_spent: 0
      })
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || '提交失败');
    }
    successMessage.value = '提交成功！';
    showRedoResult.value = true;
    // 刷新错题本
    await fetchWrongBook();
  } catch (e) {
    errorMessage.value = e.message || '提交失败';
  } finally {
    submitLoading.value = false;
  }
};

function formatDate(dt) {
  if (!dt) return '';
  const d = new Date(dt);
  return d.toLocaleString();
}

onMounted(fetchWrongBook);
</script>
<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <header class="bg-primary-800 text-white px-6 py-4 shadow-md">
      <div class="container mx-auto flex justify-between items-center">
        <h1 class="text-2xl font-bold">错题本</h1>
        <router-link to="/index" class="text-white hover:text-primary-200 transition-colors">
          返回主页
        </router-link>
      </div>
    </header>
    <div class="container mx-auto px-6 py-8 flex-grow">
      <div v-if="loading" class="text-center py-8">
        <p class="text-gray-600">加载中...</p>
      </div>
      <div v-if="errorMessage" class="bg-red-100 text-red-800 p-3 rounded-lg mb-4">
        {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="bg-green-100 text-green-800 p-3 rounded-lg mb-4">
        {{ successMessage }}
      </div>
      <div v-if="!currentRecord && wrongRecords.length" class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">我的错题本 ({{ wrongRecords.length }} 题)</h2>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">标题</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">知识点</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">难度</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">上次作答</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="rec in wrongRecords" :key="rec.record_id">
                <td class="px-6 py-4 whitespace-nowrap max-w-[300px]">
                  <div class="truncate" :title="rec.title">{{ rec.title }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">{{ rec.topic_name }}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 py-1 rounded text-xs font-medium"
                    :class="{
                      'bg-green-100 text-green-800': rec.difficulty === '简单',
                      'bg-yellow-100 text-yellow-800': rec.difficulty === '中等',
                      'bg-orange-100 text-orange-800': rec.difficulty === '较难',
                      'bg-red-100 text-red-800': rec.difficulty === '困难'
                    }"
                  >{{ rec.difficulty }}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">{{ formatDate(rec.attempted_at) }}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <button @click="startRedo(rec)" class="text-primary-600 hover:text-primary-800">重新练习</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-if="currentRecord" class="bg-white rounded-lg shadow-md p-6">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-semibold text-gray-800">
            {{ currentRecord.topic_name }} · {{ currentRecord.difficulty }}
          </h2>
          <button @click="currentRecord = null" class="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors">
            返回错题本
          </button>
        </div>
        <div class="mb-8">
          <h3 class="font-medium text-lg mb-2">题目内容:</h3>
          <div class="bg-gray-50 p-4 rounded-md">{{ currentRecord.content }}</div>
        </div>
        <div class="mb-8">
          <h3 class="font-medium text-lg mb-2">你的上次答案:</h3>
          <div class="bg-yellow-50 p-4 rounded-md">{{ currentRecord.user_answer }}</div>
        </div>
        <div class="mb-8">
          <h3 class="font-medium text-lg mb-2">重新作答:</h3>
          <textarea v-model="redoAnswer" rows="4" class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500" :disabled="submitLoading" placeholder="请在此输入你的新答案..."></textarea>
        </div>
        <div class="flex justify-end">
          <button @click="submitRedo" class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors" :disabled="submitLoading">
            {{ submitLoading ? '提交中...' : '提交新答案' }}
          </button>
        </div>
        <div v-if="showRedoResult" class="mt-6 space-y-4">
          <div>
            <h3 class="font-medium text-lg mb-2 text-green-600">参考答案:</h3>
            <div class="bg-green-50 p-4 rounded-md">{{ currentRecord.answer }}</div>
          </div>
          <div>
            <h3 class="font-medium text-lg mb-2 text-blue-600">解析:</h3>
            <div class="bg-blue-50 p-4 rounded-md whitespace-pre-wrap">{{ currentRecord.explanation }}</div>
          </div>
        </div>
      </div>
      <div v-if="!wrongRecords.length && !loading" class="bg-white rounded-lg shadow-md p-6 text-center">
        <p class="text-gray-600">暂无错题，继续加油！</p>
      </div>
    </div>
  </div>
</template> 