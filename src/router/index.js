import { createRouter, createWebHistory } from "vue-router";
import Welcome from "../components/Welcome.vue";
import Dialogue from "../components/Dialogue.vue";
import Login from "../components/Login.vue";
import Information from "../components/Information.vue";
import Register from "../components/Register.vue";
import Index from "../components/Index.vue";
import CheckIn from "@/components/CheckIn.vue";
import PracticeProblem from "@/components/PracticeProblem.vue";
import path from "path";

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
    path: "/checkin",
    name: "CheckIn",
    component: CheckIn,
  },
  {
    path: "/practiceproblem",
    name: "PracticeProblem",
    component: PracticeProblem,
  },
  {
    path: "/index",
    name: "Index",
    component: Index,
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
