# Changelog

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.6.1] - 2026-10-24

### Changed
- 功能范围最终确定为两项：好友申请自动同意、群聊邀请自动同意
- 代码分支精简为两项精确匹配，其余请求直接返回
- README 功能表同步精简为上述两项

## [1.6.0] - 2026-10-24

### Changed
- 请求分支判定改为按 `request_type` 与 `sub_type` 精确匹配
- 日志 `action` 字段改为明确值：`accept_friend` / `accept_group_invite`

## [1.4.0] - 2026-10-24

### Changed
- 新增 `display_name` 字段，面板展示名改为「自动同意好友申请、群聊邀请」

## [1.3.0] - 2026-10-24

### Changed
- 群聊邀请由「自动拒绝」改为「自动同意」
- `sub_type` 按原始事件传递，不再硬编码
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