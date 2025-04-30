<script setup>
import { useRouter } from 'vue-router';
import { ref } from 'vue';

const router = useRouter();

const goToDialogue = () => {
  router.push('/dialogue');
};

const goToLogin = () => {
  router.push('/login');
};

</script>

<template>
</template>
