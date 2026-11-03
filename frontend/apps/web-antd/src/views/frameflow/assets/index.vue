<script setup lang="ts">
import { onUnmounted, ref } from 'vue';
import { Alert, Button, Card, Upload, message } from 'ant-design-vue';
const preview = ref(''),
  name = ref('');
function clear() {
  if (preview.value) URL.revokeObjectURL(preview.value);
  preview.value = '';
  name.value = '';
}
function beforeUpload(file: File) {
  if (!file.type.startsWith('image/')) {
    message.error('请选择图片文件');
    return false;
  }
  if (file.size > 10 * 1024 * 1024) {
    message.error('图片不能超过 10 MB');
    return false;
  }
  clear();
  preview.value = URL.createObjectURL(file);
  name.value = file.name;
  message.success('图片已载入当前会话');
  return false;
}
onUnmounted(clear);
</script>
<template>
  <main class="ff-page">
    <h1>品牌素材</h1>
    <p class="ff-lead">整理此刻的视觉灵感。</p>
    <Alert
      message="素材仅保存在当前浏览器会话，尚未上传云端"
      type="info"
      show-icon
    /><Card
      ><Upload.Dragger
        accept="image/*"
        :show-upload-list="false"
        :before-upload="beforeUpload"
        ><p>点击或拖拽图片到这里</p>
        <p>支持图片，单张不超过 10 MB</p></Upload.Dragger
      ><template v-if="preview"
        ><h2>{{ name }}</h2>
        <img class="ff-asset" :src="preview" :alt="name" />
        <div class="ff-actions">
          <Button @click="clear">移除素材</Button>
        </div></template
      ></Card
    >
  </main>
</template>
