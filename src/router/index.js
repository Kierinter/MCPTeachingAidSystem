import { createRouter, createWebHistory } from "vue-router";
import Welcome from "@/component/Welcome.vue";
import Login from "@/component/Login.vue";
import Register from "@/component/Register.vue";
import Index from "@/component/Index.vue";
import Dialogue from "@/component/Dialogue.vue";
import CheckIn from "@/component/CheckIn.vue";
import PracticeProblem from "@/component/PracticeProblem.vue";
import ProblemManagement from "@/component/ProblemManagement.vue";
import StudentManagement  from "@/component/StudentManagement.vue";
import StudentCheckIn from "@/component/StudentCheckIn.vue";
import ClassWork from "@/component/ClassWork.vue";
import WrongBook from "@/component/WrongBook.vue";
import path from "path";

const routes = [
  {
    path: "/",
    name: "Welcome",
    component: Welcome,
    meta: { requiresAuth: false },
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: { requiresAuth: false },
  },
  {
    path: "/register",
    name: "Register",
    component: Register,
    meta: { requiresAuth: false },
  },
  {
    path: "/index",
    name: "Index",
    component: Index,
    meta: { requiresAuth: true },
  },
  {
    path: "/dialogue",
    name: "Dialogue",
    component: Dialogue,
    meta: { requiresAuth: true },
  },
  {
    path: "/checkin",
    name: "CheckIn",
    component: CheckIn,
    meta: { requiresAuth: true },
  },
  {
    path: "/practiceproblem",
    name: "PracticeProblem",
    component: PracticeProblem,
    meta: { requiresAuth: true },
  },
  {
    path: "/problemmanagement",
    name: "ProblemManagement",
    component: ProblemManagement,
    meta: { requiresAuth: true, requiresTeacher: true },
  },
  {
    path: "/studentmanagement",
    name: "StudentManagement",
    component: StudentManagement,
    meta: { requiresAuth: true, requiresTeacher: true },
  },
  {
    path: "/studentcheckin",
    name: "StudentCheckIn",
    component: StudentCheckIn,
    meta: { requiresAuth: true },
  },
  {
    path: "/classwork",
    name: "ClassWork",
    component: ClassWork,
    meta: { requiresAuth: true },
  },
  {
    path: "/wrongbook",
    name: "WrongBook",
    component: WrongBook,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 全局前置守卫，检查用户是否已登录及权限
router.beforeEach((to, from, next) => {
  // 获取本地存储的认证令牌和用户信息
  const authToken = localStorage.getItem("authToken");
  const userString = localStorage.getItem("user");
  const user = userString ? JSON.parse(userString) : null;
  // 如果路由需要认证且没有令牌，重定向到登录页面
  if (to.meta.requiresAuth && !authToken) {
    next({ name: "Login", query: { redirect: to.fullPath } });
  } 
  // 如果路由需要教师权限且用户不是教师，重定向到主页
  else if (to.meta.requiresTeacher && (!user || user.role !== 'teacher')) {
    next({ name: "Index" });
  }
  else {
    next();
  }
});

export default router;
