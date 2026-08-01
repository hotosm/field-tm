"""Area splitter module."""

from enum import StrEnum
from pathlib import Path

algorithms_path = Path(__file__).parent / "algorithms"


class SplittingAlgorithm(StrEnum):
    """The type of splitting to apply to an AOI."""

    NO_SPLITTING = "NO_SPLITTING"
    DIVIDE_BY_SQUARE = "DIVIDE_BY_SQUARE"
    AVG_BUILDING_VORONOI = "AVG_BUILDING_VORONOI"
    AVG_BUILDING_SKELETON = "AVG_BUILDING_SKELETON"
    TOTAL_TASKS = "TOTAL_TASKS"
    SPLIT_BY_ROADS = "SPLIT_BY_ROADS"

    @property
    def sql_path(self) -> Path | None:
        """Get the algorithm-specific (step 4) SQL file for building-based algorithms."""
        if self in (
            SplittingAlgorithm.AVG_BUILDING_VORONOI,
            SplittingAlgorithm.AVG_BUILDING_SKELETON,
            SplittingAlgorithm.TOTAL_TASKS,
        ):
            sql_file = {
                SplittingAlgorithm.AVG_BUILDING_VORONOI: "avg_building_voronoi.sql",
                SplittingAlgorithm.AVG_BUILDING_SKELETON: (
                    "avg_building_straight_skeleton.sql"
                ),
                SplittingAlgorithm.TOTAL_TASKS: "avg_building_straight_skeleton.sql",
            }[self]
            return algorithms_path / sql_file
        return None

    @property
    def sql_files(self) -> list[Path] | None:
        """Ordered SQL files to run for SQL-based splitting, or None if not SQL-based."""
        if self.sql_path:
            return [
                algorithms_path / "common/1-linear-features.sql",
                algorithms_path / "common/2-group-buildings.sql",
                algorithms_path / "common/3-cluster-buildings.sql",
                self.sql_path,
                algorithms_path / "common/5-alignment.sql",
                algorithms_path / "common/6-extract.sql",
            ]
        if self is SplittingAlgorithm.SPLIT_BY_ROADS:
            return [
                algorithms_path / "common/1-linear-features.sql",
                algorithms_path / "split_by_roads.sql",
            ]
        return None

    @property
    def label(self) -> str:
        """Human-readable name."""
        return {
            SplittingAlgorithm.NO_SPLITTING: "No Splitting (Use Whole AOI)",
            SplittingAlgorithm.DIVIDE_BY_SQUARE: "Split by Square",
            SplittingAlgorithm.AVG_BUILDING_VORONOI: "Average Buildings v1 (Voronoi)",
            SplittingAlgorithm.AVG_BUILDING_SKELETON: (
                "Average Buildings v2 (Straight Skeleton)"
            ),
            SplittingAlgorithm.TOTAL_TASKS: "Split by Specific Number of Tasks",
            SplittingAlgorithm.SPLIT_BY_ROADS: "Split by Roads",
        }[self]

    @property
    def required_params(self) -> list[str]:
        """List of required parameter names for this algorithm."""
        return {
            SplittingAlgorithm.NO_SPLITTING: [],
            SplittingAlgorithm.DIVIDE_BY_SQUARE: [],
            SplittingAlgorithm.AVG_BUILDING_VORONOI: ["num_buildings"],
            SplittingAlgorithm.AVG_BUILDING_SKELETON: ["num_buildings"],
            SplittingAlgorithm.TOTAL_TASKS: ["num_enumerators"],
            SplittingAlgorithm.SPLIT_BY_ROADS: [],
        }[self]
