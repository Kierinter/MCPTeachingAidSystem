<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getAuthHeaders } from '../utils/auth';

const route = useRoute();
const router = useRouter();
const checkInId = computed(() => route.params.id);

// 数据存储
const checkInDetails = ref(null);
const studentList = ref([]);
const isLoading = ref(true);
const error = ref(null);

// 分类统计
const statistics = computed(() => {
    if (!checkInDetails.value) return { total: 0, present: 0, late: 0, absent: 0 };

    return {
        total: checkInDetails.value.total_students || 0,
        present: checkInDetails.value.checked_in_count || 0,
        late: checkInDetails.value.late_count || 0,
        absent: checkInDetails.value.absent_count || 0
    };
});

// 计算签到百分比
const attendanceRate = computed(() => {
    if (statistics.value.total === 0) return 0;
    return Math.round(((statistics.value.present + statistics.value.late) / statistics.value.total) * 100);
});

// 加载签到详情数据
const loadCheckInDetails = async () => {
    isLoading.value = true;
    error.value = null;

    try {
        const response = await fetch(`http://localhost:8080/api/courses/check-in/${checkInId.value}/`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('获取签到详情失败');
        }

        checkInDetails.value = await response.json();
    } catch (err) {
        console.error('获取签到详情时出错:', err);
        error.value = '无法加载签到详情，请稍后重试';

        // 开发环境模拟数据
        if (process.env.NODE_ENV === 'development') {
            checkInDetails.value = {
                id: checkInId.value,
                course_name: '高等数学 (II)',
                check_in_code: '853421',
                created_at: '2025-04-30T10:00:00Z',
                expires_at: '2025-04-30T10:15:00Z',
                status: 'active',
                total_students: 45,
                checked_in_count: 38,
                late_count: 4,
                absent_count: 3,
                check_in_status: '进行中',
                time_left: 489
            };
        }
    } finally {
        isLoading.value = false;
    }
};

// 加载学生签到列表
const loadStudentList = async () => {
    try {
        const response = await fetch(`http://localhost:8080/api/courses/check-in/${checkInId.value}/students/`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('获取学生签到列表失败');
        }

        studentList.value = await response.json();
    } catch (err) {
        console.error('获取学生签到列表时出错:', err);

        // 开发环境模拟数据
        if (process.env.NODE_ENV === 'development') {
            studentList.value = [
                {
                    id: 1,
                    student_name: '张三',
                    check_in_time_display: '2025-04-30 10:02:15',
                    status: 'success',
                    location: '教室前排'
                },
                {
                    id: 2,
                    student_name: '李四',
                    check_in_time_display: '2025-04-30 10:05:42',
                    status: 'success',
                    location: '教室后排'
                },
                {
                    id: 3,
                    student_name: '王五',
                    check_in_time_display: '2025-04-30 10:12:07',
                    status: 'late',
                    location: '教室门口'
                }
            ];
        }
    }
};

// 获取状态对应的样式
const getStatusClass = (status) => {
    switch (status) {
        case 'success':
            return 'text-green-600 bg-green-100';
        case 'late':
            return 'text-yellow-600 bg-yellow-100';
        case 'absent':
            return 'text-red-600 bg-red-100';
        default:
            return 'text-gray-600 bg-gray-100';
    }
};

// 获取状态显示文本
const getStatusText = (status) => {
    switch (status) {
        case 'success':
            return '正常';
        case 'late':
            return '迟到';
        case 'absent':
            return '缺勤';
        default:
            return '未知';
    }
};

// 关闭签到
const endCheckIn = async () => {
    if (!confirm('确定要结束当前签到吗？')) return;

    try {
        // 这里实现关闭签到的API调用
        const response = await fetch(`http://localhost:8080/api/courses/check-in/${checkInId.value}/end/`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('结束签到失败');
        }

        // 重新加载签到详情
        await loadCheckInDetails();
        alert('签到已结束');
    } catch (err) {
        console.error('结束签到时出错:', err);
        alert('结束签到失败，请稍后重试');
    }
};

// 导出签到记录
const exportAttendance = async () => {
    try {
        // 实际项目中，这里应该调用API来生成并下载Excel文件
        alert('签到记录导出功能正在开发中');
    } catch (err) {
        console.error('导出签到记录时出错:', err);
        alert('导出签到记录失败，请稍后重试');
    }
};

// 返回签到页面
const goBack = () => {
    router.push('/checkin');
};

// 页面加载时获取数据
onMounted(async () => {
    await loadCheckInDetails();
    await loadStudentList();
});
</script>

