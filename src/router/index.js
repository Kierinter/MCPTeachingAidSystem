import { createRouter, createWebHistory } from "vue-router";
import Welcome from "../components/Welcome.vue";
import Dialogue from "../components/Dialogue.vue";
import Login from "../components/Login.vue";
import Information from "../components/Information.vue";
import Register from "../components/Register.vue";
import Index from "../components/Index.vue";
import Demo from "../components/demo.vue";

const routes = [
  {
    path: "/",
    name: "Welcome",
    component: Welcome,
  },
  {
    path: "/dialogue",
    name: "Dialogue",
    component: Dialogue,
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
  },
  {
    path: "/register",
    name: "Register",
    component: Register,
  },
  {
    path: "/information",
    name: "Information",
    component: Information,
  },
  {
    path: "/index",
    name: "Index",
    component: Index,
  },
  {
    path: "/demo",
    name: "Demo",
    component: Demo,
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
