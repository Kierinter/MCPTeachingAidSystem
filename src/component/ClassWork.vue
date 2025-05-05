<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { getAuthHeaders, getCurrentUser } from '../utils/auth';
import { useRouter } from 'vue-router';

const router = useRouter();
const user = getCurrentUser();
const userRole = user?.role || 'student';

const classworks = ref([]); // 作业列表
const submissions = ref([]); // 当前作业的提交列表（教师）
const mySubmission = ref(null); // 当前作业的我的提交（学生）
const showCreateDialog = ref(false);
const showDetailDialog = ref(false);
const showSubmitDialog = ref(false);
const showReviewDialog = ref(false);
const currentClasswork = ref(null);
const newWork = ref({
  title: '',
  description: '',
  class_name: '',
  deadline: ''
});
const submitContent = ref('');
const reviewScore = ref('');
const reviewFeedback = ref('');
const loading = ref(false);
const error = ref('');
const classList = ref([]);

const showAIGenerateDialog = ref(false);
const aiForm = ref({
  subject: '',
  topic: '',
  difficulty: '',
  count: 3
});
const aiLoading = ref(false);
const aiError = ref('');
const aiResult = ref([]);
const subjectOptions = ref(['数学', '物理', '化学', '英语', '生物']);
const difficultyOptions = ref(['简单', '中等', '较难', '困难']);
const topicOptions = ref(['导数', '积分', '线性代数', '几何', '概率论']);

// 添加计算属性，过滤出有效的AI生成题目（具有题目、答案和解析字段的）
const validAIProblems = computed(() => 
  aiResult.value.filter(p => p && typeof p === 'object' && p['题目'] && p['答案'] && p['解析'])
);

// 获取知识点（topic）列表
const fetchTopicOptions = async (subject) => {
  if (!subject) {
    topicOptions.value = [];
    return;
  }
  try {
    const res = await fetch(`http://localhost:8080/api/problems/topics/?subject=${encodeURIComponent(subject)}`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const data = await res.json();
      topicOptions.value = data.map(t => t.name);
    }
  } catch {}
};

watch(() => aiForm.value.subject, (val) => {
  fetchTopicOptions(val);
  aiForm.value.topic = '';
});

const handleAIGenerate = async () => {
  aiLoading.value = true;
  aiError.value = '';
  aiResult.value = [];
  try {
    const res = await fetch('http://localhost:8080/api/problems/ai_generate_problems/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(aiForm.value)
    });
    
    console.log(aiForm.value, res);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'AI生成失败');
    aiResult.value = data.problems || [];
  } catch (e) {
    aiError.value = e.message;
  } finally {
    aiLoading.value = false;
  }
};

const useAIResult = () => {
  if (!aiResult.value.length) return;
  // 将AI生成的题目拼接到作业描述
  const text = aiResult.value.map((p, idx) => `【题目${idx+1}】\n${p['题目'] || ''}\n【答案】${p['答案'] || ''}\n【解析】${p['解析'] || ''}`).join('\n\n');
  newWork.value.description = (newWork.value.description ? newWork.value.description + '\n\n' : '') + text;
  showAIGenerateDialog.value = false;
};

const copyAllContent = (type) => {
  const content = validAIProblems.value.map((p, idx) => `${idx+1}. ${p[type]}`).join('\n\n');
  navigator.clipboard.writeText(content);
};

const copyFormattedContent = () => {
  const content = validAIProblems.value.map((p, idx) => 
    `题目${idx+1}：${p['题目']}\n\n答案${idx+1}：${p['答案']}\n\n解析${idx+1}：${p['解析']}`
  ).join('\n\n-----------------\n\n');
  navigator.clipboard.writeText(content);
};

// 获取班级列表（仅教师）
const fetchClassList = async () => {
  if (userRole !== 'teacher') return;
  try {
    const res = await fetch('http://localhost:8080/api/students/profiles/', {
      headers: getAuthHeaders()
    });
    if (!res.ok) return;
    const data = await res.json();
    const set = new Set();
    data.forEach(stu => {
      if (stu.class_name) set.add(stu.class_name);
    });
    classList.value = Array.from(set);
  } catch {}
};

