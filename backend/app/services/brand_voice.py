"""
WVF Brand Voice Reference
Compiled from Instagram, LinkedIn, and Facebook screenshots
"""

# Official hashtag set observed across all platforms
WVF_HASHTAGS = [
    "#WomensVentureFund",
    "#WVFWomenEntrepreneurs",
    "#SmallBusinessSupport",
    "#WomenInBusiness",
    "#Entrepreneurship",
    "#NYCSmallBusiness",
    "#WVFCDFI",
    "#BusinessGrowth",
    "#LoanReady",
    "#CreditEducation",
    "#BusinessFunding",
    "#FinancialLiteracy",
    "#NYCBusiness",
]

# Tone and style guidelines derived from real posts
TONE_GUIDELINES = """
- Direct and benefit-forward — lead with what the audience gets
- Inclusive, warm, but professional (not overly casual)
- CTA-driven: every post ends with "Register Now", "Apply Today", "Learn More", etc.
- Emoji usage varies by platform — real WVF Facebook posts use emoji heavily and structurally
  (a checkmark on every checklist line, an emoji label on every logistics line: 📅 date, 🕐 time,
  📍 location, 💻 virtual), not just as rare urgency/date/goal markers. Match the density shown
  in the platform-specific examples/instructions for the content type being generated — do not
  default to using emoji sparingly unless the specific platform/format calls for it.
- Emphasizes accessibility: free events, bilingual services, no credit score requirements
- Community-focused: highlights partners, success stories, and collective growth
"""

# Example posts for few-shot learning
EXAMPLE_POSTS = [
    {
        "type": "workshop_promo",
        "caption": """🚨 Mark Your Calendar!

Join us for "Money & Credit: Understanding Your Credit Report" — a FREE bilingual workshop on July 16th at 2pm ET.

Learn how to:
✅ Read your credit report
✅ Spot and fix errors
✅ Improve your credit score

Perfect for entrepreneurs getting loan-ready! 

📅 July 16, 2pm ET
🔗 Register: [link]

#WomensVentureFund #CreditEducation #LoanReady #NYCSmallBusiness""",
    },
    {
        "type": "funding_announcement",
        "caption": """🎯 Need capital to grow your business?

WVF offers loans from $5K-$250K with:
• No minimum credit score required
• Free 1-on-1 technical assistance
• Support before, during, and after funding

We believe in you. Let's build together.

Apply today: [link]

#WomensVentureFund #BusinessFunding #WomenInBusiness #WVFCDFI""",
    },
    {
        "type": "event_recap",
        "caption": """Thank you to everyone who joined our Financial Literacy Month panel! 🙌

Special thanks to our partners at [Partner Org] for co-hosting this important conversation about building wealth in our communities.

Missed it? Access the recording: [link]

#WomensVentureFund #FinancialLiteracy #CommunitySupport #NYCBusiness""",
    },
]

# Visual/design conventions (for future image generation)
# Hex values estimated from a screenshot of WVF's real July 2026 newsletter —
# not pixel-picked from a source file. Update once the team exports real
# logo/brand files (see docs/PROJECT_CONTEXT.md Brand Assets).
VISUAL_STYLE = """
- Brand colors: Navy blue primary (#4A7EBB), sky/steel blue secondary (#87ACD1), white background/contrast (#FFFFFF)
- Concentric circle texture pattern as a subtle recurring background motif
- Leaf/sprout icon (three-leaf plant growing upward) as a recurring brand mark
- Bold, blocky sans-serif for headlines; clean sans-serif for body/nav
- Consistent header banner style with WVF logo
- Clean, professional layout — not overly decorative
- Text overlays are readable (high contrast, simple fonts)
- Photos feature real entrepreneurs when possible
"""


def get_brand_voice_context() -> str:
    """
    Returns the complete brand voice reference as a string for prompt injection.
    """
    hashtags_str = ", ".join(WVF_HASHTAGS)
    examples_str = "\n\n---\n\n".join(
        [f"**Example {i+1} ({ex['type']})**\n{ex['caption']}" for i, ex in enumerate(EXAMPLE_POSTS)]
    )

    return f"""
# Women's Venture Fund (WVF) Brand Voice

## Official Hashtags
{hashtags_str}

## Tone & Style
{TONE_GUIDELINES}

## Example Posts
{examples_str}

## Visual Style
{VISUAL_STYLE}
"""
