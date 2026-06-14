# اعتماد محركات الصورة: Fooocus و stable-diffusion-webui-master

## القرار

المطلوب ليس ComfyUI كقاعدة أساسية الآن، بل اعتماد:

1. Fooocus
2. stable-diffusion-webui-master / AUTOMATIC1111 WebUI

كمحركات داخل نظام الإنتاج والرؤية.

## مكانها في النظام

```text
C:\unified_ai_system
├── 05_specialized_systems
│   └── studio_vision
│       ├── fooocus
│       └── stable_diffusion_webui_master
├── 10_adapters
│   └── visual_engines
│       ├── fooocus_adapter
│       └── stable_diffusion_webui_adapter
└── 09_registry
    └── visual_engines_registry.json
```

## القانون

```text
لا نرفع الموديلات الكبيرة إلى GitHub.
لا نشغل ZIP مباشرة.
لا نشغل Fooocus أو WebUI مباشرة من القلب.
التشغيل يكون عبر Adapter فقط.
المخرجات تدخل studio_vision_core.db.
كل مخرج review_required = true.
gold_write = false.
```

## دور Fooocus

Fooocus يستخدم كمسار إنتاج سريع ومباشر للصور:

```text
text_to_image
image_prompting
style_generation
quick creative generation
production output registration
```

## دور stable-diffusion-webui-master

Stable Diffusion WebUI يستخدم كمسار تحكم متقدم:

```text
text_to_image
img2img
inpaint
upscale
face restore if available
extension tools
advanced control generation
```

## ربطها بقواعد البيانات

```text
studio_vision_core.db
├── generation_jobs
├── generation_outputs
├── prompt_blueprints
└── studio_review_queue

system_registry.db
├── components
├── external_references
├── routes
└── route_steps
```

## المسار التشغيلي

```text
Chat / Studio Request
↓
Heart Router
↓
Studio Vision Core
↓
Engine Selector
↓
Fooocus Adapter أو Stable Diffusion WebUI Adapter
↓
Local Engine Runtime
↓
Output Registration
↓
Review Queue
↓
Chat / Studio Output
```

## الخلاصة

Fooocus و stable-diffusion-webui-master محركات داخلية. لا تصبح هي النظام، ولا تختلط مع قواعد الشخصيات أو قواعد اللغة. الشخصيات مثل فنو أو مايا تطلب إنتاج صورة، والقلب يوجه الطلب إلى المحرك المناسب عبر Adapter.
