"""自动同意 QQ 好友申请 + 群聊邀请（aiocqhttp / NapCat OneBot v11）—— v1.6.0

只处理两类 OneBot request 事件（依据 OneBot v11 规范）：

  1. request_type=friend
     好友申请：有人加菲比好友              → 立即同意

  2. request_type=group, sub_type=invite
     群聊邀请：有人邀请菲比进群            → 立即同意

其余请求（含 sub_type=add 加群申请）一律忽略，不做任何动作。

无指令、无通知、无延时、无黑白名单、无限流、无欢迎语。

关闭方式：
  1. AstrBot 面板 → 插件管理 → astrbot_plugin_auto_accept_friend → 禁用
  2. 把 data/config.json 里的 "enable" 改成 false，然后重启容器
插件打开即工作，不需要任何指令。
"""
import json
import os
import time
from typing import Any

from astrbot.api import logger, star
from astrbot.api.event import AstrMessageEvent
from astrbot.api.event.filter import (
    EventMessageType,
    PlatformAdapterType,
    event_message_type,
    platform_adapter_type,
)


class AutoAcceptFriend(star.Star):
    def __init__(self, context: star.Context) -> None:
        self.context = context
        base = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(base, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.cfg_path = os.path.join(self.data_dir, "config.json")
        self.log_path = os.path.join(self.data_dir, "requests.jsonl")
        self.cfg = self._load_cfg()
        self.processed: set = set()
        logger.info(
            "[auto_accept_friend] loaded | enable=%s friend=%s group_invite=%s | 秒同意模式",
            self.cfg.get("enable", True),
            self.cfg.get("accept_friend", True),
            self.cfg.get("accept_group_invite", True),
        )

    # ---------------- 配置 ----------------
    def _default_cfg(self) -> dict:
        return {
            "enable": True,
            "accept_friend": True,
            "accept_group_invite": True,
        }

    def _load_cfg(self) -> dict:
        cfg = self._default_cfg()
        try:
            if os.path.exists(self.cfg_path):
                with open(self.cfg_path, encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    # 兼容 v1.1.x 旧键名：reject_group_invite=true → accept_group_invite=false
                    if "reject_group_invite" in loaded and "accept_group_invite" not in loaded:
                        loaded["accept_group_invite"] = not bool(
                            loaded.pop("reject_group_invite")
                        )
                    # 丢弃已废弃的加群申请开关（v1.5.0 短暂存在过）
                    loaded.pop("accept_group_join_request", None)
                    cfg.update(loaded)
            with open(self.cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[auto_accept_friend] 配置读写失败: {e}")
        return cfg

    # ---------------- 工具 ----------------
    def _append_log(self, record: dict) -> None:
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"[auto_accept_friend] 写日志失败: {e}")

    def _raw(self, event: AstrMessageEvent) -> Any:
        try:
            return event.message_obj.raw_message
        except Exception:
            return None

    def _get_client(self, event: AstrMessageEvent) -> Any:
        """按 platform_id 精确匹配适配器，取 aiocqhttp 的 CQHttp 客户端"""
        want_id = ""
        try:
            want_id = event.get_platform_id()
        except Exception:
            want_id = ""
        want_name = ""
        try:
            want_name = event.get_platform_name()
        except Exception:
            want_name = ""
        try:
            insts = self.context.platform_manager.platform_insts
        except Exception:
            insts = []
        for p in insts:
            try:
                if want_id and p.meta().id == want_id and hasattr(p, "get_client"):
                    return p.get_client()
            except Exception:
                continue
        for p in insts:
            try:
                if want_name and p.meta().name == want_name and hasattr(p, "get_client"):
                    return p.get_client()
            except Exception:
                continue
        for p in insts:
            try:
                if hasattr(p, "get_client"):
                    return p.get_client()
            except Exception:
                continue
        return None

    async def _call_action(
        self, event: AstrMessageEvent, action: str, **params: Any
    ) -> Any:
        client = self._get_client(event)
        if client is None:
            logger.error(f"[auto_accept_friend] 找不到客户端，无法调用 {action}")
            return None
        try:
            return await client.call_action(action, **params)
        except Exception as e:
            logger.error(f"[auto_accept_friend] 调用 {action} 失败: {e}")
            return None

    def _dedup(self, key: str) -> bool:
        """返回 True 表示已处理过（应跳过）"""
        if key in self.processed:
            return True
        self.processed.add(key)
        if len(self.processed) > 2000:
            self.processed.clear()
        return False

    def _ok(self, ret: Any) -> bool:
        return not (isinstance(ret, dict) and str(ret.get("status")) == "failed")

    # ---------------- 主处理 ----------------
    @platform_adapter_type(PlatformAdapterType.AIOCQHTTP)
    @event_message_type(EventMessageType.ALL)
    async def on_request(self, event: AstrMessageEvent):
        raw = self._raw(event)
        if raw is None:
            return
        try:
            if str(raw.get("post_type", "")) != "request":
                return
        except Exception:
            return

        try:
            request_type = str(raw.get("request_type", "") or "")
            sub_type = str(raw.get("sub_type", "") or "")
            user_id = str(raw.get("user_id", "") or "")
            group_id = str(raw.get("group_id", "") or "")
            comment = str(raw.get("comment", "") or "")
            flag = str(raw.get("flag", "") or "")
        except Exception:
            return

        if not flag:
            return

        # ======== 分支 A：好友申请（request_type=friend，无 group_id）========
        if request_type == "friend":
            if not self.cfg.get("enable", True):
                logger.info(
                    f"[auto_accept_friend] 开关关闭，忽略好友申请 user={user_id}"
                )
                return
            if not self.cfg.get("accept_friend", True):
                logger.info(f"[auto_accept_friend] 好友同意已关闭，忽略 {user_id}")
                return
            if self._dedup(f"{user_id}:{flag}"):
                return

            ret = await self._call_action(
                event, "set_friend_add_request", flag=flag, approve=True
            )
            ok = self._ok(ret)
            logger.info(
                f"[auto_accept_friend] 已同意好友 {user_id} ok={ok} ret={ret}"
            )
            self._append_log(
                {
                    "ts": time.time(),
                    "action": "accept_friend",
                    "qq": user_id,
                    "comment": comment,
                    "ok": ok,
                }
            )
            return

        # ======== 分支 B：群邀请（request_type=group, sub_type=invite）========
        if request_type == "group" and sub_type == "invite":
            if not self.cfg.get("enable", True):
                logger.info(
                    f"[auto_accept_friend] 开关关闭，忽略群邀请 "
                    f"group={group_id} user={user_id}"
                )
                return
            if not self.cfg.get("accept_group_invite", True):
                logger.info(
                    f"[auto_accept_friend] 群邀请同意已关闭，忽略 "
                    f"group={group_id} user={user_id}"
                )
                return
            if self._dedup(f"G:{group_id}:{user_id}:{flag}"):
                return

            ret = await self._call_action(
                event,
                "set_group_add_request",
                flag=flag,
                approve=True,
                sub_type="invite",
            )
            ok = self._ok(ret)
            logger.info(
                f"[auto_accept_friend] 已同意群邀请 group={group_id} "
                f"user={user_id} ok={ok} ret={ret}"
            )
            self._append_log(
                {
                    "ts": time.time(),
                    "action": "accept_group_invite",
                    "qq": user_id,
                    "group_id": group_id,
                    "sub_type": "invite",
                    "comment": comment,
                    "ok": ok,
                }
            )
            return

        # ======== 其余请求（含 sub_type=add 加群申请）一律忽略 ========
        logger.debug(
            f"[auto_accept_friend] 忽略未处理的请求 "
            f"request_type={request_type!r} sub_type={sub_type!r} "
            f"user={user_id} group={group_id}"
        )
        return