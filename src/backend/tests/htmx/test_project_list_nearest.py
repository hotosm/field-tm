"""Tests for the "Projects near me" listing (sort by distance)."""

from contextlib import suppress
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from litestar import status_codes as status

from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.htmx.project_list_routes import project_listing
from app.projects.project_schemas import StubProjectIn

# Reference point for the distance tests: central Nairobi.
NAIROBI = (-1.29, 36.82)


def _square(lon: float, lat: float, size: float = 0.01) -> dict:
    """Small square polygon with its south-west corner at (lon, lat)."""
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [lon, lat],
                [lon + size, lat],
                [lon + size, lat + size],
                [lon, lat + size],
                [lon, lat],
            ]
        ],
    }


@pytest_asyncio.fixture(scope="function")
async def nearby_projects(db):
    """Three projects at known distances from NAIROBI, sharing a search tag.

    The tag lets tests isolate these rows from others in the shared test DB.
    """
    tag = f"near-me-{uuid4().hex[:8]}"
    outlines = {
        # Contains the reference point, so the distance is zero.
        "here": _square(36.815, -1.295),
        # Thika, roughly 40 km north-east.
        "thika": _square(37.07, -1.04),
        # Mombasa, roughly 440 km south-east.
        "mombasa": _square(39.66, -4.05),
    }
    created = {}
    for key, outline in outlines.items():
        created[key] = await DbProject.create(
            db,
            StubProjectIn(
                project_name=f"{tag} {key}",
                field_mapping_app=FieldMappingApp.ODK,
                description="near me test",
                outline=outline,
            ),
        )
    await db.commit()

    yield tag, created

    for project in created.values():
        with suppress(Exception):
            await DbProject.delete(db, project.id)
    await db.commit()


async def test_db_all_sorts_by_distance_and_returns_km(db, nearby_projects):
    """Projects come back nearest first, with distance in kilometres."""
    tag, created = nearby_projects

    projects = await DbProject.all(db, search=tag, sort_by="nearest", near=NAIROBI)

    assert [p.id for p in projects] == [
        created["here"].id,
        created["thika"].id,
        created["mombasa"].id,
    ]
    here, thika, mombasa = projects
    assert here.distance_km == pytest.approx(0)
    assert 30 < thika.distance_km < 50
    assert 400 < mombasa.distance_km < 480


async def test_db_all_ignores_near_point_for_other_sorts(db, nearby_projects):
    """A point without sort_by="nearest" must not change order or add distance."""
    tag, _ = nearby_projects

    projects = await DbProject.all(db, search=tag, sort_by="name_asc", near=NAIROBI)

    assert [p.project_name.split()[-1] for p in projects] == [
        "here",
        "mombasa",
        "thika",
    ]
    assert all(p.distance_km is None for p in projects)


async def test_db_all_without_near_has_no_distance(db, nearby_projects):
    """Regular listings keep working and never compute a distance."""
    tag, _ = nearby_projects

    projects = await DbProject.all(db, search=tag, sort_by="nearest")

    assert len(projects) == 3
    assert all(p.distance_km is None for p in projects)


async def test_project_listing_nearest_renders_distances(client, nearby_projects):
    """The page shows distances, the privacy note and keeps the point in the form."""
    tag, created = nearby_projects

    response = await client.get(
        "/projects",
        params={"sort": "nearest", "lat": "-1.29", "lon": "36.82", "search": tag},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    text = response.text
    assert "Less than 1 km away" in text
    assert "km away" in text
    assert "Your location is only used for this search and is not" in text
    assert 'name="lat" value="-1.29"' in text
    assert 'name="lon" value="36.82"' in text
    assert '<wa-option value="nearest">' in text
    # Nearest card is rendered first.
    assert text.index(f"/projects/{created['here'].id}") < text.index(
        f"/projects/{created['mombasa'].id}"
    )


async def test_project_listing_shows_near_me_button(client):
    """The button is always offered; the distance sort option only with a point."""
    response = await client.get("/projects", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_200_OK
    assert 'id="projects-near-me"' in response.text
    assert "Projects near me" in response.text
    assert '<wa-option value="nearest">' not in response.text
    assert 'name="lat"' not in response.text


async def test_project_listing_nearest_passes_rounded_point():
    """Coordinates are rounded to ~1 km before they reach the database."""
    projects = [Mock(id=i) for i in range(13)]
    with patch(
        "app.htmx.project_list_routes.DbProject.all", new_callable=AsyncMock
    ) as mock_all:
        mock_all.return_value = projects
        response = await project_listing.fn(
            request=Mock(
                query_params={
                    "sort": "nearest",
                    "lat": "-1.286389",
                    "lon": "36.817223",
                }
            ),
            db=Mock(),
            auth_user=Mock(),
        )

    assert mock_all.await_args.kwargs["sort_by"] == "nearest"
    assert mock_all.await_args.kwargs["near"] == (-1.29, 36.82)
    assert response.context["selected_sort"] == "nearest"
    assert response.context["near"] == (-1.29, 36.82)
    # Pagination keeps the (rounded) point so page 2 is still sorted by distance.
    assert response.context["next_href"] == (
        "/projects?sort=nearest&lat=-1.29&lon=36.82&page=2"
    )


@pytest.mark.parametrize(
    ("lat", "lon"),
    [
        (None, None),
        ("-1.29", None),
        ("abc", "36.82"),
        ("nan", "36.82"),
        ("-1.29", "inf"),
        ("91", "36.82"),
        ("-1.29", "-180.5"),
    ],
)
async def test_project_listing_nearest_without_valid_point_falls_back(lat, lon):
    """Missing or invalid coordinates fall back to the default sort."""
    query_params = {"sort": "nearest"}
    if lat is not None:
        query_params["lat"] = lat
    if lon is not None:
        query_params["lon"] = lon

    with patch(
        "app.htmx.project_list_routes.DbProject.all", new_callable=AsyncMock
    ) as mock_all:
        mock_all.return_value = []
        response = await project_listing.fn(
            request=Mock(query_params=query_params), db=Mock(), auth_user=Mock()
        )

    assert mock_all.await_args.kwargs["sort_by"] == "newest"
    assert mock_all.await_args.kwargs["near"] is None
    assert response.context["selected_sort"] == "newest"
    assert response.context["near"] is None


async def test_project_listing_ignores_point_for_other_sorts():
    """A point in the URL is ignored (not used, not echoed) for other sorts."""
    with patch(
        "app.htmx.project_list_routes.DbProject.all", new_callable=AsyncMock
    ) as mock_all:
        mock_all.return_value = [Mock(id=i) for i in range(13)]
        response = await project_listing.fn(
            request=Mock(
                query_params={"sort": "oldest", "lat": "-1.29", "lon": "36.82"}
            ),
            db=Mock(),
            auth_user=Mock(),
        )

    assert mock_all.await_args.kwargs["near"] is None
    assert response.context["near"] is None
    assert response.context["next_href"] == "/projects?sort=oldest&page=2"
