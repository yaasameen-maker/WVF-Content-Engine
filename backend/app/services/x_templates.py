"""
WVF X (Twitter) — Real Post Templates

Actual published @WomensVFund X posts, transcribed from a full account
audit of x.com/WomensVFund covering the account's current active
campaign period (Mar 24, 2026 – Sep 9, 2026; posts before that are
2020-2021 text/link posts with no flyer graphics — not included). Used
as "Fixed template" starting points on the event-form page — staff pick
one and use/edit it directly, with no AI call involved. Distinct from AI
Copy generation (app/services/prompts.py's "x" SOCIAL_POST_VARIANTS
entry), which today uses only generic platform conventions since it
wasn't yet grounded in these real posts — see the note in prompts.py for
updating that once these are cross-referenced.

Every entry below is real, published copy — not written or paraphrased.
Replaces an earlier, thinner batch transcribed from screenshots (several
fields truncated with "..." where a screenshot cut off a long URL/
hashtag string) — this audit pulled full, untruncated text directly
from the live posts, so `truncated` is no longer needed as a field.

Not every audited post became a template:
- Two posts (May 22 and one Mar 24 "earlier version") were a same-day
  duplicate/reply of another post with no independent content — skipped.
- The Sep 9 carousel post's own tweet caption is used as
  `harlem_legacy_investment_suite_carousel` below; its three flyer
  SLIDES (a workshop, a conference, and a gala) are richer than a
  single X caption needs and are closer to newsletter/flyer-block
  material — not transcribed here, since this file is X captions only.

Several posts (attorney consultations, a state senator's district
office) name real private individuals/offices beyond WVF's own Key
Makers — kept here as historical record of what WVF already published
publicly on X, not re-verified or re-cleared for reuse beyond that.
"""

