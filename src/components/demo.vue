
<script setup>
import { ref } from 'vue'
// Please install OpenAI SDK first: `npm install openai`

import OpenAI from "openai";

const openai = new OpenAI({
        baseURL: 'https://api.deepseek.com',
        apiKey: 'sk-a70f9b3a6d5546f5bdead56eaffa92a2'
});

async function main() {
  const completion = await openai.chat.completions.create({
    messages: [{ role: "system", content: "You are a helpful assistant." }],
    model: "deepseek-chat",
  });

  console.log(completion.choices[0].message.content);
}

main();
const form = ref({
  subject: '',
  grade: '',
  keywords: ''
})

const loading = ref(false)
const plan = ref('')

async function generatePlan() {
  loading.value = true
  plan.value = ''

  try {
    const res = await fetch('https://api.example.com/lessonplan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(form.value)
    })

    const data = await res.json()
    plan.value = data.plan || '未能生成教案，请重试。'
  } catch (err) {
    plan.value = '接口请求失败：' + err.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
pre {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

<template>
  <div class="p-6 max-w-xl mx-auto bg-white rounded-2xl shadow">
    <h2 class="text-2xl font-bold mb-4">🧠 智能教案生成模块</h2>

    <form @submit.prevent="generatePlan" class="space-y-4">
      <div>
        <label class="block font-medium">学科：</label>
        <input v-model="form.subject" type="text" class="w-full p-2 border rounded" placeholder="如：数学" />
      </div>

      <div>
        <label class="block font-medium">年级：</label>
        <input v-model="form.grade" type="text" class="w-full p-2 border rounded" placeholder="如：初一" />
      </div>

      <div>
        <label class="block font-medium">教学目标关键词：</label>
        <input v-model="form.keywords" type="text" class="w-full p-2 border rounded" placeholder="如：一元一次方程" />
      </div>

      <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">生成教案</button>
    </form>

    <div v-if="loading" class="mt-4 text-gray-500">生成中，请稍候...</div>

    <div v-if="plan" class="mt-6 bg-gray-50 p-4 rounded border border-gray-200">
      <h3 class="font-semibold mb-2">生成结果：</h3>
      <pre class="whitespace-pre-wrap">{{ plan }}</pre>
    </div>
  </div>
</template>