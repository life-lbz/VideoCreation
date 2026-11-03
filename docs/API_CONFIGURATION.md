# 火山方舟 API 配置

项目已经预置火山方舟官方地址和 Seedance 2.0 模型。你只需要配置一个 API Key。

## 1. 获取 API Key

打开火山方舟控制台：

<https://console.volcengine.com/ark/region:ark+cn-beijing/apikey>

创建并复制“方舟 API Key”。这里需要的是方舟 API Key，不是 Access Key / Secret Key。

账号需要先开通视频生成模型服务，并确保有可用余额或套餐额度。

## 2. 填写项目配置

打开项目根目录的 `.env` 文件：

```dotenv
ARK_API_KEY=在这里粘贴你的方舟APIKey
```

不要添加引号，不要在等号两侧加空格。其余配置已经完成，不需要修改。

项目预置值：

```dotenv
VIDEO_PROVIDER=auto
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL_ID=doubao-seedance-2-0-260128
ARK_FAST_MODEL_ID=doubao-seedance-2-0-fast-260128
ARK_WATERMARK=true
```

`VIDEO_PROVIDER=auto` 表示：

- `ARK_API_KEY` 有值时，自动调用真实火山方舟 Seedance API。
- `ARK_API_KEY` 留空时，自动使用本地 Mock，不产生真实模型费用。

## 3. 启动

```bash
conda activate video_creation
python run.py
```

浏览器打开：

<http://127.0.0.1:4173>

## 4. 检查是否生效

打开：

<http://127.0.0.1:4173/api/health>

配置成功时会返回：

```json
{
  "status": "ok",
  "provider": "volcengine_ark",
  "runtime": "python"
}
```

如果 `provider` 是 `mock`，说明 `.env` 中的 `ARK_API_KEY` 仍为空，或者服务没有在修改配置后重启。

## 安全提醒

- `.env` 已被 `.gitignore` 排除，不要把 API Key 写进前端、README 或提交到 Git。
- API Key 泄露后应立即在火山方舟控制台删除并重新创建。
- 调用真实视频生成接口会产生费用，建议先在控制台设置预算和告警。

# 网页配置多个视频平台

打开 `http://127.0.0.1:4173/settings/video-providers`，选择平台，填写 API Key，点击“保存密钥”，再点击“设为默认”。接口地址由服务端固定，无需手工填写；密钥加密保存在当前 Windows 用户的服务端配置中，不回传明文。

支持火山方舟（北京）、通义万相（北京）、Runway、Luma。密钥必须属于对应平台和区域。通义万相 2.6 固定生成声音；其他参数会在创作页按平台能力调整。

“测试连接”只调用只读接口，不提交视频任务。测试通过不代表模型权限或余额充足。完整接口与部署说明见 [VIDEO_PROVIDERS.md](VIDEO_PROVIDERS.md)。

