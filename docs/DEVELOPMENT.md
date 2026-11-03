# 开发说明

## 当前阶段

当前版本采用 Vben Admin 5.7 前端和 Python FastAPI 后端，包含：

- 三套可切换主题的响应式创作工作台。
- 提示词润色、参数选择和费用预估。
- 创建、查询、取消视频任务的 HTTP API。
- 具备幂等逻辑的 Mock 异步视频供应商。
- 火山方舟 Seedance 2.0 真实供应商适配器和自动路由。
- 本地演示视频、任务进度、额度结算和结果下载。

## 本地运行

### Vben 前端开发

前端位于 `frontend/apps/web-antd`，采用官方 Vben Admin 5、Vue 3、TypeScript 和 Ant Design Vue。

在 `frontend/` 执行 `pnpm install` 安装依赖，再执行 `pnpm run dev:antd`。同时在项目根目录执行 `python run.py` 启动 Python 服务。Vite 将 `/api` 请求代理到 `http://127.0.0.1:4173`，开发页面地址以 Vite 终端输出为准。

生产部署前，在 `frontend/` 执行 `pnpm run build:antd`。Python 会优先托管 `frontend/apps/web-antd/dist`；没有构建时回退到原 `public/` 前端。也可以用 `FRAMEFLOW_FRONTEND_DIR` 指定构建目录。

迁移前备份位于 `backups/video_project-before-vben-20261029.zip`，包含私密配置，应仅在本地保存。

Vben 5.7.0 官方工程通过 `packageManager` 固定使用 pnpm 10.33.4；保留该版本和原 lockfile，主机的 pnpm 会自动选择工程版本。

前端验证命令（在 `frontend/` 执行）：

```powershell
pnpm --filter @vben/web-antd typecheck
pnpm exec vitest run --config apps/web-antd/vitest.frameflow.config.ts
pnpm run build:antd
```

浏览器验收可启动 `python tests/run_mock_server.py`，使用 4174 端口和独立的 `output/vben-smoke.db`，不会调用付费视频 API。

Python 端使用 conda 环境 `video_creation`（Python 3.11），前端依赖仍由 pnpm 管理。

```bash
conda activate video_creation
python run.py
```

打开 `http://127.0.0.1:4173`。

如果本机已经安装 FastAPI 与 Uvicorn，也可以直接运行：

```bash
python run.py
```

开发时启用自动重载：

```bash
conda activate video_creation
python -m uvicorn backend.main:app --host 127.0.0.1 --port 4173 --reload
```

检查与测试：

```bash
conda activate video_creation
python -m compileall -q backend tests run.py
python -m unittest discover -s tests -v
```

## 接入真实模型

火山方舟地址、模型 ID、创建/查询/取消接口与状态映射已经完成。只需在 `.env` 中填写 `ARK_API_KEY`，具体步骤见 [`API_CONFIGURATION.md`](API_CONFIGURATION.md)。

任务、作品和额度已保存在 SQLite。正式多用户商用部署仍需身份认证、用户隔离、支付对账、独立任务 Worker 和对象存储。产品和工程边界详见根目录 `README.md`。
