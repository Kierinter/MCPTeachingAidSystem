<script setup>
import { ref, onMounted, computed } from 'vue';
import { getAuthHeaders, getCurrentUser } from '../utils/auth';
import { useRouter } from 'vue-router';

const router = useRouter();
const user = getCurrentUser();
if (!user || user.role !== 'teacher') {
  router.push('/index');
}

const students = ref([]);
const loading = ref(false);
const error = ref('');
const showAddDialog = ref(false);
const showEditDialog = ref(false);
const addForm = ref({
  student_name: '',
  student_number: '',
  addmisson_year: '',
  grade: '',
  class_name: '',
  academic_level: 'average',
  weak_subjects: '',
  notes: ''
});
const editForm = ref({});
const editingStudentId = ref(null);


const filterName = ref('')
const filterNumber = ref('')
const filterAddmissonYear = ref('')
const filterGrade = ref('')
const filterClass = ref('')
const filterLevel = ref('')
const filterWeakSubject = ref('')

const classOptions = computed(() => {
  const set = new Set(students.value.map(s => s.class_name).filter(Boolean));
  return Array.from(set);
});
const academicLevelOptions = [
  { value: 'excellent', label: '优秀' },
  { value: 'good', label: '良好' },
  { value: 'average', label: '中等' },
  { value: 'below_average', label: '中下' },
  { value: 'poor', label: '薄弱' }
];
const weakSubjectOptions = computed(() => {
  const set = new Set();
  students.value.forEach(s => {
    (s.weak_subjects_list || []).forEach(sub => set.add(sub));
  });
  return Array.from(set);
});

const filteredStudents = computed(() => {
  return students.value.filter(stu => {
    const matchName = !filterName.value || (stu.student_name && stu.student_name.includes(filterName.value))
    const matchNumber = !filterNumber.value || (stu.student_number && stu.student_number.includes(filterNumber.value))
    const matchAddmissonYear = !filterAddmissonYear.value || (stu.addmisson_year && stu.addmisson_year.includes(filterAddmissonYear.value))
    const matchGrade = !filterGrade.value || (stu.grade && stu.grade.includes(filterGrade.value))
    const matchClass = !filterClass.value || stu.class_name === filterClass.value;
    const matchLevel = !filterLevel.value || stu.academic_level === filterLevel.value;
    const matchWeak = !filterWeakSubject.value || (stu.weak_subjects_list && stu.weak_subjects_list.includes(filterWeakSubject.value));
    return matchName && matchNumber && matchAddmissonYear && matchGrade && matchClass && matchLevel && matchWeak;
  }).map(stu => ({
    ...stu,
    student_name: stu.real_name || stu.student_name || stu.username
  }));
})

