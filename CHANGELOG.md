# Changelog

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.6.0] - 2026-10-24

### Removed
- **删除「加群申请自动同意」功能**（`sub_type=add` 分支整段移除）
- 删除配置项 `accept_group_join_request`

### Changed
- 分支判定重写为严格匹配 `request_type` + `sub_type`：
  ```python
  if request_type == "friend":                           # 好友申请
  elif request_type == "group" and sub_type == "invite":  # 群邀请
  else: return                                            # 其余一律忽略
  ```
- 修复 v1.4.0 的逻辑缺陷：原 `is_friend = ... or sub_type == "add"` 会把加群申请误判为好友申请，导致调用错误的 OneBot API
- 日志中 `action` 字段改为明确值：`accept_friend` / `accept_group_invite`

### Scope
本插件只处理两类请求：
1. 有人加机器人好友 → 立即同意
2. 有人邀请机器人进群 → 立即同意

其他请求（包括他人申请进入机器人管理的群）**一律忽略**。

## [1.5.0] - 2026-10-24

### Added
- 加群申请分支（`sub_type=add`）与 `accept_group_join_request` 开关（默认关闭）

### Fixed
- 修复 `sub_type=add` 被误判为好友申请的问题

## [1.4.0] - 2026-10-24

### Changed
- 新增 `display_name` 字段，面板展示名改为「自动同意好友申请、群聊邀请」

## [1.3.0] - 2026-10-24

### Changed
- **群聊邀请由「自动拒绝」改为「自动同意」**
- `sub_type` 改为按原始事件智能传递（`invite` 邀请入群 / `add` 申请入群），不再硬编码
- 群邀请去重键独立为 `G:{group_id}:{user_id}:{flag}`
- 群邀请日志新增 `group_id` 字段

### Config
- `reject_group_invite` → `accept_group_invite`（旧键名自动兼容转换）
- 新增 `accept_friend` 独立开关

## [1.2.0] - 2026-10-24

### Changed
- 描述精简

## [1.1.0] - 2026-10-24

### Removed
- 移除全部管理指令（`/fr status|on|off|log|clear`）
- 移除管理员通知（`_notify` 方法）
- 移除黑白名单（`whitelist` / `blacklist` / `whitelist_mode`）
- 移除每小时限流（`max_per_hour` / `_rate_ok`）
- 移除同意延时（`delay_seconds`）
- 移除欢迎语（`reply_on_accept`）

### Changed
- 改为极简模式：收到申请立即同意，零延迟、零通知

## [1.0.0] - 2026-10-24

### Added
- 自动同意 QQ 好友申请
- 自动拒绝群聊邀请
- 黑名单永久拒绝
- 白名单模式
- 管理员私聊通知
- JSONL 申请日志
- 每小时限流（默认 30 条）
- 管理指令 `/fr status|on|off|log|clear`
- 去重机制（集合上限 2000）
- 平台适配器三级兜底匹配