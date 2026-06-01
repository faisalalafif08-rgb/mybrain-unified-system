# mybrain-unified-system

## حالة المستودع

هذا المستودع يمثل مساحة عمل GitHub للنظام الموحد.

المسار المحلي الذي حدده أبو عقاب للعمل الحالي:

```text
D:\OneDrive\المستندات\New project
```

والهيكل التشغيلي داخل مساحة العمل يكون:

```text
D:\OneDrive\المستندات\New project\unified_ai_system
```

> هذا المسار مساحة تنفيذ/Workspace، وليس اسمًا نهائيًا للنظام.

---

## التعريف المعماري

النظام ليس PDF فقط، ولا OCR فقط، ولا شات فقط، ولا واجهة فقط.

النظام يتكوّن من:

- قلب النظام والتشغيل.
- العقل العام.
- المستودع ومحطات تجهيز البيانات.
- الذاكرة Bronze / Silver / Gold.
- الوكلاء وذاكرتهم المحلية.
- العقول المتخصصة والأنظمة الخارجية المزروعة عبر Adapters.
- الواجهات ولوحات التحكم والمراقبة.
- السجل Registry والمستودع Repository والسياسات والتقارير.

---

## الهيكل الرسمي

```text
unified_ai_system/
  00_system_core/
  01_general_mind/
  02_data_warehouse/
  03_memory/
  04_agents/
  05_specialized_systems/
  06_interfaces/
  07_runtime/
  08_repository/
  09_registry/
  10_adapters/
  11_policies/
  12_docs/
  13_tools/
```

---

## القانون الأعلى

```text
لا تشغيل مباشر.
لا ZIP مباشر.
لا سكربت Legacy مباشر.
لا raw يدخل العقل العام.
لا Gold بدون Decision Gate.
لا حذف أو نقل للأصل.
كل شيء يدخل عبر Gateway ثم Warehouse ثم Heart ثم Reports ثم Decision Gate.
```

---

## مسار البيانات

```text
File / Chat / Interface / System Input
→ Interface Quick Intake أو File Gateway
→ Interface Intake Handler / Warehouse Gate
→ 00_system_core / Heart Kernel
→ 02_data_warehouse / Stations
→ 03_memory / Bronze
→ 03_memory / Silver
→ Reports + BrainReports
→ 01_general_mind / Decision Fusion
→ Decision Gate
→ 03_memory / Gold
→ 04_agents / Agent Feed
→ 06_interfaces / Output
```

---

## مبدأ الأنظمة الكبيرة

أي نظام كبير، مكتبة، ZIP، مشروع قديم، محرك OCR، MMPose، Fooocus، EasyOCR، أو نظام صوت/فيديو/أفاتار:

```text
يدخل كله كمصدر خام
→ يُفحص
→ يُفهرس
→ يُقطّع
→ يُصنّف
→ يتحول إلى Station + Capability Pack + Adapter + BrainReport
→ ثم يقرر العقل العام طريقة زرعه وتشغيله
```

ولا يتم تشغيله كما هو.

---

## ملفات التأسيس الحالية

```text
unified_ai_system/11_policies/large_systems_warehouse_chat_policy.md
unified_ai_system/09_registry/foundation_registry.json
unified_ai_system/02_data_warehouse/stations/WAREHOUSE_STATIONS.md
unified_ai_system/04_agents/registry/agent_learning_policy.json
unified_ai_system/07_runtime/inbox/.gitkeep
unified_ai_system/07_runtime/reports/.gitkeep
```
