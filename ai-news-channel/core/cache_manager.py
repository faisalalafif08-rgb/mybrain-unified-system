# Advanced Caching System
# نظام التخزين المؤقت المتقدم

import logging
import hashlib
import pickle
import json
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class CacheStrategy:
    """استراتيجية التخزين المؤقت"""
    
    def __init__(self, max_size_mb: int = 1024, ttl_hours: int = 24):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl = timedelta(hours=ttl_hours)
        self.cache = {}
        self.access_times = {}
        self.lock = threading.Lock()
        self.current_size = 0
    
    def get_key_hash(self, key: str) -> str:
        """حساب بصمة المفتاح"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def put(self, key: str, value: Any) -> bool:
        """إضافة عنصر إلى الذاكرة المؤقتة"""
        try:
            with self.lock:
                # حساب حجم البيانات
                data_size = len(pickle.dumps(value))
                
                # تفريغ المساحة إذا لزم الأمر
                while self.current_size + data_size > self.max_size_bytes:
                    self._evict_least_used()
                
                key_hash = self.get_key_hash(key)
                self.cache[key_hash] = value
                self.access_times[key_hash] = datetime.now()
                self.current_size += data_size
                
                return True
        
        except Exception as e:
            logger.error(f"خطأ في إضافة البيانات للذاكرة المؤقتة: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """استرجاع عنصر من الذاكرة المؤقتة"""
        with self.lock:
            key_hash = self.get_key_hash(key)
            
            if key_hash not in self.cache:
                return None
            
            # التحقق من انتهاء صلاحية العنصر
            if datetime.now() - self.access_times[key_hash] > self.ttl:
                del self.cache[key_hash]
                del self.access_times[key_hash]
                return None
            
            # تحديث وقت الوصول
            self.access_times[key_hash] = datetime.now()
            
            return self.cache[key_hash]
    
    def _evict_least_used(self):
        """حذف العناصر الأقل استخداماً"""
        if not self.cache:
            return
        
        # حذف العنصر الأقل وصولاً مؤخراً
        lru_key = min(self.access_times, key=self.access_times.get)
        data_size = len(pickle.dumps(self.cache[lru_key]))
        
        del self.cache[lru_key]
        del self.access_times[lru_key]
        self.current_size -= data_size
        
        logger.info(f"تم حذف عنصر من الذاكرة المؤقتة")
    
    def clear(self):
        """مسح الذاكرة المؤقتة"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.current_size = 0

class DiskCache:
    """ذاكرة مؤقتة على القرص الصلب"""
    
    def __init__(self, cache_dir: str = './cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.lock = threading.Lock()
    
    def put(self, key: str, value: Any) -> bool:
        """حفظ على القرص"""
        try:
            with self.lock:
                key_hash = hashlib.md5(key.encode()).hexdigest()
                cache_file = self.cache_dir / f"{key_hash}.cache"
                
                with open(cache_file, 'wb') as f:
                    pickle.dump(value, f)
                
                return True
        
        except Exception as e:
            logger.error(f"خطأ في حفظ البيانات: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """استرجاع من القرص"""
        try:
            with self.lock:
                key_hash = hashlib.md5(key.encode()).hexdigest()
                cache_file = self.cache_dir / f"{key_hash}.cache"
                
                if not cache_file.exists():
                    return None
                
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        
        except Exception as e:
            logger.error(f"خطأ في استرجاع البيانات: {e}")
            return None
    
    def get_cache_size(self) -> int:
        """حجم الذاكرة المؤقتة بالبايتات"""
        total_size = 0
        for file in self.cache_dir.glob('*.cache'):
            total_size += file.stat().st_size
        return total_size

class HybridCache:
    """ذاكرة مؤقتة هجينة (RAM + Disk)"""
    
    def __init__(self, memory_cache_mb: int = 512, disk_cache_dir: str = './cache'):
        self.memory_cache = CacheStrategy(max_size_mb=memory_cache_mb)
        self.disk_cache = DiskCache(disk_cache_dir)
        self.stats = {
            'memory_hits': 0,
            'disk_hits': 0,
            'misses': 0
        }
    
    def put(self, key: str, value: Any, tier: str = 'memory'):
        """إضافة إلى الذاكرة المؤقتة"""
        if tier == 'memory':
            self.memory_cache.put(key, value)
        elif tier == 'disk':
            self.disk_cache.put(key, value)
        elif tier == 'both':
            self.memory_cache.put(key, value)
            self.disk_cache.put(key, value)
    
    def get(self, key: str) -> Optional[Any]:
        """استرجاع من الذاكرة المؤقتة"""
        # محاولة الحصول من الذاكرة أولاً
        value = self.memory_cache.get(key)
        if value is not None:
            self.stats['memory_hits'] += 1
            return value
        
        # ثم من القرص
        value = self.disk_cache.get(key)
        if value is not None:
            self.stats['disk_hits'] += 1
            # إعادة المحتوى إلى الذاكرة
            self.memory_cache.put(key, value)
            return value
        
        self.stats['misses'] += 1
        return None
    
    def get_stats(self) -> Dict:
        """إحصائيات الذاكرة المؤقتة"""
        total_hits = self.stats['memory_hits'] + self.stats['disk_hits']
        total_requests = total_hits + self.stats['misses']
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'memory_hits': self.stats['memory_hits'],
            'disk_hits': self.stats['disk_hits'],
            'misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'disk_cache_size_mb': self.disk_cache.get_cache_size() / 1024 / 1024
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # اختبار النظام
    cache = HybridCache()
    
    # إضافة بيانات
    cache.put('test_key', {'data': 'test_value'}, tier='both')
    
    # استرجاع البيانات
    value = cache.get('test_key')
    print(f"القيمة: {value}")
    print(f"الإحصائيات: {cache.get_stats()}")
