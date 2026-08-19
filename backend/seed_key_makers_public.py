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

photo_url sourcing (Aug 2026): pulled from each business's own real
website/social page, confirmed business-by-business with Yaasameen rather
than auto-matched, since URL/domain alone wasn't always enough to confirm
which business a given image belonged to. Two categories:
  - Direct hosted image URLs (Wix/Shopify/WVF site CDNs) — stable, no
    expiry, used as-is.
  - Local files under frontend/public/key-makers/ for the 3 businesses
    with no usable photo of the owner (LASweetsNY, Venus Cannabis, Pink
    Nail Beauty Lounge) — their real Instagram profile photos are served
    from signed, expiring CDN URLs (cdninstagram.com ?oe=... tokens) that
    would 404 within days/weeks, so their real logo images were saved
    locally instead. These are brand logos, not owner photos — a
    deliberate content-type mismatch with the other 7 entries, acceptable
    per Yaasameen's Aug 19 decision to use them anyway rather than leave
    those 3 with no image at all.
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
        # Real Instagram profile photo is served from a signed, expiring
        # CDN URL — logo saved locally instead. See module docstring.
        "photo_url": "/key-makers/la-sweets-ny.png",
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
        "photo_url": "https://www.tamicodancing.com/wp-content/uploads/2019/11/gallery-4.jpg",
    },
    {
        "business_name": "Michelle Beauty Salon I & II",
        "owner_name": "Michelle",
        "business_type": "Beauty Salon",
        "website": None,
        "social_media": "WVF profile: https://womensventurefund.org/michelle-beauty-salon/",
        "photo_url": "https://womensventurefund.org/wp-content/uploads/2025/09/Michelle-pic.png",
    },
    {
        "business_name": "Kwick Check Cashing",
        "owner_name": "Francis D'Amore",
        "business_type": "Financial Services",
        "website": "https://www.kwikcheckcashing.com/",
        "social_media": None,
        "photo_url": "https://www.kwikcheckcashing.com/wp-content/uploads/2018/07/contact-header-img01.jpg",
    },
    {
        "business_name": "Nurture Postnatal Care",
        "owner_name": "Amina Cush",
        "business_type": "Postpartum Care",
        "website": "https://www.nurture-care.co/",
        "social_media": "Instagram: https://www.instagram.com/nurturepostnatalcare/",
        "photo_url": (
            "https://images.squarespace-cdn.com/content/v1/660e3a953d827820df5fcf61/"
            "d8dfa362-9e0d-4eb5-8366-01bf1d993b71/IMG_6446+4.JPG?format=750w"
        ),
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
        # Confirmed against altheastropicaldelights.com/about-us — this is
        # the teal-dress photo of Althea herself. See module docstring.
        "photo_url": (
            "https://static.wixstatic.com/media/4be789_b8d78e11b9314ae58ea0695a3e9aef79~mv2_d_1200_1600_s_2.jpg/"
            "v1/crop/x_284,y_243,w_916,h_1357/fill/w_626,h_928,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,"
            "quality_auto/IMG-20190522-WA0072.jpg"
        ),
    },
    {
        "business_name": "Meow Cleeva",
        "owner_name": "Martha Colón",
        "business_type": "Art / Home Décor / Gifts",
        "website": "https://www.meowcleeva.art/",
        "social_media": "Instagram: https://www.instagram.com/meow_cleeva/",
        "photo_url": "https://cdn.shopify.com/s/files/1/0313/5556/8259/files/Martha_Colon_artist_nyc_2025.png?v=1758060346",
    },
    {
        "business_name": "Venus Cannabis Shop",
        "owner_name": "Gina Candelario",
        "business_type": "Cannabis Retail Shop",
        "website": None,
        "social_media": "Instagram: https://www.instagram.com/venuscannabis/",
        # Real Instagram profile photo is served from a signed, expiring
        # CDN URL — logo saved locally instead. See module docstring.
        "photo_url": "/key-makers/venus-cannabis.png",
    },
    {
        "business_name": "Pink Nail Beauty Lounge",
        "owner_name": "Glady Garcia",
        "business_type": "Nail / Beauty Services",
        "website": None,
        "social_media": "Instagram: https://www.instagram.com/pinkbeauty_naillounge/",
        # Real Instagram profile photo is served from a signed, expiring
        # CDN URL — logo saved locally instead. See module docstring.
        "photo_url": "/key-makers/pink-beauty.png",
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
        # NOTE (Aug 19): this Wix URL was mistakenly assigned to Althea
        # first, then corrected once her own About page confirmed it was
        # actually her photo. This candidate photo of Yvonne (a custom
        # pillow product shot, no person) was previously reviewed and
        # rejected — Yvonne has no confirmed real photo yet. See module
        # docstring; revisit once a real photo of Yvonne is sourced.
        "photo_url": None,
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
