from datetime import datetime

from sqlalchemy import Select, and_, case, func, or_, select
from sqlalchemy.orm import Session, joinedload

from src.models.activity import Activity, Venue


def list_activities(
    db: Session,
    age: int | None,
    drop_in: bool | None,
    venue: str | None,
    city: str | None,
    state: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> list[Activity]:
    stmt: Select[tuple[Activity]] = select(Activity).where(
        Activity.is_free.is_(True),
        Activity.status.in_(("active", "needs_review")),
    )
    stmt = stmt.options(joinedload(Activity.venue))
    stmt = stmt.outerjoin(Venue, Activity.venue_id == Venue.id)

    filters = []
    if age is not None:
        filters.append(and_(Activity.age_min.is_(None) | (Activity.age_min <= age)))
        filters.append(and_(Activity.age_max.is_(None) | (Activity.age_max >= age)))
    if drop_in is not None:
        filters.append(Activity.drop_in.is_(drop_in))
    if venue:
        filters.append(func.lower(Venue.name).like(f"%{venue.lower()}%"))
    if city:
        filters.append(func.lower(Venue.city).like(f"%{city.lower()}%"))
    if state:
        filters.append(func.upper(Venue.state) == state.upper())
    if date_from is not None:
        filters.append(Activity.start_at >= date_from)
    if date_to is not None:
        filters.append(Activity.start_at <= date_to)

    if filters:
        stmt = stmt.where(*filters)

    stmt = stmt.order_by(Activity.start_at.asc()).limit(200)
    return list(db.scalars(stmt))


def get_filter_suggestions(
    db: Session,
    *,
    field: str,
    query: str,
    limit: int = 10,
) -> list[str]:
    """Return small suggestion lists for UI autocomplete.

    Uses prefix matching (`value%`) so MySQL can use indexes efficiently.
    """
    q = query.strip()
    if not q:
        return []

    if field == "venue":
        column = Venue.name
        # Support typing after a leading article, e.g. "m" -> "The Metropolitan Museum..."
        prefixed_patterns = [f"{q}%", f"The {q}%", f"A {q}%", f"An {q}%"]
        rank = case(
            (column.like(f"{q}%"), 0),
            (column.like(f"The {q}%"), 1),
            (column.like(f"A {q}%"), 2),
            (column.like(f"An {q}%"), 3),
            else_=9,
        )
        stmt = (
            select(column)
            .distinct()
            .where(column.is_not(None), or_(*[column.like(pattern) for pattern in prefixed_patterns]))
            .order_by(rank.asc(), column.asc())
            .limit(max(1, min(limit, 20)))
        )
        return [value for value in db.scalars(stmt) if value]
    elif field == "city":
        column = Venue.city
    elif field == "state":
        column = Venue.state
    else:
        return []

    stmt = (
        select(column)
        .distinct()
        .where(column.is_not(None), column.like(f"{q}%"))
        .order_by(column.asc())
        .limit(max(1, min(limit, 20)))
    )
    return [value for value in db.scalars(stmt) if value]
