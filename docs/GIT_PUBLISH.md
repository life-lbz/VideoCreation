# GitHub 发布命令记录

目标仓库：https://github.com/345488485/text-to-video

以下为本次发布实际执行的 Git 命令，按阶段整理，相同命令重复执行时只列一次。PowerShell 的输出筛选未列入 Git 命令。未执行强制推送或删除远端历史。

## 初始检查

前两条执行时本地尚无 Git 仓库，返回相应提示。GitHub CLI `gh auth status` 也检查过，但本机未安装 gh；实际推送使用 Git Credential Manager。

```powershell
git status --short
git remote -v
git ls-remote https://github.com/345488485/text-to-video.git
git config --global user.name
git config --global user.email
git config --global credential.helper
```

## 建立仓库与检查上传内容

```powershell
git init -b main
git remote add origin https://github.com/345488485/text-to-video.git
git add --dry-run .
git ls-files --cached --others --exclude-standard -z
git ls-files --others --exclude-standard
git config --show-origin --get-all credential.helper
git ls-remote --symref origin HEAD
git fetch origin
git add .
git diff --cached --stat
git diff --cached --name-only
git check-ignore .env data/frameflow.db backups/video_project-before-vben-20261029.zip output/video-providers.png .pnpm-store frontend/node_modules frontend/apps/web-antd/dist
git config user.name 345488485
git config user.email 345488485@users.noreply.github.com
git add .gitignore tests
git diff --cached --numstat
```

## 提交、推送和核验

```powershell
git add docs/GIT_PUBLISH.md
git commit -m "feat: publish FrameFlow video agent with Vben frontend"
git push -u origin main
git rev-parse HEAD
git ls-remote origin refs/heads/main
git status --short
```

发布前运行 `python tests/scan_publish_secrets.py`，对上传候选文件检查本机 `.env` 中的密钥原文及常见令牌格式，扫描仅报告文件名，不输出密钥值。敏感配置、加密凭据、数据库、备份、日志、截图、依赖缓存和构建产物通过 `.gitignore` 排除。本机私人邮箱未用作本次提交邮箱。
