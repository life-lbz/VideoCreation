<script setup lang="ts">
import type { Work } from '#/api/frameflow/contracts';
import { Button, Card, Popconfirm } from 'ant-design-vue';
defineProps<{ work: Work; deleting?: boolean }>();
defineEmits<{ remove: [id: string] }>();
</script>
<template>
  <Card class="ff-work"
    ><video :src="work.resultUrl" controls preload="metadata" playsinline />
    <h3>{{ work.title }}</h3>
    <p>
      {{ work.ratio }} · {{ work.duration }} 秒 · {{ work.resolution }} · 已完成
    </p>
    <p>{{ new Date(work.createdAt).toLocaleString() }}</p>
    <div class="ff-actions">
      <Button :href="work.resultUrl" download>下载视频</Button
      ><Popconfirm
        title="确认删除这项作品？"
        ok-text="删除"
        cancel-text="保留"
        @confirm="$emit('remove', work.id)"
        ><Button danger :loading="deleting">删除</Button></Popconfirm
      >
    </div></Card
  >
</template>
