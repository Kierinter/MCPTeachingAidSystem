import { RouterView } from "vue-router";

// 添加全局样式，确保页面铺满屏幕
<template>
  <RouterView></RouterView>
</template>

<style>
html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
}

#app {
  height: 100%;
}
</style>
