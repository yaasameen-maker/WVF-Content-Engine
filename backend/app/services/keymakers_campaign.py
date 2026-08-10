"""
WVF Keymakers Campaign — Real Reference Copy

The "Keymakers" initiative (distinct from Felix/GHL's 4 audience personas —
see docs/PROJECT_CONTEXT.md Open Questions) recruits past and prospective
WVF clients to record video testimonials answering "What was your key?" —
the person, decision, relationship, resource, or turning point that changed
what was possible for their business. Selected stories feed the Member
Spotlight newsletter block (see newsletter_blocks.py /
build_member_spotlight_prompt) once Nancy provides real testimonial
content.

Source: real WVF/Maria Otero copy (4-email recruitment drip: initial invite
+ 3 follow-ups at day 4/9/15), provided August 7, 2026. Two audience
variants exist — "Current WVF Clients" and "Cold List of Entrepreneurs" —
with original/revised copy pairs. Every message requires Maria's approval
before sending; this file is a *reference* for tone/structure, not
send-ready copy staff can use unreviewed.

This is deliberately NOT merged into brand_voice.py's EXAMPLE_POSTS —
those are evergreen, always-injected brand voice; this is a specific,
time-bound campaign with its own sequencing rules. Exposed as its own
context function so callers opt in explicitly (e.g. when generating
Keymakers-specific newsletter/eblast content) rather than it silently
influencing every generation call.
"""

# Two email sequences (4 messages each: initial + 3 follow-ups), by audience.
# Only the most-recent "Revised Message" is kept here — see the source
# .docx files (WVF SMB/Revised Current WVF Messages.docx and
# WVF SMB/EBlast Copy/.../Revised New Client.docx) for original-vs-revised
# diffs if that history is ever needed.

KEYMAKERS_SEQUENCE_CURRENT_CLIENTS = [
    {
        "stage": "initial",
        "send_day": 0,
        "subject_options": None,  # not specified for the initial send in source material
        "body": """Hello [First Name],
Every business has a door that once seemed impossible to open.
[KEYMAKERS VISUAL]
Women's Venture Fund is building Keymakers—a community designed to help more women entrepreneurs find those doors and walk through them. We are starting with the women who know firsthand what that journey really takes.
As someone who has been part of the WVF community, we invite you to answer one simple question:
What was your key?
The person, decision, relationship, resource, or turning point that changed what was possible for your business.
We would love to hear your answer and the story behind it through a brief recorded conversation. Your words and experience can help another woman recognize an opportunity, overcome a challenge, or take her next step with greater confidence.
[SHARE YOUR KEY]
The knowledge women gain while building their businesses should not disappear. Keymakers is creating a place where those stories, insights, relationships, and resources can be shared to support the women who come next.
A recorded conversation is not the only way to participate. You can also visit the Keymakers page to nominate another woman whose story should be heard, join us at the fall gathering, or become part of a growing community of entrepreneurs sharing stories, knowledge, connections, and opportunities.
[VISIT KEYMAKERS]
The doors women have already opened can become pathways for the women coming next.
Warmly,
Maria Otero
Founder and President
Women's Venture Fund""",
    },
    {
        "stage": "follow_up_1",
        "send_day": 4,
        "send_condition": "Only to contacts who did not reply, did not complete the Share Your Key form, did not opt out, and did not bounce.",
        "subject_options": [
            "What was the key for your business?",
            "We would like to include your story",
            "A quick Keymakers follow-up",
        ],
        "body": """Hello [First Name],
We wanted to follow up on our recent invitation because we'd truly love to hear your story.
Every entrepreneur has a moment, person, opportunity, or decision that helped move their business forward. We call that your key.
What was your key?
We're inviting members of the WVF community to share theirs through a brief, guided conversation. There's nothing to prepare, and no speech is required—we simply want to learn from your experience.
[SHARE YOUR KEY]
Your story has the potential to encourage, inform, and open doors for other women entrepreneurs while becoming part of a growing community built on shared knowledge, meaningful connections, and real experiences.
[VISIT KEYMAKERS]
We hope you'll join us.
Warmly,
Maria Otero
Founder and President
Women's Venture Fund""",
    },
    {
        "stage": "follow_up_2",
        "send_day": 9,
        "send_condition": (
            "Send a different reason to participate — emphasize one of: their experience "
            "may help another entrepreneur; selected stories will become part of the first "
            "Keymakers collection; participation requires no speech or preparation; they can "
            "participate in ways other than recording a story."
        ),
        "subject_options": [
            "Another woman may need what you learned",
            "Your experience belongs in Keymakers",
            "The knowledge behind the business",
        ],
        "body": """Hello [First Name],
Every woman who builds a business learns lessons that can't be found in a book.
Sometimes it's the introduction that led to a first customer. The decision that changed everything. The resource that arrived at the right moment. Or the mistake that became the most valuable lesson of all.
Too often, those experiences stay with one person. Keymakers is being built so they don't.
By sharing your story through a brief, guided conversation, you can help another entrepreneur recognize an opportunity, avoid a costly mistake, or take her next step with greater confidence.
You can share your key through a short recorded conversation:
[SHARE YOUR KEY]
If recording a conversation isn't the right fit, there are other ways to be part of Keymakers. You can nominate another woman entrepreneur, join us at the fall gathering, or stay connected as the Keymakers community grows.
[VISIT KEYMAKERS]
Thank you for helping build a community where women learn from one another.
Warmly,
Maria Otero
Founder and President
Women's Venture Fund""",
    },
    {
        "stage": "final_follow_up",
        "send_day": 15,
        "send_condition": (
            "Brief closing message. Do not use false urgency — explain that WVF is "
            "completing the first group of Keymaker interviews or preparing the initial "
            "collection."
        ),
        "subject_options": [
            "Final invitation for the first Keymakers collection",
            "We hope your story will be included",
            "One last Keymakers invitation",
        ],
        "body": """Hello [First Name],
As we prepare the first Keymakers collection, we wanted to extend one final invitation to members of the WVF community.
Every business has a story behind it—a person, relationship, decision, resource, or turning point that changed what became possible. We'd be honored to include yours.
If you're willing to share your key, we'll guide you through a brief, recorded conversation. There's nothing to prepare—we simply want to hear your experience in your own words.
[SHARE YOUR KEY]
If now isn't the right time, you can still be part of Keymakers by nominating another woman entrepreneur or exploring other ways to get involved.
[VISIT KEYMAKERS]
Thank you for being part of the Women's Venture Fund community. We hope you'll stay connected as Keymakers grows and continues to bring women entrepreneurs together through shared stories, knowledge, and opportunity.
Warmly,
Maria Otero
Founder and President
Women's Venture Fund""",
    },
]

