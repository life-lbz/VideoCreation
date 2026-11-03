<script setup lang="ts">
import { Button, Card } from 'ant-design-vue';
import { useRouter } from 'vue-router';
const router = useRouter();
const templates = [
  {
    title: '城市漫游',
    category: '旅行',
    prompt: '清晨的江南小巷，镜头缓慢前行，晨光穿过薄雾，青石板上倒映着屋檐',
  },
  {
    title: '品牌故事',
    category: '商业',
    prompt:
      '一瓶香水放在黑色大理石台面上，柔和侧光，镜头缓慢环绕，呈现精致质感',
  },
  {
    title: '自然诗意',
    category: '生活',
    prompt: '山间云雾缓慢流动，阳光穿过树林，溪水泛起微光，电影感航拍镜头',
  },
];
</script>
<template>
  <main class="ff-page">
    <h1>灵感模板</h1>
    <p class="ff-lead">从一段描述出发，创造你的专属画面。</p>
    <div class="ff-grid">
      <Card v-for="t in templates" :key="t.title" :title="t.title"
        ><p>{{ t.category }}</p>
        <p>{{ t.prompt }}</p>
        <div class="ff-actions">
          <Button
            type="primary"
            @click="
              router.push({ path: '/studio', query: { prompt: t.prompt } })
            "
            >使用模板</Button
          >
        </div></Card
      >
    </div>
  </main>
</template>
