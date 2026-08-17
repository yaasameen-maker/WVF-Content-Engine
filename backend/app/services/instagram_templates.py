"""
WVF Instagram — Real Post Templates

Actual published @womensventfund Instagram posts, transcribed from
screenshots provided by the client (D:\\WVF Templates\\Instagram,
August 13-16, 2026). Used as "Fixed template" starting points on the
event-form page — staff pick one and use/edit it directly, with no AI
call involved. Distinct from AI Copy generation
(app/services/prompts.py's "instagram" SOCIAL_POST_VARIANTS entry),
which generates a NEW caption grounded in these same real posts' observed
style rather than reusing one verbatim.

Every entry below is real, published copy — not written or paraphrased.
Hashtags are transcribed exactly as they appeared (including any that
appeared as plain text without a leading # in the original screenshot,
noted per-entry).
"""

INSTAGRAM_TEMPLATES: dict[str, dict] = {
    "money_credit_webinar": {
        "label": "Event promo — checklist + emoji markers",
        "category": "event_promo",
        "caption": """Ready to make 2027 your year? Start building your credit today!

If your credit isn't where you want it to be, don't wait. Learn practical strategies to build, repair, and strengthen your credit so you're ready for future financing opportunities.

📅 Wednesday, August 12
🕐 12:00–1:00 PM

🎯 Your financial future starts now. Don't miss this FREE webinar!

👉 Register now: https://us06web.zoom.us/webinar/register/WN_tweo9dPOTquRqHC2AiwQ2w""",
        "hashtags": [
            "#WomensVentureFund",
            "#CreditRepair",
            "#LoanReady",
            "#SmallBusiness",
            "#WomenEntrepreneurs",
        ],
    },
    "legal_help_urgency": {
        "label": "Event promo — urgency/limited-spots framing",
        "category": "event_promo",
        "caption": """🚨 ONLY 10 SPOTS LEFT 🚨

Need legal help for your business?

WVF and the City Bar Justice Center are offering FREE one-on-one legal consultations with volunteer attorneys.

Get answers to your questions about:
✔ Business Structure
✔ Contracts
✔ Commercial Leases
✔ Intellectual Property
✔ Legal Issues Affecting Your Business

📅 June 25, 2026
⏰ 3:30 PM – 5:45 PM
📍 In-Person Session
💥 FREE 40-minute consultation 💥 Limited availability 💥 Approved applicants only

⚠️ Spots are filling quickly. Don't wait until it's too late.""",
        "hashtags": [],
    },
    "wvf_funding_lunch_apply": {
        "label": "Event promo — sparkle hook + emoji bullet list",
        "category": "event_promo",
        "caption": """✨ WVF IS FUNDING — ARE YOU READY? ✨

Women entrepreneurs, this is your sign to stop waiting and start growing. 🚀

Join Women's Venture Fund for our virtual Lunch & APPLY sessions where you'll learn how to confidently position your business for funding and growth.

💡 Perfect for businesses ready for:
💰 Working Capital
🏢 Second Locations
📦 Additional Product Lines
📢 Targeted Digital Marketing Campaigns
📈 Increased Revenue Growth

📅 May 29 | June 30 | July 30
⏰ 12PM–1PM ET
💻 Zoom

👤 Hosted by Nancy Soto-Askew, Director of Women's Venture Fund

🥗 Bring your lunch
💻 Bring your laptop
🔥 Bring your business goals

🔗 Register here: https://us06web.zoom.us/webinar/register/WN_0yP53RS4TlmrNVqG-SGSQQ""",
        "hashtags": [
            "#WVF",
            "#WomensVentureFund",
            "#WomenOwnedBusiness",
            "#WomenEntrepreneurs",
            "#WVFFundingandtraining",
        ],
    },
    "money_matters_workshop": {
        "label": "Event promo — checklist + \"strong businesses\" close",
        "category": "event_promo",
        "caption": """💰 READY TO GET FUNDING READY?

This Small Business Month, join Women's Venture Fund & NYWIB for a powerful financial workshop designed for entrepreneurs ready to grow smarter.

📊 Learn:
✔ Cash Flow Management
✔ Understanding Profit & Loss
✔ Budgeting for Growth
✔ Funding Readiness Tips

📅 May 19, 2026
⏰ 11AM – 12PM
💻 Zoom Webinar

🔥 Strong businesses know their numbers.
🔥 Smart entrepreneurs prepare for capital.

📮 Register now through the link:
https://us06web.zoom.us/webinar/register/WN_pVzKeDljROSl8SYe6ERbOA""",
        "hashtags": [
            "#SmallBusinessMonth",
            "#WVFWomenEntrepreneurs",
            "#MoneyMatters",
            "#BusinessGrowth",
            "#GetFundedWVFinancialEducationNYWIB",
        ],
    },
    "ai_marketing_webinar_reminder": {
        "label": "Event promo — happening-today reminder, AI/marketing topic",
        "category": "event_promo",
        "caption": """🚨 HAPPENING TODAY at 11 AM (1 Hour Only!) 🚨

Entrepreneurs—this is your moment to stop overworking your marketing and start working smarter.

Join Women's Venture Fund for a power-packed LIVE Zoom training on using AI tools to simplify and scale your marketing.

💡 Imagine creating content, emails, and social posts in minutes—not hours.
💡 Imagine automating your marketing while increasing visibility.

That's exactly what you'll learn today with guest expert Evelyn Carrasco (Bizmarley & Associates).

🔥 What you'll walk away with:
• AI tools you can start using TODAY
• Faster content creation strategies
• Smarter marketing systems that save time
• Real tactics to boost engagement + growth

⏰ 12PM – Don't miss it. This is your last call.
👉 Register now: https://us06web.zoom.us/webinar/register/WN_Tc9HZCVsQyalKfWwHy3i1w""",
        "hashtags": [],
    },
    "ai_marketing_webinar_announcement": {
        "label": "Event promo — lightning-bolt hook, full detail version",
        "category": "event_promo",
        "caption": """⚡ STOP doing everything manually ⚡

This Financial Literacy Month, learn how to WORK SMARTER.

Join WVF for a webinar on using AI to simplify your marketing and grow your business 🔥

✨ You'll learn how to:
• Create content in minutes
• Automate your marketing
• Build a stronger brand
• Save HOURS every week

🧑‍💼 Perfect for entrepreneurs ready to level up

📅 April 29
⏰ 12PM – 1PM
💻 Live Webinar

🚨 Don't miss learning during Financial Literacy Month, this is a game changer.
👉 Register now: https://us06web.zoom.us/webinar/register/WN_Tc9HZCVsQyalKfWwHy3i1w""",
        "hashtags": [
            "#WVFFinancialLiteracyMonth",
            "#BossWomen",
            "#WVFEntrepreneurLife",
            "#MarketingTips",
            "#AIforBusiness",
            "#WVF",
        ],
    },
    "financial_literacy_month_intro": {
        "label": "Awareness post — no event, monthly theme framing",
        "category": "awareness",
        "caption": """April is Financial Literacy Month!

Strong businesses = strong financial foundations 👍
✔ Cash Flow
✔ Credit
✔ Capital Access

WVF is here to help you build, grow, and fund your business with confidence.

Don't wait, start strengthening your business today.

Register: https://us06web.zoom.us/webinar/register/WN_Tc9HZCVsQyalKfWwHy3i1w""",
        "hashtags": [
            "#FinancialLiteracyMonth",
            "#WomenInBusiness",
            "#SmallBizTips",
            "#NYCEntrepreneurs",
            "#BusinessGrowth",
            "#AccessToCapital",
        ],
    },
    "money_finances_poll": {
        "label": "Engagement post — poll/comment prompt, no event",
        "category": "engagement",
        "caption": """🚩 Entrepreneurs: Stop Guessing With Your Business Finances 🚩

Your business may be making sales... but do you truly understand your numbers? 👀💰

This Small Business Month, Women's Venture Fund (WVF) and NYWIB are bringing entrepreneurs together for a powerful conversation on the financial side of business growth.

📌 If you want funding, lenders want to see that you understand:
✔ Cash Flow""",
        "hashtags": [],
    },
    "tribe_of_women_quote": {
        "label": "Quote card — inspirational, minimal caption",
        "category": "quote",
        "caption": """Behind every successful woman is a tribe of other successful women who have her back""",
        "hashtags": [],
    },
    "money_moves_poll": {
        "label": "Engagement post — A/B/C poll, comment-bait CTA",
        "category": "engagement",
        "caption": """Be honest...

Do you check your business finances...
A) Weekly
B) Monthly
C) When you're stressed

It's Financial Literacy Month, so let's tighten up!

Money Moves to Make NOW:
Know your cash flow (don't guess)
Separate your accounts
Check your P&L like your IG insights
Track expenses yes, even that $9.99
Build business credit BEFORE you need it

WVF is here to help you get funded + stay ready 💪

👍 Comment A, B, or C - no judgment!""",
        "hashtags": [
            "#FinancialLiteracyMonth",
            "#MoneyTalk",
            "#EntrepreneurLife",
            "#WomenInBusiness",
            "#SmallBusinessTips",
            "#WVF",
        ],
    },
}


def list_instagram_templates() -> dict[str, str]:
    """Returns {template_key: label} for every real Instagram template —
    for populating a frontend picker, same pattern as
    keymakers_campaign.list_keymakers_stages()."""
    return {key: t["label"] for key, t in INSTAGRAM_TEMPLATES.items()}


def get_instagram_template(template_key: str) -> dict:
    """
    Returns one real Instagram template's full data (label, category,
    caption, hashtags). Raises KeyError with the valid options listed if
    template_key is unrecognized, matching
    keymakers_campaign.get_keymakers_stage()'s error shape.
    """
    template = INSTAGRAM_TEMPLATES.get(template_key)
    if template is None:
        raise KeyError(
            f"Unknown Instagram template '{template_key}'. Valid options: "
            f"{list(INSTAGRAM_TEMPLATES.keys())}"
        )
    return template