KEYMAKERS_SEQUENCE_COLD_LIST = [
    {
        "stage": "initial",
        "send_day": 0,
        "subject_options": None,
        "body": """Hello [First Name],
Women entrepreneurs hear plenty of success stories. What they rarely hear is what actually made the difference.
The introduction that led to a major customer. The financing that arrived at the right moment. The lesson learned after an expensive mistake. The person who explained how the system really worked. The decision that changed the course of the business.
Businesses grow through more than individual effort. They grow through trusted relationships, candid advice, timely introductions, and knowledge shared behind the scenes. Yet women entrepreneurs have had limited access to the networks where those opportunities are created and shared.
Women's Venture Fund is building Keymakers - a community where women can share the stories, knowledge, relationships, resources, and opportunities that help businesses move forward.
We are beginning with one simple question:
What was your key?
The person, decision, relationship, resource, or turning point that changed what was possible for your business.
We would love to hear your answer through a brief, guided recorded conversation. No speech or preparation is required. We simply want to hear what made the difference, in your own words.
Selected stories will become part of the first Keymakers collection, helping women entrepreneurs discover what truly moves businesses forward and connect with others willing to share what they have learned.
[SHARE YOUR KEY]
For nearly three decades, Women's Venture Fund has worked alongside women entrepreneurs by providing financing, practical guidance, and meaningful business connections.
[Learn more about Women's Venture Fund.]
The knowledge women gain while building their businesses should not end with them. Keymakers is creating a place where those experiences can inspire, guide, and support the women who come next.
A recorded conversation is only one way to participate. You can also visit the Keymakers page to nominate another woman whose story should be heard, join us at the fall gathering, or become part of a growing community of entrepreneurs sharing stories, knowledge, resources, and opportunities.
[VISIT KEYMAKERS]
We are now selecting the first group of Keymaker stories. We hope yours will be one of them.
Warmly,
Maria Otero
Founder and President
Women's Venture Fund""",
    },
]
# Note: only the initial-touch "Cold List of Entrepreneurs" message was
# provided as distinct source copy; the day 4/9/15 follow-ups for this
# audience were not included in the source material. Reuse the Current
# Clients follow-up structure/timing if a cold-list drip is needed, but
# confirm wording with Maria before sending — cold-list framing differs
# ("we invite you to answer" vs. the current-client "as someone who has
# been part of the WVF community").