X_TEMPLATES: dict[str, dict] = {
    "harlem_legacy_investment_suite_carousel": {
        "label": "Event promo — carousel, 3 September events",
        "category": "event_promo",
        "caption": """Meet WVF this September: Harlem Legacy Investment Suite 9/20, Cash Flow with Chase 9/23, and SCORE NYC's Business Conference 9/29.

womensventurefund.org/events/""",
        "hashtags": ["#WVF", "#NYCEntrepreneurs"],
    },
    "business_next_chapter_loan_inquiry": {
        "label": "Evergreen — loan inquiry CTA, no event date",
        "category": "evergreen",
        "caption": """Your Business Deserves a Next Chapter. ❤️

You believed in your business. So do we. Ready to grow?

WVF wants to hear from women entrepreneurs with established businesses and a vision for what's next.

👉 Start your WVF Loan Inquiry: womensventurefund.org/womens-business-loan-inquiry""",
        "hashtags": ["#loanapps", "#smallbiz"],
    },
    "government_contracting": {
        "label": "Event promo — MWBE certification / government contracting webinar",
        "category": "event_promo",
        "caption": """🚨 Don't Leave Money on the Table!

Learn how to become #MWBE Certified and compete for government contracts.

📅 Wednesday, July 29, 2026 | 🕚 11 AM ET

🎟️ Register NOW: us06web.zoom.us/webinar/registration""",
        "hashtags": [
            "#MWBE",
            "#GovernmentContracts",
            "#SmallBusiness",
            "#WomenEntrepreneurs",
            "#WomensVentureFund",
        ],
    },
    "legal_help_10_spots": {
        "label": "Event promo — free legal consultation, urgency framing",
        "category": "event_promo",
        "caption": """🚨 ONLY 10 SPOTS LEFT! 🚨

Need legal help for your business? Get a one-on-one consultation with volunteer attorneys through the City Bar Justice Center.

✅ Contracts
✅ Leases
✅ Business issues

📅 June 25

Register now before spots are gone: us06web.zoom.us/webinar/registration""",
        "hashtags": ["#WVF"],
    },
    "lunch_and_apply_funding": {
        "label": "Event promo — recurring \"Lunch & APPLY\" funding sessions",
        "category": "event_promo",
        "caption": """WVF IS FUNDING! 🚨

Women entrepreneurs are you ready to grow? Join WVF's virtual 'Lunch & APPLY' sessions to position your business for funding, expansion, working capital & growth. 💼📈

📅 May 29 | June 30 | July 30
⏰ 12PM ET

🔗 Register now""",
        "hashtags": ["#WVF", "#WVFsmallbusinessmonth"],
    },
    "money_matters_cash_flow_lenders": {
        "label": "Event promo — \"Money Matters\", lender-focused hook",
        "category": "event_promo",
        "caption": """Many entrepreneurs focus on sales — but lenders focus on numbers. 📊💰

Understanding cash flow, budgeting, and P&L statements can help position your business for funding opportunities.

Join WVF + NYWIB for 'Money Matters' on May 19.

Register: us06web.zoom.us/webinar/registration""",
        "hashtags": [],
    },
    "money_matters_funding_ready": {
        "label": "Event promo — \"Money Matters\", checklist + emoji markers",
        "category": "event_promo",
        "caption": """🚨 WVF IS FUNDING 🚨

Are you funding ready? Join WVF & NYWIB for 💰 MONEY MATTERS and learn:

✔️ Cash Flow
✔️ Profit & Loss
✔️ Budgeting
✔️ Funding Readiness

📅 May 19
⏰ 11AM EST
💻 FREE Zoom Webinar

Register now: us06web.zoom.us/webinar/registration""",
        "hashtags": ["#SmallBizMonth", "#WVF", "#NYWIB", "#GetFunded"],
    },
    "ai_marketing_webinar_today": {
        "label": "Event promo — AI marketing webinar, happening-today reminder",
        "category": "event_promo",
        "caption": """🚨 TODAY 11 AM 🚨

Stop overworking your marketing. Learn how to use AI tools to:

✔ Create content FAST
✔ Automate your marketing
✔ Grow your business smarter

🎯 1-hour LIVE training
🔥 Don't miss this

👉 us06web.zoom.us/webinar/registration""",
        "hashtags": [],
    },
    "financial_literacy_poll_know_your_numbers": {
        "label": "Engagement post — A/B/C poll, Financial Literacy Month",
        "category": "engagement",
        "caption": """Be honest… Do you know your business numbers RIGHT NOW?

A) Yes
B) Kinda
C) No

It's #FinancialLiteracyMonth - time to level up:
• Track cash flow
• Know your P&L
• Separate finances
• Build credit

Comment A, B, or C""",
        "hashtags": [
            "#FinancialLiteracyMonth",
            "#WVFSmallBusiness",
            "#EntrepreneurLife",
            "#MoneyMatters",
        ],
    },
    "harlem_financial_literacy_pop_up": {
        "label": "Event promo — Harlem community pop-up, Financial Literacy Month",
        "category": "event_promo",
        "caption": """JOIN US!!!

You don't know what you don't know… 💡

Come Learn WVF will be in Harlem for Financial Literacy Month sharing resources for:
✔ Credit
✔ Capital
✔ Small Business Growth

📍 April 25 | 12–3 PM
📍 163 W 125th St

Don't miss it. us06web.zoom.us/webinar/registration""",
        "hashtags": ["#WVFEntrepreneur"],
    },
    "financial_literacy_month_awareness": {
        "label": "Awareness post — Financial Literacy Month, no single event",
        "category": "awareness",
        "caption": """April is Financial Literacy Month 💡

Strong businesses are built on:
✔️ Cash flow
✔️ Credit
✔️ Capital access

WVF helps entrepreneurs grow with training + funding pathways.

us06web.zoom.us/webinar/registration""",
        "hashtags": ["#FinancialLiteracyMonth", "#SmallBusiness", "#WVF"],
    },
    "ai_marketing_webinar_announcement": {
        "label": "Event promo — AI marketing webinar, full announcement",
        "category": "event_promo",
        "caption": """🚨 Don't miss this during #FinancialLiteracyMonth!

Use AI to:
✔ Save time
✔ Simplify marketing
✔ Grow your business

📅 April 29th 12PM - 1PM
💻 Webinar

👉Register Today us06web.zoom.us/webinar/registration""",
        "hashtags": [
            "#FinancialLiteracyMonth",
            "#WVFSmallBusiness",
            "#WomenEntrepreneurs",
            "#AItools",
        ],
    },
    "the_plan_fell_apart_panel": {
        "label": "Event promo — founder panel, Eventbrite link",
        "category": "event_promo",
        "caption": """When the plan stops working, what do you do next?

When the Plan Fails: What Actually Works Next. We're bringing together women founders to share what actually helped them move forward - in real business and career turning points.

March 30 👉 eventbrite.com/the-plan-fell-apart-now-what""",
        "hashtags": [],
    },
    # NOT a real published X post like the entries above — new copy for
    # an upcoming event (Sept 23, 2026), written from the event flyer,
    # not transcribed from x.com/WomensVFund. Kept here (rather than a
    # separate "unpublished" file) since staff need it in the same
    # Fixed-template picker; flag it here if this file's scope is ever
    # audited again.
    "navigating_cash_flow_chase_workshop": {
        "label": "Event promo — Navigating Cash Flow workshop w/ Chase (Sept 23)",
        "category": "event_promo",
        "caption": """Cash flow is about more than tracking what comes in and goes out. Join Women's Venture Fund and Chase for an in-person workshop on practical ways to manage expenses, anticipate financial challenges, and make informed decisions for your business.

Whether you're launching a business or running an established one, Navigating Cash Flow will help you build strategies for greater financial stability and growth.

📍 JPMorgan Chase Harlem Community Branch, 55 West 125th Street, New York, NY 10027
📅 September 23, 2026 | 5–7 PM

Space is limited. Register in advance: Workshop registration""",
        "hashtags": [],
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
    hashtags). Raises KeyError with the valid options listed if
    template_key is unrecognized, matching
    instagram_templates.get_instagram_template()'s error shape.
    """
    template = X_TEMPLATES.get(template_key)
    if template is None:
        raise KeyError(
            f"Unknown X template '{template_key}'. Valid options: "
            f"{list(X_TEMPLATES.keys())}"
        )
    return template
