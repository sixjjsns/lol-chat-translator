"""后台任务管理：用 QThread + 信号槽执行翻译任务，避免阻塞 UI 主线程。

设计（标准 Qt worker 模式）：
- TaskManager 是 QObject（主线程），持有 QThread 和 _Worker。
- _Worker 被 moveToThread 到 QThread，其 run_task 在 worker 线程执行。
- 通过「队列信号 + 完成信号」串行驱动，避免在主线程跑死循环。
- 结果通过信号（finished / failed）安全回传主线程。
"""
import queue

from PySide6.QtCore import QObject, QThread, Signal

from ..core.models import TranslationRequest
from ..core.translation_service import TranslationService
from ..infrastructure.logging_config import get_logger

logger = get_logger()


class _Worker(QObject):
    """运行在 QThread 中的工作对象，串行处理任务队列。"""

    finished = Signal(object)   # TranslationResult
    failed = Signal(str)        # 异常消息
    _next = Signal()            # 内部：请求处理下一个任务

    def __init__(self, translation_service: TranslationService):
        super().__init__()
        self._service = translation_service
        self._queue: queue.Queue = queue.Queue()
        self._busy = False

    def enqueue(self, request: TranslationRequest):
        """入队（线程安全），并触发处理。"""
        self._queue.put(request)
        self._next.emit()

    def _process_next(self):
        """在 worker 线程执行，处理队列中的一个任务。"""
        if self._busy:
            return
        try:
            request = self._queue.get_nowait()
        except queue.Empty:
            return
        self._busy = True
        try:
            result = self._service.translate(request)
            self.finished.emit(result)
        except Exception as e:
            logger.warning("翻译任务异常: %s", e)
            self.failed.emit(str(e))
        finally:
            self._busy = False
            # 若队列还有任务，继续处理
            if not self._queue.empty():
                self._next.emit()

    @property
    def busy(self) -> bool:
        return self._busy


class TaskManager(QObject):
    """翻译任务管理器（主线程对象）。"""

    finished = Signal(object)   # TranslationResult
    failed = Signal(str)        # 错误消息

    def __init__(self, translation_service: TranslationService, parent=None):
        super().__init__(parent)
        self._thread = QThread()
        self._worker = _Worker(translation_service)
        self._worker.moveToThread(self._thread)

        # 连接 worker 内部信号（跨线程自动排队，槽在 worker 线程执行）
        self._worker._next.connect(self._worker._process_next)

        # 转发结果信号到主线程
        self._worker.finished.connect(self.finished.emit)
        self._worker.failed.connect(self.failed.emit)

    def start(self):
        self._thread.start()

    def stop(self):
        self._thread.quit()
        self._thread.wait(2000)

    def enqueue(self, request: TranslationRequest):
        self._worker.enqueue(request)

    @property
    def busy(self) -> bool:
        return self._worker.busy
