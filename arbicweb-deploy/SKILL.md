---
name: arbicweb-deploy
description: 把 arbicweb（阿拉伯语研究舱）更新部署到腾讯云轻量服务器 <DEPLOY_SERVER_IP> 并验证。当用户要求"上线/部署/更新网站到服务器"时使用。
agent_created: true
---

# arbicweb 部署技能

## 服务器事实（2026-07-25 确认）

- IP：`<DEPLOY_SERVER_IP>`（腾讯云轻量，上海，Ubuntu 24.04）
- SSH：`ssh -i ~/.ssh/id_arbicweb_deploy root@<DEPLOY_SERVER_IP>`（免密已配置；若失效，让用户在 OrcaTerm 网页终端把新公钥追加到 `/root/.ssh/authorized_keys`）
- 项目目录：`/opt/arbicweb`（不是旧文档里的 /www/wwwroot/...）
- 架构：nginx(80/443) → 127.0.0.1:8123，python 服务静态文件+API 全包（SimpleHTTPRequestHandler 子类，cwd=/opt/arbicweb）
- 服务：`systemctl restart dreamhalidearabic-activation`（已 enable 开机自启）
- 环境变量：`/etc/default/dreamhalidearabic-activation`（ADMIN_KEY、SMTP、DEEPSEEK_*；改后必须 restart）
- 数据库：`/opt/arbicweb/activation-state.db` —— **绝不可用本地文件覆盖**，含全部用户激活/账户/点数流水

## 部署步骤（一键脚本）

推荐使用项目根目录的 `deploy.py` 一键部署：
```bash
python deploy.py
```
脚本自动完成：检查/生成 SSH 密钥 → 打包 → 上传 → 备份数据库 → 解压 → 重启服务 → 验证。

## 部署步骤（手动）

1. 本地打包（在项目根 E:\aiproject\arbicweb 执行）：
   ```bash
   tar -czf /tmp/site-update-$(date +%Y%m%d).tar.gz \
     index.html app.html admin.html data.js word_libraries.js \
     activation_server.py activation_admin.py backup_activation_db.py install_backup_cron.sh \
     deploy design assets/audio/sentences assets/audio/v2 assets/audio/words assets/fonts assets/vendor
   ```
   排除：activation-state.db、activation-codes-*.txt、activation-code-hashes.js、node_modules、tmp_*、*.bak、material_uploads、output。
2. 服务器先备份再动：
   ```bash
   mkdir -p /root/arbicweb-backups/$(date +%Y%m%d) && cp -a /opt/arbicweb/activation-state.db <备份目录>/
   ```
3. scp 上传 tar.gz 到服务器 /tmp，两端 md5sum 比对一致。
4. 服务器解压：`cd /opt/arbicweb && tar -xzf /tmp/<包>`，然后 `python3 -m py_compile activation_server.py` 验证语法，md5sum 确认 db 未变。
5. 若端口 8123 被非 systemd 的旧进程占用（`ss -tlnp | grep 8123`），先 kill 再 `systemctl restart dreamhalidearabic-activation`。
6. 验证清单（全过才算完成）：
   - `curl -sI https://dreamhalidearabic.site/` → 200
   - `curl -s https://dreamhalidearabic.site/design/v2/index.html` → 有 HTML
   - `POST /api/session` → 返回 JSON（SESSION_MISSING 属正常）
   - `POST /api/activate` 用假码 → 应返回 JSON `CODE_NOT_FOUND`（HTTP 404 是设计行为，不是故障；只要 body 是 JSON 就正常）
   - `GET /assets/audio/sentences/0001.mp3` → 200 audio/mpeg
   - `GET /admin.html` → 200
   - `POST /api/admin/status` 无密钥 → 应被拒绝
7. 清理服务器 /tmp 里的包；报告备份位置。

## 坑

- 孤儿进程：2026-07 曾有人手动 nohup 跑旧服务占住 8123，导致 systemd 服务 bind 失败假死。重启前先确认 8123 的属主进程是 systemd 拉起的。
- v2/manifest.json 为空 `{}` 是内容现状不是 bug：句子音频走 data.js 的 audio 字段（assets/audio/sentences/），词音频走 words/manifest.json；manifest 查不到时前端回退 Web Speech TTS。
- Windows Git Bash 下 `curl -o /dev/null -w '%{size_download}'` 可能显示 0 bytes（exit 23），是本地怪癖，以 HTTP 状态码 + `| head -c` 看 body 为准。
- 管理后台教程：deploy/管理后台与服务器运维教程.md（教用户时引用它，别重写）。
- **AI 解析不稳定修复（2026-07-25）**：`call_deepseek_analysis` 增加了对 HTTP 429/5xx 和 JSON 解析失败的重试（指数退避），默认超时从 90→120 秒，默认重试次数从 1→2（一共 3 次尝试）。修复前 DeepSeek 返回限流/服务端错误时不会重试直接报错，这是用户反馈"有时跑不通"的主因。
- **nginx proxy_read_timeout 注意**：AI 重试后最坏情况可能耗时 3×120+退避≈370 秒。如果服务器 nginx 的 `proxy_read_timeout` 仍是 120s，AI 重试期间可能被 nginx 断开返回 504。建议在服务器 nginx 的 `/api/ai/analyze` location 单独设置 `proxy_read_timeout 300s;`（或把整个 /api/ 的 timeout 提上去）。
