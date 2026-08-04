"""
Seeds the key_makers table with WVF's real 10 Key Makers — public-facing
fields only (business name, owner name, business type, public website/social
links WVF already publishes about these clients).

Deliberately excludes personal phone numbers, personal emails, and
unconfirmed street addresses — this file is committed to git, and that data
should never enter version control. See CLAUDE.md for the reasoning.

Run manually against a provisioned database:
    cd backend && python seed_key_makers_public.py

Testimonial quotes are left as placeholders until Nancy sends real
testimonial content (see docs/PROJECT_CONTEXT.md Action Items).
"""

from app.database import SessionLocal
from app.models import KeyMaker

KEY_MAKERS = [
    {
        "business_name": "LASweetsNY",
        "owner_name": "Loretta Calderon",
        "business_type": "Bakery / Catering",
        "website": "https://lasweetsny.com/",
        "social_media": "Instagram: https://www.instagram.com/lasweetsny/",
    },
    {
        "business_name": "TamiCo. Dancing Company",
        "owner_name": "Tamiko Maldonado",
        "business_type": "Dance Education",
        "website": "https://www.tamicodancing.com/",
        "social_media": (
            "Instagram: https://www.instagram.com/tamicodancing/ | "
            "Facebook: https://www.facebook.com/tamicodancing/"
        ),
    },
    {
        "business_name": "Michelle Beauty Salon I & II",
        "owner_name": "Michelle",
        "business_type": "Beauty Salon",
        "website": None,
        "social_media": "WVF profile: https://womensventurefund.org/michelle-beauty-salon/",
    },
    {
        "business_name": "Kwick Check Cashing",
        "owner_name": "Francis D'Amore",
        "business_type": "Financial Services",
        "website": "https://www.kwikcheckcashing.com/",
        "social_media": None,
    },
    {
        "business_name": "Nurture Postnatal Care",
        "owner_name": "Amina Cush",
        "business_type": "Postpartum Care",
        "website": "https://www.nurture-care.co/",
        "social_media": "Instagram: https://www.instagram.com/nurturepostnatalcare/",
    },
    {
        "business_name": "Althea's Tropical Delights",
        "owner_name": "Althea",
        "business_type": "Food / Bakery",
        "website": "https://www.altheastropicaldelights.com/",
        "social_media": (
            "Instagram: https://www.instagram.com/altheastropicaldelights/ | "
            "Facebook: https://www.facebook.com/altheabakes/"
        ),
    },
    {
        "business_name": "Meow Cleeva",
        "owner_name": "Martha Colón",
        "business_type": "Art / Home Décor / Gifts",
        "website": "https://www.meowcleeva.art/",
        "social_media": "Instagram: https://www.instagram.com/meow_cleeva/",
    },
    {
        "business_name": "Venus Cannabis Shop",
        "owner_name": "Gina Candelario",
        "business_type": "Cannabis Retail Shop",
        "website": None,
        "social_media": "Instagram: https://www.instagram.com/venuscannabis/",
    },
    {
        "business_name": "Pink Nail Beauty Lounge",
        "owner_name": "Glady Garcia",
        "business_type": "Nail / Beauty Services",
        "website": None,
        "social_media": "Instagram: https://www.instagram.com/pinkbeauty_naillounge/",
    },
    {
        "business_name": "Living the Life I Dance About Creations",
        "owner_name": "Yvonne Williams Coston",
        "business_type": "Custom Inspirational Gifts",
        "website": "https://www.livingthelifeidanceabout.com/",
        "social_media": (
            "Instagram: https://www.instagram.com/livingthelifeidanceabout/ | "
            "Facebook: https://www.facebook.com/LTLIDAPillows123 | "
            "LinkedIn: https://www.linkedin.com/in/yvonne-williams-coston-mba-11967210"
        ),
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = {km.business_name for km in db.query(KeyMaker).all()}
        added = 0
        for entry in KEY_MAKERS:
            if entry["business_name"] in existing:
                continue
            db.add(KeyMaker(**entry))
            added += 1
        db.commit()
        print(f"Seeded {added} new Key Makers ({len(KEY_MAKERS) - added} already present).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
