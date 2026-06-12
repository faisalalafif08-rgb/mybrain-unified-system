#!/bin/bash
# Setup Script for AI News Channel
# سكريبت التثبيت لقناة الأخبار بالذكاء الاصطناعي

set -e

echo "🚀 بدء تثبيت قناة الأخبار بالذكاء الاصطناعي..."
echo "================================"

# Check Python version
echo "✅ التحقق من إصدار Python..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "✅ إنشاء بيئة Python الافتراضية..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "تم إنشاء venv"
fi

# Activate virtual environment
echo "✅ تفعيل البيئة الافتراضية..."
source venv/bin/activate

# Upgrade pip
echo "✅ ترقية pip..."
pip install --upgrade pip

# Install requirements
echo "✅ تثبيت المكتبات المطلوبة..."
pip install -r requirements.txt

# Create directories
echo "✅ إنشاء المجلدات المطلوبة..."
mkdir -p data/{avatars,generated_videos,logs}
mkdir -p output
mkdir -p audio
mkdir -p temp

# Copy config files
echo "✅ نسخ ملفات الإعدادات..."
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || echo ".env.example غير موجود"
fi

echo ""
echo "================================"
echo "✨ تم التثبيت بنجاح!"
echo "================================"
echo ""
echo "الخطوات التالية:"
echo "1. عدّل ملف .env وأضف مفاتيح API"
echo "2. شغّل: python main.py"
echo "3. افتح المتصفح على: http://localhost:8000"
echo ""
