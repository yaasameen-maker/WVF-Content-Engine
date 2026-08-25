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

Full bio content (title/location/industry/key_quotes/story) added Aug
2026 for 4 of the 10 real Key Makers (LASweetsNY, TamiCo. Dancing
Company, Michelle Beauty Salon I & II, Living the Life I Dance About
Creations) — real testimonial/story content provided directly, not
generated or paraphrased. The other 6 don't have this content yet;
their bio fields stay None/unset, which the Profiles page renders as
"Bio pending," never fabricated or left blank. key_quotes is stored as
a JSON string (json.dumps of a list[str]) — see KeyMaker.key_quotes'
docstring in app/models/content.py for why (matches the JSON-in-Text
convention already used by ContentItem.body elsewhere in this codebase).

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

import json

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
        "title": "CEO",
        "location": "Harlem, New York",
        "industry": "Food / Culinary / Hospitality",
        "key_quotes": json.dumps(
            [
                "If you have the will and the desire to do what's in your heart, you can do it. "
                "It doesn't matter where you come from or what you have. I want the world to know that."
            ]
        ),
        "story": (
            "Loretta Calderon, CEO of LA Sweets NY in Harlem, began her entrepreneurial journey because "
            "she wanted to create something of her own. When she started, she didn't know where the "
            "journey would lead, but she held onto one thing throughout the process: faith.\n\n"
            "For Loretta, faith meant believing that she could overcome whatever challenges came her way. "
            "It meant trusting in God, believing in herself, and recognizing the people and opportunities "
            "that helped her along the journey. Over time, her perspective on challenges changed. Instead "
            "of seeing difficulties as obstacles designed to stop her, she began seeing them as lessons "
            "that could help her grow and keep moving forward.\n\n"
            "Her business is also deeply connected to her family and memories of home. The recipes she "
            "uses come from her mother, her sister, and the foods she grew up with. One of the most "
            "meaningful is her mother's coconut cake. She remembers watching her mother make it from "
            "scratch as a child, waiting to lick the bowl. Even after opening her business, Detta would "
            "still call her mother for guidance, asking, “Mom, how do I do this?” That connection "
            "to her family has become part of the heart and identity of her business.\n\n"
            "Another important part of Loretta's story is her relationship with Harlem. When she first "
            "started, she wasn't immediately sure what the larger mission of her business would be. But "
            "after being placed in the heart of Harlem, on 121st Street, she began to see her location as "
            "more than simply a place to operate a business. She came to understand it as a blessing and "
            "an opportunity to serve her community.\n\n"
            "Today, Loretta's story is about much more than building a business. It is about faith, "
            "family, resilience, purpose, and believing that your circumstances do not determine what you "
            "are capable of achieving.\n\n"
            "Core story/theme: Loretta transformed a desire to build something of her own into a "
            "purpose-driven business rooted in faith, family, and community. Her mother's recipes connect "
            "her business to her childhood and heritage, while her experience as an entrepreneur taught "
            "her to turn challenges into opportunities for growth. Her journey demonstrates that you don't "
            "need to know exactly where your path will lead—you need the faith and determination to "
            "take the next step.\n\n"
            "Key message: If you have the will and the desire to pursue what is in your heart, you can do "
            "it. Where you come from or what you have doesn't determine what you can build."
        ),
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
        "industry": "Dance education / Arts / Youth development",
        "key_quotes": json.dumps(
            [
                "I created TamiCo Dancing because I felt there was a lack of any arts programs in this "
                "community for students to be able to express themselves and have a different outlet.",
                "It's an honor for me to have that support and for them to feel that it was a safe place "
                "for them.",
            ]
        ),
        "story": (
            "Tamiko Maldonado founded Tamiko Dancing after recognizing a gap in arts education within her "
            "community. Having spent approximately six years teaching dance through the Board of "
            "Education, she saw firsthand how valuable dance and creative expression could be for "
            "students—and how limited access to arts programs was in her community.\n\n"
            "She created Tamiko Dancing to give students more than just dance lessons. She wanted to "
            "create a place where young people could express themselves, develop their skills, find "
            "mentorship, and feel safe and supported.\n\n"
            "Building the business was far from easy. Over roughly a decade, Tamiko experienced the "
            "uncertainty that comes with entrepreneurship, including days when she had no students and "
            "others when she had only a few. Without previous experience running a business, she had to "
            "learn as she went and take on every role the business required.\n\n"
            "What makes her especially proud is the long-term impact she has had on her community. "
            "Students who first came to her studio as middle schoolers have grown up, become parents, and "
            "now bring their own children to Tamiko Dancing. For Tamiko, this represents more than "
            "business success—it demonstrates that she created a place where generations of families "
            "felt welcomed, supported, and safe.\n\n"
            "Core story/theme: Tamiko turned a lack of arts opportunities in her community into a "
            "long-term community institution, using dance not only as an educational activity but also as "
            "a vehicle for self-expression, mentorship, safety, and connection across generations."
        ),
    },
    {
        "business_name": "Michelle Beauty Salon I & II",
        "owner_name": "Michelle",
        "business_type": "Beauty Salon",
        "website": None,
        "social_media": "WVF profile: https://womensventurefund.org/michelle-beauty-salon/",
        "photo_url": "https://womensventurefund.org/wp-content/uploads/2025/09/Michelle-pic.png",
        "industry": "Beauty and personal care",
        "key_quotes": json.dumps(
            [
                "I've learned to overcome obstacles. My inspiration was my sister. The key was my "
                "partner. And the continuation was what I enjoy doing.",
                "I learned about the loan, which helped me a lot to pave the way to my second salon.",
                "You always start from below, and if you are strong, you can do it.",
            ]
        ),
        "story": (
            "Her entrepreneurial journey began through inspiration from her sister, who already had her "
            "own business. Curious about entrepreneurship, she began asking questions about how she could "
            "start a business herself. With the encouragement and support of her partner, she leaped and "
            "opened her first salon.\n\n"
            "Starting the business was not easy. She experienced the uncertainty that comes with opening "
            "a business and not immediately having enough customers to cover the bills. Instead of "
            "allowing those challenges to stop her, she learned to battle through the difficult moments "
            "and keep moving forward.\n\n"
            "A major turning point came when she learned about business loans. Access to financing gave "
            "her the resources and confidence she needed to expand beyond her first location and open her "
            "second salon. For her, the loan wasn't simply financial support—it gave her the "
            "motivation to continue believing in what she was building.\n\n"
            "Her story is also deeply connected to creating opportunities for other women. She hopes that "
            "the women who work alongside her will eventually be able to establish businesses of their "
            "own, open new doors, and create their own paths to success.\n\n"
            "Core story/theme: Her journey is a story of inspiration, support, resilience, and growth. "
            "Her sister sparked the idea, her partner helped give her the courage to begin, and access to "
            "financing helped her expand. She represents the idea that entrepreneurs don't have to start "
            "with everything figured out—they can start small, learn along the way, and build their "
            "way forward.\n\n"
            "Key message: “Never give up, and never think it's too late to start. You may have to "
            "start from the bottom, but with strength and determination, you can build something bigger.”"
        ),
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
        "owner_name": "Althea Magloire",
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
        # Confirmed real photo of Yvonne (filename "Yvonne New photo_
        # 12_2022"), provided directly Aug 19 — replaces the earlier
        # candidate (a custom pillow product shot, no person) that was
        # reviewed and rejected. See module docstring.
        "photo_url": (
            "https://static.wixstatic.com/media/e1c06e_425d6ce43e214f94bbc66c4b2dbc498d~mv2.jpg/"
            "v1/crop/x_0,y_97,w_480,h_541/fill/w_546,h_616,al_c,lg_1,q_80,enc_avif,quality_auto/"
            "Yvonne%20New%20photo_%2012_2022.jpg"
        ),
        "industry": "Creative arts / Inspirational products / Handmade creations",
        "key_quotes": json.dumps(
            [
                "I was inspired to create something meaningful, spiritual, uplifting, and also "
                "comforting.",
                "My uniqueness is my audience.",
                "I'm most proud of having the privilege to have that special moment with an "
                "individual to create an experience for them on a pillow.",
            ]
        ),
        "story": (
            "Yvonne Williams Coston created Living the Life I Dance About Creations with the intention "
            "of making something that was more than simply a product. She wanted her work to be "
            "meaningful, spiritual, uplifting, and comforting, creating pieces that could connect with "
            "people on a deeper emotional level.\n\n"
            "One of her biggest challenges was finding the right audience. Yvonne realized that many of "
            "the venues where she showcased her work did not truly serve or understand her creativity. "
            "Instead of changing her work to fit those spaces, she eventually discovered something much "
            "more important: her uniqueness was the very thing that would attract the right audience.\n\n"
            "That realization came from an unexpected moment with a single customer. On a day when she "
            "had only one customer, the woman made a purchase and told Yvonne that what she was creating "
            "was beautiful and unique. She encouraged Yvonne to keep going, telling her that her work was "
            "changing people's lives.\n\n"
            "That interaction became a turning point. The customer gave Yvonne confirmation that she "
            "didn't need to appeal to everyone—she needed to connect with the people who truly "
            "understood and valued what she created. From there, Yvonne embraced her individuality and "
            "allowed her unique creativity to guide the direction of her business.\n\n"
            "Today, one of the things Yvonne is most proud of is the personal connection and experience "
            "she can create for each individual customer. Her work allows her to turn something as simple "
            "as a pillow into a meaningful, personal experience.\n\n"
            "Core story/theme: Yvonne's entrepreneurial journey is about embracing uniqueness rather than "
            "trying to fit into someone else's mold. A single customer's encouragement helped her "
            "recognize that the thing she once struggled to find an audience for was actually her "
            "greatest strength. Her business now centers on creating meaningful, comforting experiences "
            "that resonate with people on a personal and spiritual level."
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
