"""
回音 (Huíyīn) - 启动入口
一个会主动找你说话的 AI 陪伴体
"""

import sys
import time
from datetime import datetime

from loguru import logger

from config.settings import settings
from core.models import Message, Role, FutureTask, GenerationMode
from core.engine.dual_track import DualTrackEngine
from core.engine.memory import MemoryEngine
from core.engine.scheduler import Scheduler


def create_llm():
    """根据配置创建对应的 LLM 适配器"""
    provider = settings.LLM_PROVIDER
    if provider == "deepseek":
        from core.llm.deepseek import DeepSeekAdapter
        return DeepSeekAdapter()
    elif provider == "gemini":
        from core.llm.gemini import GeminiAdapter
        return GeminiAdapter()
    elif provider == "mimo":
        from core.llm.mimo import MimoAdapter
        return MimoAdapter(
            api_key=settings.MIMO_API_KEY,
            base_url=settings.MIMO_BASE_URL,
            model_name=settings.MIMO_MODEL
        )
    elif provider == "openai_compat":
        from core.llm.openai_compat import OpenAICompatAdapter
        return OpenAICompatAdapter(
            api_key=settings.OPENAI_COMPAT_API_KEY,
            base_url=settings.OPENAI_COMPAT_BASE_URL,
            model_name=settings.OPENAI_COMPAT_MODEL
        )
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")


def create_channel():
    """根据配置创建对应的消息通道"""
    ch = settings.CHANNEL
    if ch == "cli":
        from channels.cli import CLIChannel
        return CLIChannel()
    # Phase 1 增加:
    # elif ch == "wechat": ...
    # Phase 3 增加:
    # elif ch == "telegram": ...
    else:
        raise ValueError(f"不支持的通道: {ch}")


def main():
    # 配置日志
    logger.remove()
    logger.add(sys.stderr, level=settings.LOG_LEVEL)
    logger.add(settings.DATA_DIR / "huiyin.log", rotation="10 MB", level="DEBUG")

    # 验证配置
    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        print(f"\n❌ 配置错误: {e}")
        print("请复制 .env.example 为 .env 并填入你的 API Key\n")
        sys.exit(1)

    # 初始化组件
    llm = create_llm()
    engine = DualTrackEngine(llm=llm)
    memory = MemoryEngine()
    channel = create_channel()

    def handle_future_task(task: FutureTask):
        """当调度器触发未来任务时执行"""
        logger.info(f"⏰ 异步任务触发! 模式: {task.generation_mode.value}")
        
        new_future_task = None
        
        if task.generation_mode == GenerationMode.PRE_GENERATED and task.content:
            # 预生成的直接发送
            channel.send_split(task.content.messages, task.content.delays)
            reply_text = " ".join(task.content.messages)
            memory.add(Message(role=Role.AI, content=reply_text))
            
        elif task.generation_mode == GenerationMode.DEFERRED:
            # 延迟生成的，重新带上 task.reason 去问 LLM
            context = memory.get_context()
            profile = memory.get_user_profile_summary()
            try:
                response = engine.process_deferred(
                    messages=context,
                    task_reason=task.reason,
                    user_profile=profile
                )
                if response.reply.strip() and "[空]" not in response.reply:
                    if response.is_split and response.split_messages:
                        channel.send_split(response.split_messages, response.split_delays)
                        reply_text = " ".join(response.split_messages)
                    else:
                        channel.send(response.reply)
                        reply_text = response.reply
                    memory.add(Message(role=Role.AI, content=reply_text))
                
                # 提取大模型生成的新任务
                if response.future_task:
                    new_future_task = response.future_task
                    
            except Exception as e:
                logger.error(f"未来轨 LLM 调用失败: {e}")

        # === 无限循环托底机制 ===
        # 如果当前任务处理完没有产生新的主动任务（例如大模型漏了，或者是 pre_generated），
        # 强制塞入一个保底任务，确保无限循环不断链。
        if engine.enable_proactive:
            if new_future_task:
                scheduler.add_task(new_future_task)
                logger.debug(f"未来任务已接力: {new_future_task.trigger_time}")
            else:
                from datetime import timedelta, timezone
                fallback_time = datetime.now(timezone.utc) + timedelta(minutes=2)
                fallback_task = FutureTask(
                    trigger_time=fallback_time,
                    generation_mode=GenerationMode.DEFERRED,
                    reason="用户没有回复，继续找话题戳他"
                )
                scheduler.add_task(fallback_task)
                local_time_str = fallback_task.trigger_time.astimezone().strftime('%Y-%m-%d %H:%M:%S')
                logger.debug(f"已启动兜底未来任务接力: {local_time_str} (本地时间)")

    scheduler = Scheduler(on_trigger=handle_future_task)
    scheduler.start()

    logger.info(f"回音启动 | LLM: {settings.LLM_PROVIDER} | 通道: {settings.CHANNEL}")

    def handle_message(msg: Message):
        """收到用户消息时的处理逻辑"""
        # 记录用户消息
        memory.add(msg)
        logger.info(f"用户: {msg.content}")

        # 获取对话上下文
        context = memory.get_context()
        profile = memory.get_user_profile_summary()

        # 调用双轨引擎
        try:
            response = engine.process(
                messages=context,
                user_profile=profile,
            )
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            channel.send("...我刚才走神了，你再说一遍？")
            return

        # 模拟回复延迟
        delay = max(0.3, response.delay_seconds)
        time.sleep(delay)

        # 发送回复
        if response.is_split and response.split_messages and response.split_delays:
            channel.send_split(response.split_messages, response.split_delays)
            reply_text = " ".join(response.split_messages)
        else:
            channel.send(response.reply)
            reply_text = response.reply

        # 记录 AI 回复
        ai_msg = Message(role=Role.AI, content=reply_text, timestamp=datetime.now())
        memory.add(ai_msg)

        # 如果开启了主动功能
        if engine.enable_proactive:
            if response.future_task:
                scheduler.add_task(response.future_task)
                logger.debug(f"未来任务已入队: {response.future_task.trigger_time}")
            else:
                # 解析失败或者大模型故意返回 null（比如用户说别烦我）
                # 必须清理旧任务，防止上一个定时任务像个幽灵一样在错误的时间触发！
                scheduler.remove_task()

    # 注册回调 & 启动
    channel.on_receive(handle_message)
    channel.start()

    # 阻塞主线程
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("回音关闭")
        channel.stop()
        scheduler.stop()


if __name__ == "__main__":
    main()
