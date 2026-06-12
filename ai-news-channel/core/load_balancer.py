# Smart Load Distribution System
# نظام توزيع الحمل الذكي

import logging
import psutil
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class TaskPhase(Enum):
    """مراحل المعالجة"""
    QUEUE = "queue"
    IMAGE_GENERATION = "image_generation"
    IMAGE_ENHANCEMENT = "image_enhancement"
    VIDEO_EDITING = "video_editing"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskPriority(Enum):
    """أولويات المهام"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0

@dataclass
class ResourceMetrics:
    """قياسات الموارد"""
    cpu_percent: float
    memory_percent: float
    gpu_percent: float
    gpu_memory_percent: float
    disk_percent: float
    active_tasks: int
    queued_tasks: int
    timestamp: str
    
    def is_overloaded(self) -> bool:
        """التحقق من الحمل الزائد"""
        return (self.cpu_percent > 85 or 
                self.memory_percent > 80 or 
                self.gpu_percent > 90)
    
    def available_capacity(self) -> float:
        """السعة المتاحة (0-1)"""
        avg_usage = (self.cpu_percent + self.memory_percent + self.gpu_percent) / 3
        return (100 - avg_usage) / 100

@dataclass
class Task:
    """تعريف المهمة"""
    task_id: str
    name: str
    priority: TaskPriority
    phase: TaskPhase
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_duration: int = 0  # بالثواني
    actual_duration: int = 0
    resource_requirements: Dict = None
    status: str = "pending"
    progress: float = 0.0  # 0-100
    error_message: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    
    def is_completed(self) -> bool:
        return self.phase in [TaskPhase.COMPLETED, TaskPhase.FAILED]
    
    def duration_so_far(self) -> int:
        """المدة منذ البداية"""
        if self.started_at:
            start = datetime.fromisoformat(self.started_at)
            return int((datetime.now() - start).total_seconds())
        return 0

class ResourceMonitor:
    """مراقب الموارد المتقدم"""
    
    def __init__(self, update_interval: int = 2):
        self.update_interval = update_interval
        self.metrics_history = []
        self.max_history = 1000
        self.monitoring = False
        self.current_metrics = None
    
    def get_current_metrics(self) -> ResourceMetrics:
        """الحصول على قياسات الموارد الحالية"""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        # محاولة الحصول على معلومات GPU
        gpu_percent = 0.0
        gpu_memory_percent = 0.0
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_percent = gpu.load * 100
                gpu_memory_percent = gpu.memoryUsed / gpu.memoryTotal * 100
        except ImportError:
            logger.warning("GPUtil غير مثبت - لن يتم مراقبة GPU")
        
        metrics = ResourceMetrics(
            cpu_percent=cpu,
            memory_percent=memory,
            gpu_percent=gpu_percent,
            gpu_memory_percent=gpu_memory_percent,
            disk_percent=disk,
            active_tasks=0,
            queued_tasks=0,
            timestamp=datetime.now().isoformat()
        )
        
        self.current_metrics = metrics
        self.metrics_history.append(metrics)
        
        # الاحتفاظ بآخر N قياس فقط
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
        
        return metrics
    
    def get_average_metrics(self, last_n: int = 10) -> ResourceMetrics:
        """الحصول على متوسط القياسات"""
        if not self.metrics_history:
            return self.get_current_metrics()
        
        recent = self.metrics_history[-last_n:]
        
        avg_cpu = sum(m.cpu_percent for m in recent) / len(recent)
        avg_memory = sum(m.memory_percent for m in recent) / len(recent)
        avg_gpu = sum(m.gpu_percent for m in recent) / len(recent)
        avg_gpu_mem = sum(m.gpu_memory_percent for m in recent) / len(recent)
        avg_disk = sum(m.disk_percent for m in recent) / len(recent)
        
        return ResourceMetrics(
            cpu_percent=avg_cpu,
            memory_percent=avg_memory,
            gpu_percent=avg_gpu,
            gpu_memory_percent=avg_gpu_mem,
            disk_percent=avg_disk,
            active_tasks=recent[-1].active_tasks if recent else 0,
            queued_tasks=recent[-1].queued_tasks if recent else 0,
            timestamp=datetime.now().isoformat()
        )
    
    def get_metrics_trend(self) -> Dict:
        """تحليل اتجاه الحمل"""
        if len(self.metrics_history) < 2:
            return {}
        
        recent_5 = self.metrics_history[-5:]
        cpu_trend = recent_5[-1].cpu_percent - recent_5[0].cpu_percent
        memory_trend = recent_5[-1].memory_percent - recent_5[0].memory_percent
        
        return {
            'cpu_trend': cpu_trend,  # موجب = زيادة
            'memory_trend': memory_trend,
            'direction': 'increasing' if cpu_trend > 0 else 'decreasing',
            'stable': abs(cpu_trend) < 5
        }

class SmartTaskQueue:
    """قائمة الانتظار الذكية"""
    
    def __init__(self, max_queue_size: int = 100):
        self.queue = []
        self.max_queue_size = max_queue_size
        self.lock = threading.Lock()
    
    def add_task(self, task: Task) -> bool:
        """إضافة مهمة إلى قائمة الانتظار"""
        with self.lock:
            if len(self.queue) >= self.max_queue_size:
                logger.warning("قائمة الانتظار امتلأت")
                return False
            
            self.queue.append(task)
            # ترتيب حسب الأولوية
            self.queue.sort(key=lambda x: (x.priority.value, x.created_at))
            logger.info(f"تم إضافة المهمة: {task.task_id}")
            return True
    
    def get_next_task(self) -> Optional[Task]:
        """الحصول على المهمة التالية"""
        with self.lock:
            if self.queue:
                return self.queue.pop(0)
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """البحث عن مهمة معينة"""
        with self.lock:
            for task in self.queue:
                if task.task_id == task_id:
                    return task
            return None
    
    def get_queue_status(self) -> Dict:
        """حالة قائمة الانتظار"""
        with self.lock:
            return {
                'total': len(self.queue),
                'high_priority': sum(1 for t in self.queue if t.priority.value <= 1),
                'normal_priority': sum(1 for t in self.queue if t.priority.value == 2),
                'low_priority': sum(1 for t in self.queue if t.priority.value == 3)
            }

class LoadBalancer:
    """موازن الحمل الذكي"""
    
    def __init__(self):
        self.monitor = ResourceMonitor()
        self.task_queue = SmartTaskQueue()
        self.active_tasks = {}
        self.completed_tasks = []
        self.lock = threading.Lock()
        
        # حدود الحمل
        self.thresholds = {
            'cpu_warning': 70,
            'cpu_critical': 85,
            'memory_warning': 70,
            'memory_critical': 80,
            'gpu_warning': 80,
            'gpu_critical': 90
        }
    
    def can_process_task(self, task: Task) -> bool:
        """التحقق من إمكانية معالجة المهمة"""
        metrics = self.monitor.get_current_metrics()
        
        # إذا كانت المهمة حرجة، نعالجها حتى لو كان الحمل عالي
        if task.priority == TaskPriority.CRITICAL:
            return True
        
        # التحقق من الموارد المتاحة
        if metrics.is_overloaded():
            if task.priority == TaskPriority.HIGH:
                # السماح بمهام عالية الأولوية فقط
                return metrics.cpu_percent < self.thresholds['cpu_critical']
            return False
        
        return True
    
    def distribute_tasks(self) -> Dict:
        """توزيع المهام على المراحل"""
        distribution = {
            'ready_to_process': [],
            'waiting': [],
            'processing': [],
            'bottleneck_detected': False,
            'recommendation': ''
        }
        
        metrics = self.monitor.get_current_metrics()
        metrics.active_tasks = len(self.active_tasks)
        metrics.queued_tasks = len(self.task_queue.queue)
        
        # التحقق من الاختناقات
        if metrics.is_overloaded():
            distribution['bottleneck_detected'] = True
            distribution['recommendation'] = 'تقليل عدد المهام الجديدة'
        
        # معالجة قائمة الانتظار
        while True:
            task = self.task_queue.get_next_task()
            if not task:
                break
            
            if self.can_process_task(task):
                distribution['ready_to_process'].append(task)
                with self.lock:
                    self.active_tasks[task.task_id] = task
            else:
                distribution['waiting'].append(task)
                # إعادة المهمة إلى قائمة الانتظار
                self.task_queue.add_task(task)
        
        distribution['processing'] = list(self.active_tasks.values())
        
        logger.info(f"التوزيع: {len(distribution['ready_to_process'])} جاهزة، "
                   f"{len(distribution['waiting'])} في الانتظار")
        
        return distribution
    
    def estimate_completion_time(self) -> Dict:
        """تقدير وقت الإنجاز"""
        metrics = self.monitor.get_average_metrics()
        queue_status = self.task_queue.get_queue_status()
        
        # حساب معدل معالجة المهام
        completed = len(self.completed_tasks)
        if completed < 2:
            avg_time_per_task = 60
        else:
            avg_durations = [t.actual_duration for t in self.completed_tasks[-10:]]
            avg_time_per_task = sum(avg_durations) / len(avg_durations)
        
        total_queued = queue_status['total']
        estimated_total_time = total_queued * avg_time_per_task
        
        return {
            'total_queued': total_queued,
            'avg_time_per_task': avg_time_per_task,
            'estimated_total_seconds': estimated_total_time,
            'estimated_minutes': estimated_total_time / 60,
            'current_capacity': metrics.available_capacity()
        }
    
    def get_system_report(self) -> Dict:
        """تقرير شامل عن النظام"""
        metrics = self.monitor.get_current_metrics()
        avg_metrics = self.monitor.get_average_metrics()
        trend = self.monitor.get_metrics_trend()
        queue_status = self.task_queue.get_queue_status()
        completion = self.estimate_completion_time()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'current_metrics': {
                'cpu': metrics.cpu_percent,
                'memory': metrics.memory_percent,
                'gpu': metrics.gpu_percent,
                'disk': metrics.disk_percent
            },
            'average_metrics': {
                'cpu': avg_metrics.cpu_percent,
                'memory': avg_metrics.memory_percent,
                'gpu': avg_metrics.gpu_percent
            },
            'trend': trend,
            'queue': queue_status,
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'completion_estimate': completion,
            'system_health': self._get_health_score(metrics)
        }
    
    def _get_health_score(self, metrics: ResourceMetrics) -> str:
        """حساب درجة صحة النظام"""
        score = 100
        score -= (metrics.cpu_percent / 100) * 30
        score -= (metrics.memory_percent / 100) * 30
        score -= (metrics.gpu_percent / 100) * 30
        score -= (len(self.active_tasks) / 10) * 10
        
        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'fair'
        else:
            return 'poor'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # اختبار النظام
    balancer = LoadBalancer()
    
    # الحصول على تقرير النظام
    report = balancer.get_system_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