// 获取作业列表
const fetchClassWorks = async () => {
  loading.value = true;
  try {
    const res = await fetch('http://localhost:8080/api/students/classworks/', {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('获取作业失败');
    classworks.value = await res.json();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};

// 教师布置作业
const handleCreateWork = async () => {
  loading.value = true;
  try {
    const res = await fetch('http://localhost:8080/api/students/classworks/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(newWork.value)
    });
    if (!res.ok) throw new Error('布置作业失败');
    showCreateDialog.value = false;
    await fetchClassWorks();
    newWork.value = { title: '', description: '', class_name: '', deadline: '' };
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};

// 查看作业详情
const openDetail = async (cw) => {
  currentClasswork.value = cw;
  showDetailDialog.value = true;
  if (userRole === 'teacher') {
    // 获取提交列表
    const res = await fetch(`http://localhost:8080/api/students/classworks/${cw.id}/submissions/`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      submissions.value = await res.json();
    }
  } else {
    // 获取我的提交
    const res = await fetch(`http://localhost:8080/api/students/studentworks/?classwork=${cw.id}`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const arr = await res.json();
      mySubmission.value = arr.length ? arr[0] : null;
    }
  }
};

// 学生提交作业
const handleSubmitWork = async () => {
  loading.value = true;
  try {
    const res = await fetch('http://localhost:8080/api/students/studentworks/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        classwork: currentClasswork.value.id,
        content: submitContent.value
      })
    });
    if (!res.ok) throw new Error('提交失败');
    showSubmitDialog.value = false;
    await openDetail(currentClasswork.value);
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};

// 教师批改作业
const openReview = (submission) => {
  reviewScore.value = submission.score || '';
  reviewFeedback.value = submission.feedback || '';
  currentClasswork.value = submission;
  showReviewDialog.value = true;
};
const handleReview = async () => {
  loading.value = true;
  try {
    const res = await fetch(`http://localhost:8080/api/students/studentworks/${currentClasswork.value.id}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ score: reviewScore.value, feedback: reviewFeedback.value })
    });
    if (!res.ok) throw new Error('批改失败');
    showReviewDialog.value = false;
    await openDetail(currentClasswork.value.classwork);
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await fetchClassList();
  await fetchClassWorks();
});
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <header class="bg-primary-800 text-white px-6 py-4 shadow-md">
      <div class="container mx-auto flex justify-between items-center">
        <h1 class="text-2xl font-bold">课堂作业</h1>
        <router-link to="/index" class="text-white hover:text-primary-200 transition-colors">
          返回主页
        </router-link>
      </div>
    </header>
    <div class="container mx-auto px-6 py-8 flex-grow">
      <div v-if="error" class="bg-red-100 text-red-800 p-3 rounded mb-4">{{ error }}</div>
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-semibold text-gray-800">作业列表</h2>
        <button v-if="userRole==='teacher'" @click="showCreateDialog=true" class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">布置作业</button>
      </div>
      <div v-if="loading" class="text-center py-8 text-gray-600">加载中...</div>
      <div v-else class="overflow-x-auto bg-white rounded-lg shadow-md p-6">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">标题</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">班级</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">截止时间</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cw in classworks" :key="cw.id">
              <td class="px-4 py-2">{{ cw.title }}</td>
              <td class="px-4 py-2">{{ cw.class_name }}</td>
              <td class="px-4 py-2">{{ cw.deadline?.replace('T',' ').slice(0,16) }}</td>
              <td class="px-4 py-2">
                <button @click="openDetail(cw)" class="text-primary-600 hover:text-primary-800">详情</button>
              </td>
            </tr>
            <tr v-if="classworks.length===0">
              <td colspan="4" class="text-center text-gray-500 py-4">暂无作业</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 布置作业弹窗 -->
      <div v-if="showCreateDialog" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md relative">
          <h3 class="text-lg font-semibold mb-4">布置新作业</h3>
          <form @submit.prevent="handleCreateWork" class="space-y-4">
            <div>
              <label class="block text-gray-700 text-sm mb-1">标题</label>
              <input v-model="newWork.title" type="text" class="w-full border border-gray-300 rounded px-3 py-2" required />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">班级</label>
              <select v-model="newWork.class_name" class="w-full border border-gray-300 rounded px-3 py-2">
                <option value="">请选择</option>
                <option v-for="c in classList" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">截止时间</label>
              <input v-model="newWork.deadline" type="datetime-local" class="w-full border border-gray-300 rounded px-3 py-2" required />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">描述</label>
              <textarea v-model="newWork.description" class="w-full border border-gray-300 rounded px-3 py-2"></textarea>
            </div>
            <div class="flex justify-between items-center mt-2">
              <button type="button" @click="showAIGenerateDialog=true" class="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200">AI生成练习</button>
              <div class="flex gap-3">
                <button type="button" @click="showCreateDialog=false" class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">取消</button>
                <button type="submit" class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">保存</button>
              </div>
            </div>
          </form>
        </div>
      </div>

      <!-- AI生成练习弹窗 -->
      <div v-if="showAIGenerateDialog" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-lg relative">
          <h3 class="text-lg font-semibold mb-4">AI生成练习题</h3>
          <form @submit.prevent="handleAIGenerate" class="space-y-4">
            <div>
              <label class="block text-gray-700 text-sm mb-1">科目</label>
              <select v-model="aiForm.subject" class="w-full border border-gray-300 rounded px-3 py-2" required>
                <option value="">请选择</option>
                <option v-for="s in subjectOptions" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">知识点</label>
              <select v-model="aiForm.topic" class="w-full border border-gray-300 rounded px-3 py-2" required>
                <option value="">请选择</option>
                <option v-for="t in topicOptions" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">难度</label>
              <select v-model="aiForm.difficulty" class="w-full border border-gray-300 rounded px-3 py-2" required>
                <option value="">请选择</option>
                <option v-for="d in difficultyOptions" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">题目数量</label>
              <input v-model.number="aiForm.count" type="number" min="1" max="10" class="w-full border border-gray-300 rounded px-3 py-2" required />
            </div>
            <div class="flex justify-end gap-3 mt-4">
              <button type="button" @click="showAIGenerateDialog=false" class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">取消</button>
              <button type="submit" class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700" :disabled="aiLoading">{{ aiLoading ? '生成中...' : '生成' }}</button>
            </div>
          </form>
          <div v-if="aiError" class="bg-red-100 text-red-800 p-2 rounded mt-2">{{ aiError }}</div>
          <div v-if="aiResult.length" class="mt-4">
            <h4 class="font-semibold mb-2">生成结果：</h4>
            <div class="max-h-64 overflow-y-auto bg-gray-50 rounded p-2 text-sm">
              <!-- 集中显示所有题目，带复制按钮 -->
              <div class="mb-4 relative">
                <div class="flex justify-between items-center mb-1">
                  <b>所有题目：</b>
                  <button @click="copyAllContent('题目')" class="text-xs bg-blue-100 text-blue-700 rounded px-2 py-1 hover:bg-blue-200">复制全部题目</button>
                </div>
                <div class="bg-white border rounded p-2 whitespace-pre-line">
                  <div v-for="(p, idx) in validAIProblems" :key="'q'+idx" class="mb-2">
                    <div><b>{{ idx+1 }}. </b>{{ p['题目'] }}</div>
                  </div>
                </div>
              </div>

              <!-- 集中显示所有答案，带复制按钮 -->
              <div class="mb-4 relative">
                <div class="flex justify-between items-center mb-1">
                  <b>所有答案：</b>
                  <button @click="copyAllContent('答案')" class="text-xs bg-green-100 text-green-700 rounded px-2 py-1 hover:bg-green-200">复制全部答案</button>
                </div>
                <div class="bg-white border rounded p-2 whitespace-pre-line">
                  <div v-for="(p, idx) in validAIProblems" :key="'a'+idx" class="mb-2">
                    <div><b>{{ idx+1 }}. </b>{{ p['答案'] }}</div>
                  </div>
                </div>
              </div>

              <!-- 集中显示所有解析，带复制按钮 -->
              <div class="mb-4 relative">
                <div class="flex justify-between items-center mb-1">
                  <b>所有解析：</b>
                  <button @click="copyAllContent('解析')" class="text-xs bg-yellow-100 text-yellow-700 rounded px-2 py-1 hover:bg-yellow-200">复制全部解析</button>
                </div>
                <div class="bg-white border rounded p-2 whitespace-pre-line">
                  <div v-for="(p, idx) in validAIProblems" :key="'e'+idx" class="mb-2">
                    <div><b>{{ idx+1 }}. </b>{{ p['解析'] }}</div>
                  </div>
                </div>
              </div>

              <!-- 完整格式化内容的复制按钮 -->
              <button @click="copyFormattedContent()" class="w-full mt-2 px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700">
                复制完整格式化内容（题目+答案+解析）
              </button>
            </div>
            <button @click="useAIResult" class="mt-2 px-4 py-1 bg-green-600 text-white rounded hover:bg-green-700">全部填入作业描述</button>
          </div>
        </div>
      </div>

      <!-- 作业详情弹窗 -->
      <div v-if="showDetailDialog" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-2xl relative overflow-y-auto max-h-[80vh]">
          <h3 class="text-lg font-semibold mb-4">作业详情</h3>
          <div class="mb-2"><b>标题：</b>{{ currentClasswork.title }}</div>
          <div class="mb-2"><b>班级：</b>{{ currentClasswork.class_name }}</div>
          <div class="mb-2"><b>截止时间：</b>{{ currentClasswork.deadline?.replace('T',' ').slice(0,16) }}</div>
          <div class="mb-2"><b>描述：</b>{{ currentClasswork.description }}</div>
          <div v-if="userRole==='student'">
            <div v-if="mySubmission">
              <div class="mt-4 p-3 bg-green-50 rounded">已提交：{{ mySubmission.content }}</div>
              <div v-if="mySubmission.score !== null" class="mt-2">成绩：{{ mySubmission.score }}<br/>评语：{{ mySubmission.feedback }}</div>
            </div>
            <div v-else class="mt-4">
              <button @click="showSubmitDialog=true" class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">提交作业</button>
            </div>
          </div>
          <div v-if="userRole==='teacher'">
            <h4 class="mt-4 font-semibold">学生提交</h4>
            <table class="min-w-full divide-y divide-gray-200 mt-2">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase">学生</th>
                  <th class="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase">内容</th>
                  <th class="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase">提交时间</th>
                  <th class="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase">分数</th>
                  <th class="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase">评语</th>
                  <th class="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="sub in submissions" :key="sub.id">
                  <td class="px-2 py-1">{{ sub.student_name }}</td>
                  <td class="px-2 py-1">{{ sub.content }}</td>
                  <td class="px-2 py-1">{{ sub.submitted_at?.replace('T',' ').slice(0,16) }}</td>
                  <td class="px-2 py-1">{{ sub.score ?? '-' }}</td>
                  <td class="px-2 py-1">{{ sub.feedback }}</td>
                  <td class="px-2 py-1">
                    <button @click="openReview(sub)" class="text-primary-600 hover:text-primary-800">批改</button>
                  </td>
                </tr>
                <tr v-if="submissions.length===0">
                  <td colspan="6" class="text-center text-gray-500 py-2">暂无提交</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="flex justify-end mt-6">
            <button @click="showDetailDialog=false" class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">关闭</button>
          </div>
        </div>
      </div>

      <!-- 学生提交作业弹窗 -->
      <div v-if="showSubmitDialog" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md relative">
          <h3 class="text-lg font-semibold mb-4">提交作业</h3>
          <form @submit.prevent="handleSubmitWork" class="space-y-4">
            <div>
              <label class="block text-gray-700 text-sm mb-1">作业内容</label>
              <textarea v-model="submitContent" class="w-full border border-gray-300 rounded px-3 py-2" required></textarea>
            </div>
            <div class="flex justify-end space-x-3 mt-4">
              <button type="button" @click="showSubmitDialog=false" class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">取消</button>
              <button type="submit" class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">提交</button>
            </div>
          </form>
        </div>
      </div>

      <!-- 教师批改作业弹窗 -->
      <div v-if="showReviewDialog" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md relative">
          <h3 class="text-lg font-semibold mb-4">批改作业</h3>
          <form @submit.prevent="handleReview" class="space-y-4">
            <div>
              <label class="block text-gray-700 text-sm mb-1">分数</label>
              <input v-model="reviewScore" type="number" min="0" max="100" class="w-full border border-gray-300 rounded px-3 py-2" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">评语</label>
              <textarea v-model="reviewFeedback" class="w-full border border-gray-300 rounded px-3 py-2"></textarea>
            </div>
            <div class="flex justify-end space-x-3 mt-4">
              <button type="button" @click="showReviewDialog=false" class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">取消</button>
              <button type="submit" class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">保存</button>
            </div>
          </form>
        </div>
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