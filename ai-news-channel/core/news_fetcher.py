#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Fetcher Module
جالب الأخبار من مصادر متعددة
"""

import requests
import json
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class NewsFetcher:
    """جالب الأخبار من APIs مختلفة"""
    
    def __init__(self, config: Dict):
        """
        تهيئة جالب الأخبار
        
        Args:
            config: قاموس الإعدادات
        """
        self.config = config
        self.news_sources = config.get('news_sources', {})
        self.cache = []
    
    def fetch_from_newsapi(self, api_key: str, country: str = 'sa', limit: int = 10) -> List[Dict]:
        """
        جلب الأخبار من NewsAPI
        
        Args:
            api_key: مفتاح API
            country: رمز الدولة (sa, eg, ae)
            limit: عدد الأخبار المطلوبة
            
        Returns:
            قائمة الأخبار
        """
        try:
            url = f"https://newsapi.org/v2/top-headlines?country={country}&apiKey={api_key}&pageSize={limit}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            formatted_news = []
            for article in articles:
                news_item = {
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'content': article.get('content'),
                    'source': article.get('source', {}).get('name'),
                    'image_url': article.get('urlToImage'),
                    'url': article.get('url'),
                    'published_at': article.get('publishedAt'),
                    'fetched_at': datetime.now().isoformat()
                }
                formatted_news.append(news_item)
            
            logger.info(f"تم جلب {len(formatted_news)} أخبار من NewsAPI")
            self.cache.extend(formatted_news)
            return formatted_news
            
        except requests.exceptions.RequestException as e:
            logger.error(f"خطأ في جلب الأخبار من NewsAPI: {e}")
            return []
    
    def fetch_from_mediastack(self, api_key: str, keywords: str = 'news', limit: int = 10) -> List[Dict]:
        """
        جلب الأخبار من MediaStack API
        
        Args:
            api_key: مفتاح API
            keywords: الكلمات المفتاحية
            limit: عدد الأخبار
            
        Returns:
            قائمة الأخبار
        """
        try:
            url = f"http://api.mediastack.com/v1/news?access_key={api_key}&keywords={keywords}&limit={limit}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('data', [])
            
            formatted_news = []
            for article in articles:
                news_item = {
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'content': article.get('content'),
                    'source': article.get('source'),
                    'image_url': article.get('image'),
                    'url': article.get('url'),
                    'published_at': article.get('published_at'),
                    'fetched_at': datetime.now().isoformat()
                }
                formatted_news.append(news_item)
            
            logger.info(f"تم جلب {len(formatted_news)} أخبار من MediaStack")
            self.cache.extend(formatted_news)
            return formatted_news
            
        except requests.exceptions.RequestException as e:
            logger.error(f"خطأ في جلب الأخبار من MediaStack: {e}")
            return []
    
    def get_cached_news(self) -> List[Dict]:
        """الحصول على الأخبار المخزنة مؤقتاً"""
        return self.cache
    
    def clear_cache(self):
        """مسح الذاكرة المؤقتة"""
        self.cache = []
        logger.info("تم مسح الذاكرة المؤقتة")
    
    def filter_news(self, keywords: List[str]) -> List[Dict]:
        """
        تصفية الأخبار حسب الكلمات المفتاحية
        
        Args:
            keywords: الكلمات المفتاحية
            
        Returns:
            الأخبار المصفاة
        """
        filtered = []
        for article in self.cache:
            title_lower = article.get('title', '').lower()
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    filtered.append(article)
                    break
        
        return filtered


if __name__ == '__main__':
    # مثال على الاستخدام
    config = {'news_sources': {}}
    fetcher = NewsFetcher(config)
    
    # جلب الأخبار
    # news = fetcher.fetch_from_newsapi('YOUR_API_KEY', 'sa')
    # print(json.dumps(news, ensure_ascii=False, indent=2))
