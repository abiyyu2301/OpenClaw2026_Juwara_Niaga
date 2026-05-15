"""Build ICP / offer / outreach context dicts from a Campaign row."""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

from db.models import Campaign


def format_geography(campaign: Campaign) -> str:
    if campaign.geo_place_name:
        parts = [campaign.geo_place_name]
        if campaign.geo_radius_km:
            parts.append(f"radius {campaign.geo_radius_km} km")
        return ", ".join(parts)
    return campaign.geography or ""


def icp_dict(campaign: Campaign) -> dict:
    return {
        "name": campaign.name,
        "target_industry": campaign.target_industry,
        "company_size": campaign.company_size,
        "geography": format_geography(campaign),
        "buyer_role": campaign.buyer_role,
        "pain_points": campaign.pain_points,
        "disqualifiers": campaign.disqualifiers,
    }


def offer_dict(campaign: Campaign) -> dict:
    return {
        "offer": campaign.offer,
        "pricing_range_min": campaign.pricing_range_min,
        "pricing_range_max": campaign.pricing_range_max,
        "currency": campaign.currency or "IDR",
        "sales_target_revenue": campaign.sales_target_revenue,
    }


def rep_dict(campaign: Campaign) -> dict:
    return {
        "name": campaign.rep_name or "Tim Niaga",
        "title": campaign.rep_title or "",
        "email": campaign.rep_email or "",
        "phone": campaign.rep_phone or "",
    }


def email_sender(campaign: Campaign) -> dict:
    """SMTP always uses team Gmail; rep fields personalize From display + Reply-To."""
    return {
        "from_display_name": campaign.rep_name or "Tim Niaga",
        "reply_to": (campaign.rep_email or "").strip() or None,
    }


def outreach_context(campaign: Campaign, *, promo_url: Optional[str] = None) -> dict:
    return {
        "sales_voice": campaign.sales_voice or "Formal tapi hangat, Bahasa Indonesia bisnis",
        "sales_voice_samples": campaign.sales_voice_samples or "",
        "rep": rep_dict(campaign),
        "promo_asset_url": promo_url or campaign.promo_asset_url,
        "promo_asset_type": campaign.promo_asset_type,
    }


def suggest_max_leads(campaign: Campaign) -> int:
    """Suggest leads per run from revenue target and pricing band."""
    target = campaign.sales_target_revenue
    if not target or target <= 0:
        return campaign.max_leads_per_run or 10

    lo = campaign.pricing_range_min or 500_000
    hi = campaign.pricing_range_max or lo
    avg_deal = max((lo + hi) / 2, 1)
    # Rough funnel: 30% qualify, 10% of qualified close
    qualify_rate = 0.30
    close_rate = 0.10
    deals_needed = target / avg_deal
    processed_needed = deals_needed / (qualify_rate * close_rate)
    return int(max(3, min(50, math.ceil(processed_needed))))
