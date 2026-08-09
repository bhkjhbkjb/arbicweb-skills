# arbicweb-skills · 阿拉伯语研究舱配套 Skills

> 3 个 skill：词库导入 / 句卡生成 / 服务器部署。

「阿拉伯语研究舱（arbicweb）」应用的配套 WorkBuddy skills：把原始阿语教材/词表/截图转成规范词库、生成带逐词拆解的例句句卡、以及把站点部署到云服务器并验证。

## 📦 包含的 Skills

### `arabic-vocab-ingest`
将原始阿语词汇材料（PDF 教材、xlsx 词表、纯文本词表、截图）转成研究舱 word_libraries.js 中的规范词库，含注音(tashkeel)与中文词性标注。

### `arabic-sentence-card`
为研究舱撰写阿拉伯语句卡（例句/句卡）并追加到 data.js，含逐词拆解(POS 着色)、句法说明与三字母词根派生。

### `arbicweb-deploy`
把 arbicweb（阿拉伯语研究舱）更新部署到云服务器并验证（部署目标地址请在本地配置，本仓库不含真实地址）。



## 🚀 安装与使用

这些 skills 面向 [WorkBuddy](https://www.codebuddy.cn) 的 skill 体系（亦兼容 Claude Code / Codex 等同类 skill 目录）。

```bash
git clone https://github.com/bhkjhbkjb/arbicweb-skills.git
# 把需要的 skill 文件夹复制到你的 skills 目录
cp -r arbicweb-skills/<skill-name> ~/.workbuddy/skills/
```

在 WorkBuddy 中直接以 skill 名称触发即可（如输入 `/<skill-name>` 或自然语言描述）。

## 📂 目录结构

```
arbicweb-skills/
├── arabic-vocab-ingest/   (SKILL.md + references/ + scripts/)
├── arabic-sentence-card/ (SKILL.md + references/ + scripts/)
└── arbicweb-deploy/      (SKILL.md)
```

## 🔒 安全说明

本仓库已去除敏感信息（服务器 IP、API 密钥、内部地址等），相关位置以占位符（如 `<DEPLOY_SERVER_IP>`、`<MOMENT_RESEARCH_HOST>`）标注，请按你自己的运行环境替换。

---

*由 **Hreed** 维护 · 欢迎 Star / 提 Issue*
