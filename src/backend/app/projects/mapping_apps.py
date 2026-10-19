"""Catalogue of mapping apps and the guided app recommendation (#3135).

Type A apps sync tasks through an API (ODK, QField). Type B apps get the task
plan as files only; Field-TM just stores and shares it.
"""

from dataclasses import dataclass

from app.db.enums import FieldMappingApp
from app.i18n import _

SYNC = "A"
FILES = "B"


@dataclass(frozen=True)
class MappingApp:
    """One entry in the app picker."""

    key: FieldMappingApp
    name: str
    type: str
    logo: str | None
    url: str
    description: str
    good_for: str

    @property
    def syncs(self) -> bool:
        """Whether Field-TM pushes tasks to the app (Type A)."""
        return self.type == SYNC


def _logo(filename: str) -> str:
    return f"/static/images/apps/{filename}"


def mapping_apps() -> list[MappingApp]:
    """All apps, in display order (built per call so strings are translated)."""
    app = FieldMappingApp
    return [
        MappingApp(
            app.QFIELD,
            "QField",
            SYNC,
            _logo("qfield.svg"),
            "https://qfield.org",
            _("GIS mapping app for Android and iOS, with our simple task plugin."),
            _("Drawing and editing geometry, detailed surveys"),
        ),
        MappingApp(
            app.ODK,
            "ODK Collect",
            SYNC,
            _logo("odk.svg"),
            "https://getodk.org",
            _("Form-based survey app for Android."),
            _("Form-heavy surveys, simple phones"),
        ),
        MappingApp(
            app.EVERYDOOR,
            "Every Door",
            FILES,
            _logo("everydoor.png"),
            "https://every-door.app",
            _("Fast OpenStreetMap editor for shops, amenities and entrances."),
            _("Updating existing OSM buildings and points of interest"),
        ),
        MappingApp(
            app.STREETCOMPLETE,
            "StreetComplete",
            FILES,
            _logo("streetcomplete.svg"),
            "https://streetcomplete.app",
            _("Answer simple quests to complete OpenStreetMap data."),
            _("Quick OSM attribute quests on roads and points of interest"),
        ),
        MappingApp(
            app.COMAPEO,
            "CoMapeo",
            FILES,
            _logo("comapeo.png"),
            "https://comapeo.app",
            _("Offline-first mapping for communities and territories."),
            _("Offline, community-led mapping"),
        ),
        MappingApp(
            app.COMAPS,
            "CoMaps",
            FILES,
            _logo("comaps.png"),
            "https://comaps.app",
            _("Offline maps and navigation, with OSM editing."),
            _("Navigating to tasks, editing OSM points"),
        ),
        MappingApp(
            app.PANORAMAX,
            "Panoramax",
            FILES,
            _logo("panoramax.svg"),
            "https://panoramax.fr",
            _("Open street-level imagery, captured with any camera."),
            _("Street-level imagery along roads"),
        ),
        MappingApp(
            app.SKETCHMAP,
            "SketchMap",
            FILES,
            _logo("sketchmap.svg"),
            "https://sketch-map-tool.heigit.org",
            _("Print paper maps, sketch on them, scan them back."),
            _("Paper maps and sketch mapping"),
        ),
        MappingApp(
            app.CHATMAP,
            "ChatMap",
            FILES,
            _logo("chatmap.svg"),
            "https://chatmap.hotosm.org",
            _("Turn locations shared in chat apps into a map."),
            _("Location sharing from chat apps"),
        ),
        MappingApp(
            app.OTHER,
            _("Other app"),
            FILES,
            None,
            "",
            _("Any other app. Share the tasks as files and links."),
            _("Any app"),
        ),
    ]


def get_mapping_app(key: object) -> MappingApp | None:
    """Look up an app by enum or value (None if unknown)."""
    value = getattr(key, "value", key)
    return next((a for a in mapping_apps() if a.key.value == value), None)


def is_sync_app(key: object) -> bool:
    """Whether the app is Type A (tasks synced through an API)."""
    app = get_mapping_app(key)
    return bool(app and app.syncs)


MAPPING_TYPES = ("buildings", "roads", "rivers", "pois", "other")


def recommend_apps(
    mapping_type: str, for_osm: bool, well_mapped: bool | None
) -> tuple[list[FieldMappingApp], str]:
    """Recommend apps (best first) for the guided questions, with a reason."""
    app = FieldMappingApp
    if not for_osm:
        return [app.QFIELD, app.ODK], _(
            "Not for OpenStreetMap: QField for map-based capture and editing, "
            "or ODK for form-heavy surveys."
        )
    if well_mapped is False:
        return [app.QFIELD, app.ODK], _(
            "Poorly mapped: QField lets mappers draw the missing geometry."
        )
    if mapping_type in ("buildings", "pois"):
        return [app.EVERYDOOR, app.STREETCOMPLETE], _(
            "Already mapped: Every Door is the quickest way to update buildings "
            "and points of interest."
        )
    if mapping_type == "roads":
        return [app.STREETCOMPLETE, app.PANORAMAX], _(
            "Already mapped: StreetComplete for road details, or Panoramax "
            "for street-level imagery."
        )
    return [app.QFIELD], _("QField handles any kind of feature.")


def app_picker_context(
    mapping_type: str = "",
    for_osm: str = "",
    well_mapped: str = "",
    selected: str = "",
) -> dict:
    """Template context for the app picker, given the raw form answers."""
    recommended: list[FieldMappingApp] = []
    reason = None
    if for_osm in ("yes", "no"):
        recommended, reason = recommend_apps(
            mapping_type if mapping_type in MAPPING_TYPES else "other",
            for_osm == "yes",
            {"yes": True, "no": False}.get(well_mapped),
        )
    apps = sorted(
        mapping_apps(),
        key=lambda a: recommended.index(a.key) if a.key in recommended else 99,
    )
    return {
        "apps": apps,
        "recommended": recommended,
        "reason": reason,
        "selected": selected,
    }
