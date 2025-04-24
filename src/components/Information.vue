<script setup>
import { onMounted } from 'vue'
import Chart from 'chart.js/auto'

onMounted(() => {
  const ctx = document.getElementById('scoreChart').getContext('2d')
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['第1次月考', '第2次月考', '第3次月考'],
      datasets: [{
        label: '班级平均分',
        data: [75, 78, 82],
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
        tension: 0.4
      }]
    },
    options: {
      scales: {
        y: { beginAtZero: true, max: 100 }
      }
    }
  })
})
</script>

<template>
  <div class="bg-gray-50 p-6 font-sans">
    <!-- 班级概况 -->
    <div class="bg-white p-6 rounded-xl shadow mb-6">
      <h2 class="text-xl font-bold mb-4">班级信息 - 高二(3)班</h2>
      <div class="flex gap-8 text-gray-700">
        <div>学生人数：<strong>42人</strong></div>
        <div>平均分：<strong>78.5</strong></div>
        <div>班级总分排名：<strong>全校第 5</strong></div>
        <div>月考次数：<strong>3次</strong></div>
      </div>
    </div>

    <!-- 三个图表并排显示 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 成绩走势图表 -->
      <div class="bg-white p-6 rounded-xl shadow">
        <h3 class="text-lg font-semibold mb-4">月考成绩走势</h3>
        <canvas id="scoreChart" height="200"></canvas>
      </div>

      <!-- 学困生 -->
      <div class="bg-white p-6 rounded-xl shadow">
        <h3 class="text-lg font-semibold mb-4 text-red-600">学困生（总分 &lt; 60）</h3>
        <ul class="text-gray-700 space-y-2">
          <li>李明 - 总分：56（语文40 数学38 英语55）</li>
          <li>张婷 - 总分：52（语文50 数学30 英语60）</li>
          <li>韩磊 - 总分：48（语文35 数学32 英语45）</li>
        </ul>
      </div>

      <!-- 偏科预警 -->
      <div class="bg-white p-6 rounded-xl shadow">
        <h3 class="text-lg font-semibold mb-4 text-yellow-600">偏科预警</h3>
        <ul class="text-gray-700 space-y-2">
          <li>王杰 - 数学 38（语文80 英语82）</li>
          <li>林静 - 英语 40（语文85 数学90）</li>
          <li>周旭 - 语文 42（数学78 英语75）</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import 'https://cdn.tailwindcss.com';
</style> 