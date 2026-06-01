# Large Systems + Warehouse + Chat Policy

## 1) الهدف

هذه السياسة تثبت طريقة التعامل مع أي نظام كبير أو ملف أو مشروع قديم أو مكتبة أو ZIP أو مدخل شات أو واجهة داخل النظام الموحد.

القاعدة الأساسية:

```text
النظام الكبير لا يعمل كامل كما هو.
النظام الكبير يُزرع.
الذاكرة تحفظ وتفرز.
العقل يفهم ويقرر.
القلب يشغّل ويراقب.
الواجهة تعرض وتتحكم.
والوكلاء يساعدون حسب السياق بدون دور ثابت.
```

---

## 2) الممنوعات

ممنوع:

- تشغيل ZIP مباشرة.
- تشغيل سكربتات Legacy مباشرة.
- تشغيل مكتبة خارجية كاملة بدون Adapter.
- إدخال raw إلى العقل العام.
- إدخال raw إلى Gold.
- تعديل أو حذف أو نقل الأصل.
- اعتماد معرفة من OCR مباشرة.
- استخدام py_compile لأنه ينشئ `__pycache__`.
- جعل الواجهة أو الوكيل صاحب قرار نهائي.

---

## 3) مسار الدخول

كل مدخل يدخل عبر بوابة مناسبة:

```text
Chat / UI Input
→ Interface Quick Intake
→ Interface Intake Handler
→ Heart / Warehouse Gate

File / ZIP / Project
→ File Gateway
→ Warehouse Intake
→ Heart Scanner

External-like System Source
→ Warehouse Runtime Inbox
→ Safe Inventory
→ Manifest
```

---

## 4) محطات المستودع

المستودع لا يقرر ولا يكتب Gold.

وظائفه:

- Intake.
- Hash / SHA256.
- Fingerprint.
- Type Detection.
- Metadata.
- Classification.
- Safe Extract.
- Manifest.
- Relationship Mapping.
- Extraction.
- Cleanup.
- Quality Review.
- Chunking.
- Embedding preparation.
- Memory Write Proposal.
- Agent Feed Proposal.
- BrainReport.

---

## 5) Bronze / Silver / Gold

```text
Bronze = خام محفوظ ومفهرس.
Silver = منظم، منقح، مقطع، ومجهز.
Gold = معتمد فقط بعد Decision Gate.
```

لا يدخل Gold إلا بعد:

1. تقرير المستودع.
2. تقرير العقول المتخصصة عند الحاجة.
3. تقارير الوكلاء عند الحاجة.
4. فحص الأخطاء.
5. قرار العقل العام.
6. Decision Gate.

---

## 6) الأنظمة الكبيرة

أي نظام كبير يتحول إلى:

```text
Station
+ Capability Pack
+ Adapter
+ Contract
+ Manifest
+ BrainReport
```

ولا يعمل باسمه القديم داخل النظام.

الاسم القديم يبقى فقط:

```text
source_name
source_path
lineage
```

---

## 7) الكود القديم

فحص Python يكون قراءة آمنة فقط:

- AST syntax-only.
- بدون py_compile.
- بدون تشغيل imports.
- بدون إنشاء `__pycache__`.
- النتائج تكتب في reports فقط.

---

## 8) الشات والواجهة

الواجهة ليست عقلًا ولا مستودعًا.

وظيفتها:

- استقبال المدخلات.
- إعطاء input_id.
- فحص سريع للحجم والخطر والنوع.
- إرسال input_record إلى الطبقات التالية.
- عرض الحالة والمخرجات.
- توفير تحكم ومراقبة.

ولا تعتمد معرفة نهائية.

---

## 9) الوكلاء

الوكلاء شخصيات تشغيلية مرنة.

لكل وكيل:

- working_memory.
- private_memory.
- learning_unit.
- local_agent_mind.
- discovery_reports.

لكن الوكيل:

- لا يكتب Gold.
- لا يعتمد معرفة نهائية.
- لا يقرر القرار النهائي.
- يرجع اكتشافاته للمستودع وDecision Gate.

---

## 10) العقل العام

العقل العام يتكوّن من المناهج الخمسة داخل:

```text
unified_ai_system/01_general_mind/methodology_council
```

والقرار النهائي يخرج من دمج المناهج عبر:

```text
decision_fusion
```

ولا يخرج من واجهة أو وكيل أو منهج منفصل.
