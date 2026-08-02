"""
Standalone test script to verify content generation pipeline.
Run this to see real Claude API output before building the full UI.
"""

import asyncio
import json
from dotenv import load_dotenv

from app.schemas import EventInput
from app.services.generation import generate_all_content

# Load environment variables
load_dotenv()


# Real sample event from WVF's actual programming
SAMPLE_EVENT = EventInput(
    title="Money & Credit: Understanding Your Credit Report",
    date="July 16, 2024 at 2:00 PM ET",
    speaker="WVF Financial Education Team",
    registration_link="https://www.womenventurefund.org/events/money-credit-workshop",
    audience="NYC-based women entrepreneurs, aspiring business owners, Spanish-speaking community welcome",
    description="""Join us for a FREE bilingual workshop on understanding your credit report. 
    Learn how to read your credit report, identify and dispute errors, and improve your credit score 
    to become loan-ready. This workshop is perfect for entrepreneurs seeking funding or looking to 
    strengthen their financial foundation. No prior financial knowledge required — we'll break it 
    down step by step. Spanish interpretation available."""
)


async def main():
    print("=" * 60)
    print("WVF Content Generation Test")
    print("=" * 60)
    print(f"\n📋 Event: {SAMPLE_EVENT.title}")
    print(f"📅 Date: {SAMPLE_EVENT.date}\n")
    
    print("🔄 Generating content (calling Claude API concurrently)...\n")
    
    try:
        result = await generate_all_content(SAMPLE_EVENT)
        
        print("=" * 60)
        print("✅ SOCIAL POST")
        print("=" * 60)
        print(f"Caption:\n{result.social_post.caption}\n")
        print(f"Hashtags: {' '.join(result.social_post.hashtags)}\n")
        print(f"CTA: {result.social_post.cta}\n")
        print(f"Image Prompt: {result.social_post.suggested_image_prompt}\n")
        
        print("=" * 60)
        print("📌 HASHTAGS")
        print("=" * 60)
        print(f"Primary: {', '.join(result.hashtags.primary_hashtags)}")
        print(f"Topic-Specific: {', '.join(result.hashtags.topic_hashtags)}")
        print(f"Rationale: {result.hashtags.rationale}\n")
        
        print("=" * 60)
        print("📧 NEWSLETTER")
        print("=" * 60)
        print(f"Subject: {result.newsletter.subject_line}")
        print(f"Preview: {result.newsletter.preview_text}\n")
        print(f"Body:\n{result.newsletter.body}\n")
        print(f"CTA: {result.newsletter.cta_text} → {result.newsletter.cta_link}\n")

        print("=" * 60)
        print("🗞️  FLYER")
        print("=" * 60)
        print(f"Headline: {result.flyer.headline}")
        print(f"Subheadline: {result.flyer.subheadline}\n")
        print(f"Body:\n{result.flyer.body}\n")
        print(f"CTA: {result.flyer.cta}")
        print(f"Footer: {result.flyer.footer_details}\n")

        print("=" * 60)
        print("🗓️  CONTENT CALENDAR")
        print("=" * 60)
        print(f"Weeks: {result.calendar.weeks}")
        for entry in result.calendar.entries:
            print(f"  [{entry.day_label}] ({entry.platform}) {entry.post_idea} — {entry.cta}")
        print()

        print("=" * 60)
        print("✅ Generation Complete!")
        print("=" * 60)
        
        # Save to file for review
        with open("test_output.json", "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
        print("\n💾 Full output saved to test_output.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
