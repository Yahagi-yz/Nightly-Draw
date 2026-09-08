# 每日抽卡 · Nightly Draw

> 每天的睡前小故事。每晚十点，在故事、人物与城市之间，遇见世界的一小块。

**仓库已由用户创建；这里是项目初始化基础，不是已上线 App。每天 22:00 的自动推送仍未开启。**

仓库：`Yahagi-yz/Nightly-Draw`（当前公开，默认分支 `main`）。项目主线：[Issue #1](https://github.com/Yahagi-yz/Nightly-Draw/issues/1)。

## 已确认的方向

| 项目 | 要求 |
|---|---|
| 时间 | 每天北京时间 22:00，`Asia/Shanghai`，不随设备时区改变 |
| 行为 | 主动提供当次完整内容，而不是提醒用户回复“抽卡” |
| 卡池 | 世界故事、人物经历、历史名城；不必原创，不限奇幻 |
| 表达 | 适合睡前，温和而有好奇心，不局限于儿童童话 |
| 关联 | 每次独立可读；允许人物、地点或主题松散关联 |
| 形式 | 文字、图片或图文均可；具体生产比例尚未确定 |
| 远期 | 积累可复用内容与产品基础，逐步发展为 App |

## 本仓库有什么

`MISSION.md` 记录目标；`CONTEXT.md` 区分已确认需求、事实与待决策事项；`ROADMAP.md` 给出候选路线；`AGENTS.md` 提供后续 Agent 交接入口。`docs/` 记录内容规范、交付边界和验收条件。`schemas/card.schema.json` 与 `content/cards/` 提供卡片数据契约和三张结构样例。`preview.html` 是可直接打开的单文件样卡预览；`prompts/chatgpt-nightly-task.txt` 是自包含的任务指令。

## 当前状态

- 仓库及真实主线 Issue 已建立；初始化前的 README 与原始提交保留在 Git 历史中。
- 本仓库包含目标、规范、3 张带出处的文字样卡、预览、数据校验及测试。
- 定时任务、设备推送、持续生产卡池、App 部署均未完成。
- 当前公开性沿用用户创建仓库时的设置；没有因此选定开源许可证，也没有授权第三方素材的复用。
- 技术栈、长期推送渠道、图片来源、预算与产品运营方式尚未锁定。

## 本地检查与预览

使用 Python 3.8 或更新版本；日常校验仅需标准库。

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
```

直接用浏览器打开 `preview.html`，可切换世界故事、人物故事与历史名城样卡并查看来源。页面没有后台调度或发送功能。

`scripts/bootstrap_github.py` 是初始包保留的建仓辅助脚本。**本仓库已经存在，不要再对本项目运行 `--apply`；已有仓库的维护使用正常 Git 流程。** 不带参数仅预演，不联网、不建仓、不推送。

## 定时推送

期望配置保存于 `config/schedule.json`；当前仍为 `enabled=false`，没有真实任务 ID。当前会话未提供可创建定时内容推送的工具；相关阻塞记录在 Issue #1 和 `docs/DELIVERY.md`。

**创建仓库、上传文件或保存 cron 表达式，都不等于开启自动推送。** 只有实际调度服务返回创建成功，才能记录任务 ID、启用状态与下一次运行时间；设备接收还需要独立验证。

## 开发入口

先读 `MISSION.md` → `CONTEXT.md` → `docs/CONTENT_STANDARD.md` → `docs/DELIVERY.md`。不要把初始化基础报告为线上能力，不得把示例卡池说成可持续生产卡池。来源登记见 `docs/SOURCE_REGISTER.md`。
