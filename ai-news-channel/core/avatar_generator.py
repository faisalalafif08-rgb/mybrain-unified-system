#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Avatar Generator Module
مولد الممثلين الافتراضيين
"""

import logging
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

class AvatarGenerator:
    """مولد الممثلين الافتراضيين"""
    
    def __init__(self, config: Dict):
        """
        تهيئة مولد الممثلين
        
        Args:
            config: قاموس الإعدادات
        """
        self.config = config
        self.avatars = {}
    
    def create_avatar(self, name: str, image_url: str, properties: Dict) -> Dict:
        """
        إنشاء ممثل افتراضي
        
        Args:
            name: اسم الممثل
            image_url: رابط صورة الممثل
            properties: خصائص الممثل
            
        Returns:
            بيانات الممثل
        """
        avatar = {
            'id': f"avatar_{len(self.avatars)}",
            'name': name,
            'image_url': image_url,
            'gender': properties.get('gender', 'unknown'),
            'age': properties.get('age', 'unknown'),
            'language': properties.get('language', 'ar'),
            'voice_id': properties.get('voice_id', ''),
            'personality': properties.get('personality', ''),
            'properties': properties
        }
        
        self.avatars[avatar['id']] = avatar
        logger.info(f"تم إنشاء ممثل: {name}")
        return avatar
    
    def get_avatar(self, avatar_id: str) -> Dict:
        """
        الحصول على بيانات ممثل
        
        Args:
            avatar_id: معرف الممثل
            
        Returns:
            بيانات الممثل
        """
        return self.avatars.get(avatar_id, {})
    
    def list_avatars(self) -> List[Dict]:
        """عرض قائمة جميع الممثلين"""
        return list(self.avatars.values())
    
    def update_avatar(self, avatar_id: str, properties: Dict) -> Dict:
        """
        تحديث خصائص الممثل
        
        Args:
            avatar_id: معرف الممثل
            properties: الخصائص الجديدة
            
        Returns:
            الممثل المحدث
        """
        if avatar_id in self.avatars:
            self.avatars[avatar_id].update(properties)
            logger.info(f"تم تحديث الممثل: {avatar_id}")
        
        return self.avatars.get(avatar_id, {})
    
    def delete_avatar(self, avatar_id: str) -> bool:
        """
        حذف ممثل
        
        Args:
            avatar_id: معرف الممثل
            
        Returns:
            نجاح العملية
        """
        if avatar_id in self.avatars:
            del self.avatars[avatar_id]
            logger.info(f"تم حذف الممثل: {avatar_id}")
            return True
        return False


if __name__ == '__main__':
    # مثال على الاستخدام
    config = {}
    generator = AvatarGenerator(config)
    
    # إنشاء ممثل
    avatar = generator.create_avatar(
        'أحمد محمد',
        'https://example.com/image.jpg',
        {
            'gender': 'male',
            'age': 35,
            'language': 'ar',
            'voice_id': 'voice_1'
        }
    )
    
    print(json.dumps(avatar, ensure_ascii=False, indent=2))
