"""
Core generation logic using Claude API with structured outputs (tool use).
Calls all three content generators concurrently via asyncio.gather.
"""

import asyncio
import json
import os
from typing import Any

import anthropic
from anthropic.types import MessageParam

from app.schemas import (
    ContentCalendarOutput,
    EventInput,
    FlyerOutput,
    GeneratedContentResponse,
    HashtagsOutput,
    NewsletterOutput,
    SocialPostOutput,
)
from app.services.prompts import get_all_prompts, resolve_variant


def get_anthropic_client() -> anthropic.Anthropic:
    """Initialize Anthropic client with API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return anthropic.Anthropic(api_key=api_key)


def pydantic_to_anthropic_tool(schema_class, tool_name: str, description: str) -> dict[str, Any]:
    """
    Convert a Pydantic model to Anthropic tool schema format.
    This forces Claude to return structured JSON matching our schemas.
    """
    json_schema = schema_class.model_json_schema()
    
    return {
        "name": tool_name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": json_schema.get("properties", {}),
            "required": json_schema.get("required", []),
        },
    }


async def generate_social_post(client: anthropic.Anthropic, prompt: str) -> SocialPostOutput:
    """Generate social media post using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        SocialPostOutput,
        "create_social_post",
        "Create a WVF-branded social media post with caption, hashtags, image prompt, and CTA"
    )
    
    # Use asyncio.to_thread to run sync API call in executor
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        tools=[tool],
        messages=[{"role": "user", "content": prompt}],
    )
    
    # Extract tool use from response
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")
    
    return SocialPostOutput(**tool_use_block.input)


async def generate_hashtags(client: anthropic.Anthropic, prompt: str) -> HashtagsOutput:
    """Generate hashtag recommendations using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        HashtagsOutput,
        "recommend_hashtags",
        "Recommend primary brand hashtags and topic-specific hashtags for the event"
    )
    
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[tool],
        messages=[{"role": "user", "content": prompt}],
    )
    
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")
    
    return HashtagsOutput(**tool_use_block.input)


async def generate_newsletter(client: anthropic.Anthropic, prompt: str) -> NewsletterOutput:
    """Generate newsletter/email content using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        NewsletterOutput,
        "create_newsletter",
        "Create newsletter content with subject line, preview text, body HTML, and CTA"
    )
    
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        tools=[tool],
        messages=[{"role": "user", "content": prompt}],
    )
    
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")
    
    return NewsletterOutput(**tool_use_block.input)


async def generate_flyer(client: anthropic.Anthropic, prompt: str) -> FlyerOutput:
    """Generate event flyer copy using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        FlyerOutput,
        "create_flyer_copy",
        "Create WVF-branded flyer copy with headline, subheadline, body, CTA, and footer details"
    )

    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[tool],
        messages=[{"role": "user", "content": prompt}],
    )

    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")

    return FlyerOutput(**tool_use_block.input)


async def generate_calendar(client: anthropic.Anthropic, prompt: str) -> ContentCalendarOutput:
    """Generate a multi-week content calendar using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        ContentCalendarOutput,
        "create_content_calendar",
        "Create a multi-week content calendar with platform-varied post entries, hashtags, and CTAs"
    )

    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=[tool],
        messages=[{"role": "user", "content": prompt}],
    )

    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")

    return ContentCalendarOutput(**tool_use_block.input)


async def generate_all_content(
    event: EventInput,
    social_post_variant_selection: str = "generate_new",
    newsletter_variant_selection: str = "generate_new",
    recent_social_post_variants: list[str] | None = None,
    recent_newsletter_variants: list[str] | None = None,
) -> tuple[GeneratedContentResponse, str, str]:
    """
    Generate all content types concurrently.
    This is the main entry point for content generation.

    social_post_variant_selection / newsletter_variant_selection accept the
    same values as the frontend dropdown: "generate_new", "avoid_recent", or
    an explicit variant key (see app/services/prompts.resolve_variant).
    `recent_*_variants` should be recent structure_variant history for this
    event/content type when selection is "avoid_recent" — pass None until
    the database is wired up (falls back to "generate_new" behavior).

    Returns the generated content plus the two resolved variant keys, so
    callers can persist which variant was actually used.
    """
    client = get_anthropic_client()

    social_post_variant = resolve_variant(
        "social_post", social_post_variant_selection, recent_social_post_variants
    )
    newsletter_variant = resolve_variant(
        "newsletter", newsletter_variant_selection, recent_newsletter_variants
    )

    prompts = get_all_prompts(
        event,
        social_post_variant=social_post_variant,
        newsletter_variant=newsletter_variant,
    )

    # Run all generations concurrently
    social_post, hashtags, newsletter, flyer, calendar = await asyncio.gather(
        generate_social_post(client, prompts["social_post"]),
        generate_hashtags(client, prompts["hashtags"]),
        generate_newsletter(client, prompts["newsletter"]),
        generate_flyer(client, prompts["flyer"]),
        generate_calendar(client, prompts["calendar"]),
    )

    result = GeneratedContentResponse(
        social_post=social_post,
        hashtags=hashtags,
        newsletter=newsletter,
        flyer=flyer,
        calendar=calendar,
    )
    return result, social_post_variant, newsletter_variant
