"""
WVF X (Twitter) — Real Post Templates

Actual published @WomensVFund X posts, transcribed from screenshots the
client shared directly in conversation (Aug 17-18, 2026) — the profile
itself was also confirmed as @WomensVFund (not @womensventfund, which
an earlier assumption in this codebase had used). Used as "Fixed
template" starting points on the event-form page — staff pick one and
use/edit it directly, with no AI call involved. Distinct from AI Copy
generation (app/services/prompts.py's "x" SOCIAL_POST_VARIANTS entry),
which today uses only generic platform conventions since it wasn't yet
grounded in these real posts — see the note in prompts.py for updating
that once these are cross-referenced.

Every entry below is real, published copy — not written or paraphrased.
Several source screenshots truncated long URLs/hashtag strings with
"..." in X's own UI (scrolled or link-shortened display) — those are
preserved AS TRUNCATED below rather than guessing the missing portion.
Do not "complete" a truncated field without going back to the real post.
"""

X_TEMPLATES: dict[str, dict] = {
    "money_credit_webinar": {
        "label": "Event promo — Money & Credit webinar",
        "category": "event_promo",
        "caption": """Register now before spots are gone: us06web.zoom.us/webinar/regist...

#WVF""",
        "hashtags": [],
        "truncated": True,
    },
    "legal_help_10_spots": {
        "label": "Event promo — urgency framing, checklist",
        "category": "event_promo",
        "caption": """🚨 ONLY 10 SPOTS LEFT! 🚨

Need legal help for your business?

Get a one-on-one consultation with volunteer attorneys through the City Bar Justice Center.

✅ Contracts ✅ Leases ✅ Business issues
🗓 June 25

Register now before spots are gone: us06web.zoom.us/webinar/regist...

#WVF""",
        "hashtags": [],
        "truncated": True,
    },
    "government_contracting": {
        "label": "Event promo — government contracting webinar",
        "category": "event_promo",
        "caption": """🚨 Don't Leave Money on the Table!

Learn how to become #MWBE Certified and compete for government contracts.

🗓 Wednesday, July 29, 2026 | 🕐 11 AM ET

📌 Register NOW:
us06web.zoom.us/webinar/regist...""",
        "hashtags": [
            "#GovernmentContracts",
            "#SmallBusiness",
            "#WomenEntrepreneurs",
            "#WomensVentureFund",
        ],
    },
    "money_credit_score_aug": {
        "label": "Event promo — Money & Credit, August session",
        "category": "event_promo",
        "caption": """🗓 Aug. 12 | 12–1 PM

👉 Register: us06web.zoom.us/webinar/regist...""",
        "hashtags": ["#SmallBusiness", "#CreditScore"],
        "truncated": True,
    },
    "digital_marketing_summer_series": {
        "label": "Pinned post — Digital Marketing Summer Series (recurring course)",
        "category": "recurring_series",
        "caption": """Check out "Digital Marketing Summer Series for Women-Owned Small Businesses" eventbrite.com/e/digital-mark... @Eventbrite

Every Tuesday 5:30 pm ET, July 27–Aug 17. 4-Week Course.""",
        "hashtags": ["#DigitalMarketing", "#womenownedbusiness", "#business"],
        "truncated": True,
    },
    "financial_decisions_2027": {
        "label": "Awareness post — start-the-year financial framing",
        "category": "awareness",
        "caption": """📈 2027 starts with the financial decisions you make today.

If your credit needs work, this webinar is for you!

Learn how to build, repair & strengthen your credit and become...""",
        "hashtags": [],
        "truncated": True,
    },
}


def list_x_templates() -> dict[str, str]:
    """Returns {template_key: label} for every real X template — for
    populating a frontend picker, same pattern as
    instagram_templates.list_instagram_templates()."""
    return {key: t["label"] for key, t in X_TEMPLATES.items()}


def get_x_template(template_key: str) -> dict:
    """
    Returns one real X template's full data (label, category, caption,
    hashtags, truncated). Raises KeyError with the valid options listed
    if template_key is unrecognized, matching
    instagram_templates.get_instagram_template()'s error shape.
    """
    template = X_TEMPLATES.get(template_key)
    if template is None:
        raise KeyError(
            f"Unknown X template '{template_key}'. Valid options: "
            f"{list(X_TEMPLATES.keys())}"
        )
    return template
