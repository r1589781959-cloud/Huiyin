"""
回音 - 调度决策引擎
管理未来任务队列，负责主动消息的触发。
Phase 1 实现：使用 APScheduler 处理异步任务。
"""

from typing import Callable, Any

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from core.models import FutureTask


class Scheduler:
    """
    调度器：接入 APScheduler。
    """

    def __init__(self, on_trigger: Callable[[FutureTask], Any]):
        """
        初始化调度器。
        :param on_trigger: 当任务到期触发时调用的回调函数。
        """
        self.scheduler = BackgroundScheduler()
        self.on_trigger = on_trigger

    def add_task(self, task: FutureTask) -> None:
        """将未来任务加入调度队列"""
        if task.trigger_time:
            from datetime import datetime, timezone, timedelta
            now_utc = datetime.now(timezone.utc)
            # 防时光倒流：如果大模型数学不好生成了过去的时间，强制重置为 5 分钟后
            if task.trigger_time <= now_utc:
                task.trigger_time = now_utc + timedelta(minutes=5)
                
            self.scheduler.add_job(
                self.on_trigger,
                'date',
                run_date=task.trigger_time,
                args=[task],
                id='proactive_task',  # 固定 ID，确保新任务总是覆盖旧任务（打断机制）
                replace_existing=True
            )
            # 为了防止混淆，打印时将 UTC 时间转回本地时间显示
            local_time = task.trigger_time.astimezone()
            logger.info(f"⏰ 已挂载异步主动任务: 将在本地时间 {local_time.strftime('%Y-%m-%d %H:%M:%S')} 触发, 模式 {task.generation_mode.value}")

    def remove_task(self, task_id: str = 'proactive_task') -> None:
        """移除指定的任务，防止旧闹钟在用户意图改变后依然触发"""
        try:
            self.scheduler.remove_job(task_id)
            logger.debug(f"🗑️ 已清理过期的未来任务: {task_id}")
        except Exception:
            pass  # 如果任务不存在就不管它

    def start(self) -> None:
        """启动调度器"""
        self.scheduler.start()
        logger.info("⏳ 调度引擎 (APScheduler) 已启动")

    def stop(self) -> None:
        """停止调度器"""
        self.scheduler.shutdown(wait=False)
        logger.info("⏳ 调度引擎已关闭")