# Stable, dropdown-friendly registry of every individual message, keyed by
# a single stage_key — this is what the newsletter generator's Keymakers
# toggle selects from (one message per generation call, not the whole
# sequence at once). "label" is what a frontend dropdown should show.
KEYMAKERS_STAGES: dict[str, dict] = {
    "current_clients_initial": {
        "label": "Initial invite — Current WVF Clients",
        "audience": "Current WVF Clients",
        **KEYMAKERS_SEQUENCE_CURRENT_CLIENTS[0],
    },
    "current_clients_follow_up_1": {
        "label": "Day 4 follow-up — Current WVF Clients",
        "audience": "Current WVF Clients",
        **KEYMAKERS_SEQUENCE_CURRENT_CLIENTS[1],
    },
    "current_clients_follow_up_2": {
        "label": "Day 9 follow-up — Current WVF Clients",
        "audience": "Current WVF Clients",
        **KEYMAKERS_SEQUENCE_CURRENT_CLIENTS[2],
    },
    "current_clients_final_follow_up": {
        "label": "Day 15 final follow-up — Current WVF Clients",
        "audience": "Current WVF Clients",
        **KEYMAKERS_SEQUENCE_CURRENT_CLIENTS[3],
    },
    "cold_list_initial": {
        "label": "Initial invite — Cold List of Entrepreneurs",
        "audience": "Cold List of Entrepreneurs",
        **KEYMAKERS_SEQUENCE_COLD_LIST[0],
    },
}

KEYMAKERS_CENTRAL_QUESTION = "What was your key?"
KEYMAKERS_CENTRAL_QUESTION_SUBTEXT = (
    "The person, decision, relationship, resource, or turning point that "
    "changed what was possible for your business."
)

KEYMAKERS_APPROVAL_NOTE = (
    "All Keymakers messages require approval from Maria before sending — "
    "this reference copy is for tone/structure, not send-ready output."
)


def get_keymakers_campaign_context() -> str:
    """
    Returns the Keymakers recruitment campaign as a string for prompt
    injection — for generating Keymakers-specific content (e.g. an eblast
    inviting Key Makers to share their story), not for general brand voice.
    Callers opt in explicitly; this is not part of get_brand_voice_context().
    """
    current_clients_str = "\n\n---\n\n".join(
        f"**{msg['stage']} (day {msg['send_day']})**"
        + (f"\nSubject options: {', '.join(msg['subject_options'])}" if msg.get("subject_options") else "")
        + f"\n\n{msg['body']}"
        for msg in KEYMAKERS_SEQUENCE_CURRENT_CLIENTS
    )

    return f"""
# WVF Keymakers Recruitment Campaign (reference)

## Central Question
{KEYMAKERS_CENTRAL_QUESTION}
{KEYMAKERS_CENTRAL_QUESTION_SUBTEXT}

## Approval
{KEYMAKERS_APPROVAL_NOTE}

## Current-Clients Sequence (4 messages: initial + follow-ups at day 4, 9, 15)
{current_clients_str}
"""


def list_keymakers_stages() -> dict[str, str]:
    """Returns {stage_key: label} for every individual Keymakers message —
    for populating a frontend dropdown, same pattern as
    prompts.list_variants()."""
    return {key: stage["label"] for key, stage in KEYMAKERS_STAGES.items()}


def get_keymakers_stage_context(stage_key: str) -> str:
    """
    Returns ONE selected Keymakers message as prompt-injection context —
    the reference copy for a single stage (e.g. "current_clients_initial"),
    not the whole sequence. Raises KeyError with the valid options listed
    if stage_key is unrecognized, so callers get an actionable error
    instead of a silent empty prompt.
    """
    stage = KEYMAKERS_STAGES.get(stage_key)
    if stage is None:
        raise KeyError(
            f"Unknown Keymakers stage '{stage_key}'. Valid options: "
            f"{list(KEYMAKERS_STAGES.keys())}"
        )

    subject_line = (
        f"\nSubject options: {', '.join(stage['subject_options'])}"
        if stage.get("subject_options")
        else ""
    )
    send_condition = (
        f"\nSend condition: {stage['send_condition']}" if stage.get("send_condition") else ""
    )

    return f"""
# WVF Keymakers Recruitment Campaign — Reference Message

## Central Question
{KEYMAKERS_CENTRAL_QUESTION}
{KEYMAKERS_CENTRAL_QUESTION_SUBTEXT}

## Approval
{KEYMAKERS_APPROVAL_NOTE}

## Selected Stage: {stage['label']}
Audience: {stage['audience']} | Stage: {stage['stage']} (day {stage['send_day']}){subject_line}{send_condition}

## Reference Copy
{stage['body']}
"""
