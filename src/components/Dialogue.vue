<script setup>
// 组件逻辑部分
</script>

<template>
  <div>
    <header>物理作业生成</header>

    <div class="chat-container">
      <div class="message user">我需要生成今天的物理作业</div>
      <div class="message ai">请上传今日教学进度、需要考察的知识点以及生成的题量。</div>
    </div>

    <div class="input-area">
      <input type="text" placeholder="请输入..." />
      <input type="file" id="fileUpload" style="display: none;" />
      <button @click="document.getElementById('fileUpload').click()">📎 上传文件</button>
      <button>发送</button>
    </div>
  </div>
</template>

<style scoped>
body {
  margin: 0;
  font-family: Arial, sans-serif;
  background: #f1f5f9;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

header {
  background-color: #1e3a8a;
  color: white;
  padding: 16px;
  text-align: center;
  font-size: 20px;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  max-width: 1000px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.5;
}

.user {
  align-self: flex-end;
  background-color: #3b82f6;
  color: white;
}

.ai {
  align-self: flex-start;
  background-color: #e2e8f0;
  color: #111827;
}

.input-area {
  display: flex;
  padding: 16px;
  background-color: white;
  border-top: 1px solid #ccc;
  max-width: 1000px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.input-area input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 8px;
  margin-right: 10px;
}

.input-area button {
  padding: 10px 14px;
  background-color: #1e40af;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-left: 8px;
}

.input-area button:hover {
  background-color: #1e3a8a;
}
</style> 