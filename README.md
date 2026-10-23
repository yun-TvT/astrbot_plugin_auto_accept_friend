# astrbot_plugin_auto_accept_friend

自动同意 QQ 好友申请、群聊邀请（AstrBot / aiocqhttp / NapCat / OneBot v11）。

插件打开即工作：收到好友申请立即通过，收到群聊邀请立即同意。零延迟、零通知、零配置、零指令。

---

## 功能

| 事件 | 处理 |
|---|---|
| 好友申请 | 立即同意（`set_friend_add_request` approve=True）|
| 群聊邀请 | 立即同意（`set_group_add_request` approve=True）|
| 群成员申请入群 | 立即同意（sub_type=add）|

插件不做任何多余的事：

- 不发送任何通知
- 不提供任何聊天指令
- 无黑白名单、无限流、无欢迎语、无延时

---

## 安装

### 方式一：AstrBot WebUI

```
面板 → 插件管理 → 安装插件 → 从 URL 安装
填入：https://github.com/houyunfei666666-hue/astrbot_plugin_auto_accept_friend
```

### 方式二：手动克隆

```bash
cd /path/to/AstrBot/data/plugins
git clone https://github.com/houyunfei666666-hue/astrbot_plugin_auto_accept_friend
docker restart astrbot
```

### 方式三：压缩包

下载 Release 中的 zip，解压到 `data/plugins/` 目录后重启容器。

---

## 依赖

无第三方依赖。仅使用 AstrBot 内置 API 与 Python 标准库（`json`、`os`、`time`）。

要求：AstrBot >= 4.0.0，Python >= 3.10。

---

## 配置

配置文件在插件目录下的 `data/config.json`，首次启动自动生成：

```json
{
  "enable": true,
  "accept_friend": true,
  "accept_group_invite": true
}
```

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `enable` | bool | `true` | 插件总开关，`false` 时忽略所有请求 |
| `accept_friend` | bool | `true` | 自动同意好友申请 |
| `accept_group_invite` | bool | `true` | 自动同意群聊邀请 |

改完配置需要重启容器生效。

### 只想要好友、不想要群

```json
{
  "enable": true,
  "accept_friend": true,
  "accept_group_invite": false
}
```

### 临时关闭

```json
{
  "enable": false,
  "accept_friend": true,
  "accept_group_invite": true
}
```

---

## 日志

运行日志（stdout，看 `docker logs`）：

```
[auto_accept_friend] loaded | enable=True accept_friend=True accept_group=True | 秒同意模式
[auto_accept_friend] 已同意好友 123456789 ok=True ret={'status': 'ok', 'retcode': 0}
[auto_accept_friend] 已同意群邀请 group=987654321 user=123456789 sub_type=invite ok=True ret={'status': 'ok', 'retcode': 0}
```

申请记录文件 `data/requests.jsonl`（每行一条 JSON）：

```json
{"ts": 1761305000.1, "action": "accept", "qq": "123456789", "comment": "我是xx", "ok": true}
{"ts": 1761305000.2, "action": "accept_group", "qq": "987654321", "group_id": "123456789", "sub_type": "invite", "comment": "", "ok": true}
```

---

## 平台支持

| 平台 | 支持 |
|---|---|
| aiocqhttp（NapCat / LLOneBot / Lagrange）| ✅ |
| Telegram | ❌ |
| Discord | ❌ |
| 企业微信 / 飞书 / 钉钉 | ❌ |

本插件依赖 OneBot v11 的 `request` 事件与 `set_friend_add_request` / `set_group_add_request` API，仅 aiocqhttp 适配器提供。

---

## 工作原理

1. AstrBot 的 aiocqhttp 适配器注册了 `@self.bot.on_request()`，把 OneBot 的 `request` 事件转成 `AstrMessageEvent`：
   - 好友申请 → `MessageType.FRIEND_MESSAGE`（即 `EventMessageType.PRIVATE_MESSAGE`）
   - 群邀请 → `MessageType.GROUP_MESSAGE`（即 `EventMessageType.GROUP_MESSAGE`）
2. 原始 OneBot 事件保存在 `event.message_obj.raw_message`，含 `post_type` / `request_type` / `sub_type` / `user_id` / `group_id` / `flag` / `comment`。
3. 插件通过 `@event_message_type(EventMessageType.ALL)` + `@platform_adapter_type(PlatformAdapterType.AIOCQHTTP)` 拦截该事件。
4. 按 `platform_id` 精确匹配适配器实例，取 `get_client()` 得到 CQHttp 客户端，调用 `call_action`。
5. 去重键：好友 `{user_id}:{flag}`，群邀请 `G:{group_id}:{user_id}:{flag}`，集合超 2000 自动清空。

---

## 安全说明

- 插件同意**所有**好友申请，包括陌生人。这是设计意图，不是缺陷。
- 插件同意**所有**群聊邀请，机器人可能被拉入任意群。这是设计意图。
- 如需过滤，修改 `main.py` 中的 `on_request` 方法，在调用 `_call_action` 前加入判断。
- 插件不上传任何数据、不含遥测、不访问外部网络。

---

## 卸载

```bash
rm -rf /path/to/AstrBot/data/plugins/astrbot_plugin_auto_accept_friend
docker restart astrbot
```

或在 WebUI 插件管理中直接删除。

---

## 常见问题

**Q：插件加载了但申请没被同意？**

依次检查：

1. `docker logs astrbot --tail 50 | grep auto_accept` 有无 `已同意好友` 日志
2. NapCat 是否已登录（`docker logs napcat --tail 20`）
3. aiocqhttp 适配器是否连接（日志找 `适配器已连接`）
4. `data/config.json` 里 `enable` 是否为 `true`
5. OneBot 实现是否支持 `set_friend_add_request` API

**Q：日志报 `找不到客户端，无法调用 set_friend_add_request`？**

`_get_client` 三级兜底都没找到可用适配器。检查 `platform_manager.platform_insts` 里是否有 aiocqhttp 实例，以及 `p.meta().id` 是否与 `event.get_platform_id()` 一致。

**Q：能不能只同意特定 QQ？**

本插件不提供该功能。可自行在 `on_request` 里加 `if user_id not in ALLOWED: return`。

---

## License

AGPL-3.0