<template>
    <div class="min-h-screen bg-gray-100 py-8">
        <div class="max-w-4xl mx-auto px-4">
            <!-- 顶部导航 -->
            <div class="flex justify-between items-center mb-8">
                <h1 class="text-2xl font-bold text-gray-800">签到详情</h1>
                <button @click="goBack" class="text-primary-600 hover:text-primary-800 flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" viewBox="0 0 20 20"
                        fill="currentColor">
                        <path fill-rule="evenodd"
                            d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
                            clip-rule="evenodd" />
                    </svg>
                    返回签到页面
                </button>
            </div>

            <!-- 加载中状态 -->
            <div v-if="isLoading" class="bg-white rounded-lg shadow-sm p-8 text-center">
                <div class="animate-pulse">
                    <div class="h-8 bg-gray-200 rounded w-1/2 mx-auto mb-4"></div>
                    <div class="h-4 bg-gray-200 rounded w-1/3 mx-auto mb-2"></div>
                    <div class="h-4 bg-gray-200 rounded w-1/4 mx-auto"></div>
                </div>
                <p class="mt-4 text-gray-600">正在加载签到详情...</p>
            </div>

            <!-- 错误提示 -->
            <div v-else-if="error" class="bg-white rounded-lg shadow-sm p-8 text-center">
                <div class="text-red-600 mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24"
                        stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <p class="text-lg font-medium text-gray-800 mb-2">出错了</p>
                <p class="text-gray-600">{{ error }}</p>
                <button @click="loadCheckInDetails"
                    class="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                    重试
                </button>
            </div>

            <!-- 签到详情 -->
            <div v-else>
                <!-- 签到信息卡片 -->
                <div class="bg-white rounded-xl shadow-sm p-6 mb-6">
                    <div class="flex justify-between items-start">
                        <div>
                            <h2 class="text-xl font-semibold text-gray-800">{{ checkInDetails.course_name }}</h2>
                            <div class="mt-2 space-y-1">
                                <div class="text-sm text-gray-600">
                                    创建时间: {{ new Date(checkInDetails.created_at).toLocaleString() }}
                                </div>
                                <div class="text-sm text-gray-600">
                                    签到状态:
                                    <span :class="{
                                        'text-green-600': checkInDetails.check_in_status === '进行中',
                                        'text-red-600': checkInDetails.check_in_status === '已结束',
                                        'text-gray-600': checkInDetails.check_in_status === '已取消'
                                    }">{{ checkInDetails.check_in_status }}</span>
                                </div>
                                <div class="text-sm text-gray-600">
                                    签到码: <span class="font-medium">{{ checkInDetails.check_in_code }}</span>
                                </div>
                                <div v-if="checkInDetails.check_in_status === '进行中'" class="text-sm text-gray-600">
                                    剩余时间: <span class="font-medium">{{ Math.floor(checkInDetails.time_left / 60) }}分{{
                                        checkInDetails.time_left % 60 }}秒</span>
                                </div>
                            </div>
                        </div>

                        <div v-if="checkInDetails.check_in_status === '进行中'" class="space-x-2">
                            <button @click="endCheckIn"
                                class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition-colors">
                                结束签到
                            </button>
                        </div>
                    </div>
                </div>

                <!-- 签到统计 -->
                <div class="bg-white rounded-xl shadow-sm p-6 mb-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-4">签到情况统计</h3>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-blue-50 p-3 rounded-lg text-center">
                            <div class="text-blue-600 text-2xl font-bold">{{ statistics.total }}</div>
                            <div class="text-sm text-gray-600">总人数</div>
                        </div>
                        <div class="bg-green-50 p-3 rounded-lg text-center">
                            <div class="text-green-600 text-2xl font-bold">{{ statistics.present }}</div>
                            <div class="text-sm text-gray-600">已签到</div>
                        </div>
                        <div class="bg-yellow-50 p-3 rounded-lg text-center">
                            <div class="text-yellow-600 text-2xl font-bold">{{ statistics.late }}</div>
                            <div class="text-sm text-gray-600">迟到</div>
                        </div>
                        <div class="bg-red-50 p-3 rounded-lg text-center">
                            <div class="text-red-600 text-2xl font-bold">{{ statistics.absent }}</div>
                            <div class="text-sm text-gray-600">缺勤</div>
                        </div>
                    </div>

                    <!-- 签到率 -->
                    <div class="mt-4">
                        <div class="flex justify-between items-center mb-1">
                            <div class="text-sm font-medium text-gray-700">签到率</div>
                            <div class="text-sm font-medium text-gray-700">{{ attendanceRate }}%</div>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2.5">
                            <div class="bg-primary-600 h-2.5 rounded-full" :style="`width: ${attendanceRate}%`"></div>
                        </div>
                    </div>
                </div>

                <!-- 操作按钮 -->
                <div class="flex justify-end mb-6">
                    <button @click="exportAttendance"
                        class="px-4 py-2 bg-gray-700 text-white rounded-lg text-sm hover:bg-gray-800 transition-colors flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" viewBox="0 0 20 20"
                            fill="currentColor">
                            <path fill-rule="evenodd"
                                d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z"
                                clip-rule="evenodd" />
                        </svg>
                        导出签到记录
                    </button>
                </div>

                <!-- 学生签到列表 -->
                <div class="bg-white rounded-xl shadow-sm overflow-hidden">
                    <h3 class="text-lg font-semibold text-gray-800 p-6 pb-3">学生签到列表</h3>

                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th scope="col"
                                        class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        学生
                                    </th>
                                    <th scope="col"
                                        class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        签到时间
                                    </th>
                                    <th scope="col"
                                        class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        状态
                                    </th>
                                    <th scope="col"
                                        class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        位置
                                    </th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                <tr v-for="student in studentList" :key="student.id">
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                        {{ student.student_name }}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {{ student.check_in_time_display }}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <span
                                            :class="`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClass(student.status)}`">
                                            {{ getStatusText(student.status) }}
                                        </span>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {{ student.location || '未记录' }}
                                    </td>
                                </tr>

                                <!-- 如果没有学生签到 -->
                                <tr v-if="studentList.length === 0">
                                    <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500">
                                        暂无学生签到记录
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>