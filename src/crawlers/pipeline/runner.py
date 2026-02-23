from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy import func, literal, select

from src.crawlers.pipeline.types import ExtractedActivity
from src.crawlers.extractors.hardcoded import extract_from_event_page
from src.db.session import SessionLocal
from src.models.activity import Activity, FreeVerificationStatus, Source, Venue


def _to_free_status(value: str) -> FreeVerificationStatus:
    try:
        return FreeVerificationStatus(value)
    except ValueError:
        return FreeVerificationStatus.inferred


def _resolve_venue(
    db,
    venue_name: str | None,
    location_text: str | None,
    city: str | None,
    state: str | None,
) -> Venue | None:
    if not venue_name and not location_text:
        return None

    normalized_name = venue_name or "Unknown Venue"
    existing = db.scalar(
        select(Venue).where(
            Venue.name == normalized_name,
            Venue.city == city,
            Venue.state == state,
        )
    )
    if existing is not None:
        return existing

    venue = Venue(
        name=normalized_name,
        address=location_text,
        city=city,
        state=state,
        website=None,
    )
    db.add(venue)
    db.flush()
    return venue


def upsert_extracted_activities(
    source_url: str,
    extracted: list[ExtractedActivity],
    *,
    adapter_type: str = "static_html",
) -> list[ExtractedActivity]:
    """Upsert extracted activity rows and return the deduplicated inputs."""
    deduped = list({(a.source_url, a.title, a.start_at, a.end_at): a for a in extracted}.values())
    if not deduped:
        return deduped

    now = datetime.utcnow()
    with SessionLocal() as db:
        source = db.scalar(
            select(Source)
            .where(literal(source_url).like(func.concat(Source.base_url, "%")))
            .order_by(func.length(Source.base_url).desc())
            .limit(1)
        )
        if source is None:
            parsed = urlparse(source_url)
            source = Source(
                name=(parsed.netloc or "unknown_source"),
                base_url=f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else source_url,
                adapter_type=adapter_type,
                crawl_frequency="daily",
                active=True,
            )
            db.add(source)
            db.flush()

        urls = {a.source_url for a in deduped}
        titles = {a.title for a in deduped}
        start_times = {a.start_at for a in deduped}
        existing_items = db.scalars(
            select(Activity).where(
                Activity.source_id == source.id,
                Activity.source_url.in_(urls),
                Activity.title.in_(titles),
                Activity.start_at.in_(start_times),
            )
        ).all()
        existing_by_key = {(a.source_url, a.title, a.start_at, a.end_at): a for a in existing_items}

        for item in deduped:
            key = (item.source_url, item.title, item.start_at, item.end_at)
            current = existing_by_key.get(key)
            venue = _resolve_venue(db, item.venue_name, item.location_text, item.city, item.state)
            if current is None:
                db.add(
                    Activity(
                        source_id=source.id,
                        source_url=item.source_url,
                        title=item.title,
                        description=item.description,
                        activity_type=item.activity_type,
                        age_min=item.age_min,
                        age_max=item.age_max,
                        drop_in=item.drop_in,
                        registration_required=item.registration_required,
                        start_at=item.start_at,
                        end_at=item.end_at,
                        timezone=item.timezone,
                        location_text=item.location_text,
                        venue_id=venue.id if venue else None,
                        free_verification_status=_to_free_status(item.free_verification_status),
                        first_seen_at=now,
                        last_seen_at=now,
                        updated_at=now,
                    )
                )
                continue

            current.description = item.description
            current.activity_type = item.activity_type
            current.age_min = item.age_min
            current.age_max = item.age_max
            current.drop_in = item.drop_in
            current.registration_required = item.registration_required
            current.end_at = item.end_at
            current.timezone = item.timezone
            current.location_text = item.location_text
            current.venue_id = venue.id if venue else None
            current.free_verification_status = _to_free_status(item.free_verification_status)
            current.last_seen_at = now
            current.updated_at = now

        db.commit()

    return deduped


async def run_single_page(source_url: str, html: str):
    """Ingest a single event page payload and upsert activities into MySQL.

    Current implementation keeps the extraction phase deterministic (hardcoded parser),
    then performs a lightweight upsert keyed by source_url/title/time fields.
    """
    # 1) Parse raw HTML into normalized activity objects.
    # The extractor returns a list because one page may contain multiple activities.
    extracted = extract_from_event_page(source_url=source_url, html=html)

    # 2) Persist with shared upsert logic used by other adapters.
    return upsert_extracted_activities(source_url=source_url, extracted=extracted, adapter_type="static_html")