const loadStudents = async () => {
  loading.value = true;
  error.value = '';
  try {
    const res = await fetch('http://localhost:8080/api/students/profiles/', {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('加载学生信息失败');
    const data = await res.json();
    students.value = Array.isArray(data) ? data.map(stu => ({
      ...stu,
      student_name: stu.real_name || stu.student_name || stu.username,
      weak_subjects_list: Array.isArray(stu.weak_subjects_list)
        ? stu.weak_subjects_list
        : (stu.weak_subjects ? stu.weak_subjects.split(',').map(s => s.trim()).filter(Boolean) : [])
    })) : [];
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};

const handleAddStudent = async () => {
  loading.value = true;
  try {
    const res = await fetch('http://localhost:8080/api/students/profiles/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(addForm.value)
    });
    let data;
    try {
      data = await res.json();
    } catch (e) {
      const text = await res.text();
      throw new Error('服务器返回异常: ' + text.slice(0, 200));
    }
    if (!res.ok) {
      throw new Error(data.detail || '添加学生失败');
    }
    showAddDialog.value = false;
    await loadStudents();
    // 重置表单
    addForm.value = {
      student_name: '',
      student_number: '',
      grade: '',
      major: '',
      class_name: '',
      academic_level: 'average',
      weak_subjects: '',
      notes: ''
    };
  } catch (e) {
    alert('添加学生失败：' + e.message);
  } finally {
    loading.value = false;
  }
};

const openEditDialog = (stu) => {
  editingStudentId.value = stu.id;
  editForm.value = {
    student_name: stu.real_name,
    student_number: stu.student_number,
    addmisson_year: stu.addmisson_year,
    grade: stu.grade,
    class_name: stu.class_name,
    academic_level: stu.academic_level,
    weak_subjects: stu.weak_subjects_list ? stu.weak_subjects_list.join(',') : '',
    notes: stu.notes
  };
  showEditDialog.value = true;
};

const handleEditStudent = async () => {
  try {
    const res = await fetch(`http://localhost:8080/api/students/profiles/${editingStudentId.value}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(editForm.value)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '修改学生失败');
    }
    showEditDialog.value = false;
    await loadStudents();
  } catch (e) {
    alert('修改学生失败：' + e.message);
  }
};

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

onMounted(loadStudents);
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <header class="bg-primary-800 text-white px-6 py-4 shadow-md">
      <div class="container mx-auto flex justify-between items-center">
        <h1 class="text-2xl font-bold">班级学生管理</h1>
        <router-link to="/index" class="text-white hover:text-primary-200 transition-colors">
          返回主页
        </router-link>
      </div>
    </header>

    <div class="container mx-auto px-6 py-8 flex-grow">
      <!-- 筛选栏 -->
      <div class="bg-white rounded-lg shadow-md p-4 mb-4 flex flex-wrap gap-4 items-center">
        <input v-model="filterName" placeholder="姓名" class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500" />
        <input v-model="filterNumber" placeholder="学号" class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500" />
        <!-- <input v-model="filterGrade" placeholder="年级" class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500" />
        <input v-model="filterClass" placeholder="班级" class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500" /> --->
        <select v-model="filterClass" class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"> 
          <option value="">全部班级</option>
          <option v-for="c in classOptions" :key="c" :value="c">{{ c }}</option>
        </select>
        <select v-model="filterLevel" class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500">
          <option value="">全部学业水平</option>
          <option v-for="opt in academicLevelOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <select v-model="filterWeakSubject" class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500">
          <option value="">全部薄弱学科</option>
          <option v-for="w in weakSubjectOptions" :key="w" :value="w">{{ w }}</option>
        </select>
      </div>
      <div v-if="error" class="bg-red-100 text-red-800 p-3 rounded-lg mb-4">{{ error }}</div>
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-semibold text-gray-800">学生列表</h2>
        <button @click="showAddDialog = true" class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors">新增学生</button>
      </div>
      <div v-if="loading" class="text-center py-8 text-gray-600">正在加载学生信息...</div>
      <div v-else class="overflow-x-auto bg-white rounded-lg shadow-md p-6">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">姓名</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">学号</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">入学年份</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">年级</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">班级</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">学业水平</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">薄弱学科</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">备注</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="stu in filteredStudents" :key="stu.id">
              <td class="px-4 py-2">{{ stu.student_name }}</td>
              <td class="px-4 py-2">{{ stu.student_number }}</td>
              <td class="px-4 py-2">{{ stu.addmisson_year }}</td>
              <td class="px-4 py-2">{{ stu.grade }}</td>
              <td class="px-4 py-2">{{ stu.class_name }}</td>
              <td class="px-4 py-2">{{ stu.academic_level_display || academicLevelLabel(stu.academic_level) }}</td>
              <td class="px-4 py-2">
                <span v-for="(subject, idx) in stu.weak_subjects_list" :key="idx" class="inline-block bg-red-100 text-red-700 px-2 py-0.5 rounded mr-1 text-xs">{{ subject }}</span>
              </td>
              <td class="px-4 py-2">{{ stu.notes }}</td>
              <td class="px-4 py-2">
                <button @click="openEditDialog(stu)" class="px-2 py-1 bg-primary-600 text-white rounded hover:bg-primary-700">编辑</button>
              </td>
            </tr>
            <tr v-if="filteredStudents.length === 0">
              <td colspan="9" class="text-center text-gray-500 py-4">暂无学生信息</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 新增学生弹窗 -->
      <div v-if="showAddDialog" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md relative overflow-y-auto max-h-[80vh]">
          <h3 class="text-lg font-semibold mb-4">新增学生</h3>
          <form @submit.prevent="handleAddStudent" class="space-y-4">
            <div>
              <label class="block text-gray-700 text-sm mb-1">姓名</label>
              <input v-model="addForm.student_name" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" required />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">学号</label>
              <input v-model="addForm.student_number" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" required />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">入学年份</label>
              <input v-model="addForm.addmisson_year" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">年级</label>
              <input v-model="addForm.grade" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">班级</label>
              <input v-model="addForm.class_name" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">学业水平</label>
              <select v-model="addForm.academic_level" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
                <option v-for="opt in academicLevelOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">薄弱学科</label>
              <input v-model="addForm.weak_subjects" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" placeholder="用逗号分隔" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">备注</label>
              <textarea v-model="addForm.notes" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"></textarea>
            </div>
            <div class="flex justify-end space-x-3 mt-4">
              <button type="button" @click="showAddDialog = false" class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">取消</button>
              <button type="submit" class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">保存</button>
            </div>
          </form>
        </div>
      </div>

      <!-- 编辑学生弹窗 -->
      <div v-if="showEditDialog" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md relative overflow-y-auto max-h-[80vh]">
          <h3 class="text-lg font-semibold mb-4">编辑学生</h3>
          <form @submit.prevent="handleEditStudent" class="space-y-4">
            <div>
              <label class="block text-gray-700 text-sm mb-1">姓名</label>
              <input v-model="editForm.student_name" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" required />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">学号</label>
              <input v-model="editForm.student_number" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" required />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">年级</label>
              <input v-model="editForm.grade" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">专业</label>
              <input v-model="editForm.major" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">班级</label>
              <input v-model="editForm.class_name" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">学业水平</label>
              <select v-model="editForm.academic_level" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
                <option v-for="opt in academicLevelOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">薄弱学科</label>
              <input v-model="editForm.weak_subjects" type="text" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" placeholder="用逗号分隔" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm mb-1">备注</label>
              <textarea v-model="editForm.notes" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"></textarea>
            </div>
            <div class="flex justify-end space-x-3 mt-4">
              <button type="button" @click="showEditDialog = false" class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">取消</button>
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