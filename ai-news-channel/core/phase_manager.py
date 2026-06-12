# Smart Phase Manager
# مدير المراحل الذكي

import logging
import threading
from typing import Dict, List, Callable, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class PhaseStatus(Enum):
    """حالات المرحلة"""
    IDLE = "idle"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class PhaseMetrics:
    """قياسات المرحلة"""
    name: str
    status: PhaseStatus
    tasks_processed: int
    tasks_failed: int
    tasks_pending: int
    avg_processing_time: float
    total_time_spent: float
    last_updated: str
    current_task_id: Optional[str] = None
    error_message: Optional[str] = None

class PhaseExecutor:
    """معالج المرحلة"""
    
    def __init__(self, name: str, handler: Callable, max_parallel: int = 1):
        self.name = name
        self.handler = handler
        self.max_parallel = max_parallel
        self.status = PhaseStatus.IDLE
        self.tasks_processed = 0
        self.tasks_failed = 0
        self.tasks_pending = 0
        self.processing_times = []
        self.total_time = 0
        self.current_task_id = None
        self.error_message = None
        self.lock = threading.Lock()
    
    async def execute(self, task_data: Dict) -> Dict:
        """تنفيذ المرحلة"""
        start_time = datetime.now()
        
        try:
            with self.lock:
                self.status = PhaseStatus.PROCESSING
                self.current_task_id = task_data.get('task_id')
            
            result = await self.handler(task_data)
            
            # حساب وقت المعالجة
            duration = (datetime.now() - start_time).total_seconds()
            self.processing_times.append(duration)
            self.total_time += duration
            
            with self.lock:
                self.tasks_processed += 1
                self.status = PhaseStatus.IDLE
            
            return {'status': 'success', 'result': result, 'duration': duration}
        
        except Exception as e:
            logger.error(f"خطأ في المرحلة {self.name}: {e}")
            
            with self.lock:
                self.tasks_failed += 1
                self.error_message = str(e)
                self.status = PhaseStatus.ERROR
            
            return {'status': 'error', 'error': str(e)}
    
    def get_metrics(self) -> PhaseMetrics:
        """الحصول على قياسات المرحلة"""
        avg_time = (sum(self.processing_times) / len(self.processing_times) 
                   if self.processing_times else 0)
        
        return PhaseMetrics(
            name=self.name,
            status=self.status,
            tasks_processed=self.tasks_processed,
            tasks_failed=self.tasks_failed,
            tasks_pending=self.tasks_pending,
            avg_processing_time=avg_time,
            total_time_spent=self.total_time,
            last_updated=datetime.now().isoformat(),
            current_task_id=self.current_task_id,
            error_message=self.error_message
        )

class SmartPhaseManager:
    """مدير المراحل الذكي"""
    
    def __init__(self):
        self.phases = {}
        self.phase_order = []
        self.parallel_phases = {}  # المراحل التي تعمل بالتوازي
        self.lock = threading.Lock()
    
    def register_phase(self, name: str, handler: Callable, 
                       parallel: bool = False, max_parallel: int = 1):
        """تسجيل مرحلة جديدة"""
        executor = PhaseExecutor(name, handler, max_parallel)
        
        with self.lock:
            self.phases[name] = executor
            if not parallel:
                self.phase_order.append(name)
            else:
                if 'parallel' not in self.parallel_phases:
                    self.parallel_phases['parallel'] = []
                self.parallel_phases['parallel'].append(name)
        
        logger.info(f"تم تسجيل المرحلة: {name}")
    
    async def execute_pipeline(self, task_data: Dict) -> Dict:
        """تنفيذ خط أنابيب كامل"""
        results = {}
        current_data = task_data
        
        # تنفيذ المراحل المتسلسلة
        for phase_name in self.phase_order:
            phase = self.phases[phase_name]
            logger.info(f"بدء المرحلة: {phase_name}")
            
            result = await phase.execute(current_data)
            results[phase_name] = result
            
            if result['status'] == 'error':
                logger.error(f"فشلت المرحلة: {phase_name}")
                break
            
            # استخدام نتيجة المرحلة كمدخل للمرحلة التالية
            current_data = result.get('result', current_data)
        
        return results
    
    def get_pipeline_status(self) -> Dict:
        """حالة خط الأنابيب"""
        status = {
            'total_phases': len(self.phases),
            'sequential': self.phase_order,
            'phases': {},
            'overall_health': 'healthy'
        }
        
        total_failed = 0
        for phase_name, executor in self.phases.items():
            metrics = executor.get_metrics()
            status['phases'][phase_name] = metrics.__dict__
            total_failed += metrics.tasks_failed
        
        if total_failed > 0:
            status['overall_health'] = 'degraded'
        
        return status
    
    def get_bottleneck(self) -> Optional[str]:
        """اكتشاف الاختناق"""
        max_time = 0
        bottleneck = None
        
        for phase_name, executor in self.phases.items():
            metrics = executor.get_metrics()
            if metrics.avg_processing_time > max_time:
                max_time = metrics.avg_processing_time
                bottleneck = phase_name
        
        return bottleneck
    
    def optimize_phases(self) -> Dict:
        """تحسين توزيع المراحل"""
        recommendations = {}
        
        for phase_name, executor in self.phases.items():
            metrics = executor.get_metrics()
            
            # التحقق من معدل الفشل
            if metrics.tasks_failed > metrics.tasks_processed * 0.1:
                recommendations[phase_name] = 'معدل فشل عالي - تحقق من المرحلة'
            
            # التحقق من وقت المعالجة
            if metrics.avg_processing_time > 60:
                recommendations[phase_name] = 'وقت معالجة طويل - فكر في التوازي'
        
        return recommendations


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    manager = SmartPhaseManager()
    print("مدير المراحل الذكي جاهز")
