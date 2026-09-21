# Suhha Agent

وكيل شخصي بينفذ مهام بدالك (إيميلات، مواعيد، متابعة مشاريع على GitHub،
بحث وتلخيص) وبيتحسن مع الوقت لوحده.

## إزاي بيتطور؟

الأداة مش بتعدل كودها بنفسها (ده خطير وصعب تتأكدي إنه شغال صح). اللي
بيحصل بدل كده:

1. كل مرة تنفذي مهمة، بيتسجل ملخص للي حصل في `memory/history.jsonl`.
2. تقدري تسيبي فيدباك صريح: `python cli.py feedback "الرد كان طويل أوي"`.
3. لما تشغلي `python cli.py reflect`، الوكيل بيراجع السجل والفيدباك،
   ويطلع قاعدة سلوك قصيرة، ويضيفها لملف `memory/learned_rules.md`.
4. الملف ده بيتحمّل تلقائي جوه تعليمات الوكيل (system prompt) في **كل**
   مهمة جاية. يعني الدروس اللي اتعلمها فعلاً بتأثر على شغله من بعدها.

الملف نفسه نص عادي تقدري تفتحيه وتعدليه أو تمسحي منه أي حاجة مش عاجباكي
في أي وقت.

## التثبيت

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

افتحي `.env` وحطي فيه:

- `ANTHROPIC_API_KEY` — مطلوب، ده اللي بيشغل تفكير الوكيل.
- `GITHUB_TOKEN` و `GITHUB_DEFAULT_REPO` — اختياري، لو عايزة متابعة مشاريع.
- لإيميلات/مواعيد جوجل: اعملي OAuth client (Desktop app) من
  [Google Cloud Console](https://console.cloud.google.com/), فعّلي
  Gmail API و Calendar API، نزّلي ملف الـ credentials وسميه
  `credentials.json` وحطيه في جذر المشروع. أول مرة تستخدمي أداة إيميل
  أو كالندر هيفتح متصفح تسجيل دخول، وبعدها هيتحفظلك `token.json`
  تلقائي.

## الاستخدام

```bash
# مهمة لمرة واحدة
python cli.py run "شوفيلي آخر الـ issues المفتوحة وابعتيلي ملخص"

# محادثة تفاعلية
python cli.py chat

# سجلي فيدباك
python cli.py feedback "كنت عايزة رد أقصر"

# خلي الوكيل يتعلم من السجل والفيدباك
python cli.py reflect
```

## البنية

```
suhha/
  agent.py       # حلقة الوكيل الأساسية (Anthropic tool-use loop)
  learn.py       # خطوة التعلم/التطور الذاتي
  memory.py      # تفضيلات + سجل مهام + ملف القواعد المتعلمة
  config.py      # قراءة متغيرات البيئة
  tools/
    web_search.py    # بحث وجلب صفحات ويب، من غير مفتاح API
    github_tool.py    # issues/PRs عن طريق personal access token
    google_tool.py    # Gmail + Calendar عن طريق OAuth
cli.py           # نقطة الدخول
memory/          # بيتعمل تلقائي، فيه بياناتك الشخصية (متتنشرش في git)
```

## حدود مهمة

- كل الأدوات بتحتاج مفاتيح/صلاحيات إنتِ اللي بتحطيها — مفيش حاجة بتشتغل
  من غير إعداد.
- البحث على الإنترنت بيستخدم DuckDuckGo HTML عشان يشتغل من غير مفتاح؛
  لو محتاجة نتايج أدق ضيفي مزود بحث تاني في `tools/web_search.py`.
- التعلم هنا معناه "تحديث تعليمات نصية"، مش تدريب نموذج جديد. ده اللي
  خلّى الأداة آمنة إنها تشتغل أوتوماتيك من غير ما حد يراجع كل تعديل.
