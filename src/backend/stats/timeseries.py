"""Get number of Field-TM projects over time."""

import asyncio
import calendar
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx
import itrm
import numpy as np
from pydantic import AwareDatetime, BaseModel

# Access from the same machine: http://localhost:7052
# Access from the docker container: http://localhost:8000
# Access from another container on same docker network: http://api:8000
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", None)
headers = {"access-token": API_TOKEN} if API_TOKEN else None

START_YEAR: int = int(os.getenv("START_YEAR", 2024))


class ProjectDetails(BaseModel):
    id: int
    updated_at: Optional[AwareDatetime] = None
    created_at: Optional[AwareDatetime] = None


async def fetch_projects(client: httpx.AsyncClient) -> List[ProjectDetails]:
    url = f"{API_BASE_URL}/projects"
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    return [ProjectDetails(**proj) for proj in response.json()]


async def process_projects(projects: list[ProjectDetails]):
    now = datetime.now(timezone.utc)
    current_year = now.year
    one_year_ago = now - timedelta(days=365)
    one_month_ago = now - timedelta(days=30)
    one_week_ago = now - timedelta(days=7)

    project_per_month = defaultdict(int)  # Stores projects per month since START_YEAR
    projects_per_year = {year: 0 for year in range(START_YEAR, current_year + 1)}
    active_past_year = 0
    active_past_month = 0
    active_past_week = 0
    total_projects = len(projects)

    for project in projects:
        if project.created_at:
            project_year = project.created_at.year
            project_month = project.created_at.month

            if project_year >= START_YEAR:
                projects_per_year[project_year] += 1
                project_per_month[(project_year, project_month)] += (
                    1  # Key is (year, month)
                )

        if project.updated_at:
            if project.updated_at >= one_year_ago:
                active_past_year += 1
            if project.updated_at >= one_month_ago:
                active_past_month += 1
            if project.updated_at >= one_week_ago:
                active_past_week += 1

    # Convert month integers to month names for the current year
    projects_per_named_month = {
        calendar.month_abbr[i]: project_per_month[(current_year, i)]
        for i in range(1, 13)
    }

    # Calculate average project increase rate per month (only for months passed this year)
    current_month = now.month
    months_with_data = [
        project_per_month[(current_year, i)] for i in range(1, current_month + 1)
    ]
    project_monthly_average = (
        sum(months_with_data) / len(months_with_data) if months_with_data else 0
    )

    # Generate discrete (x, y) data points
    project_dates = []
    project_count_over_time = []

    for year in range(START_YEAR, current_year + 1):
        for month in range(1, 13):
            if year < current_year or (year == current_year and month <= current_month):
                dt = datetime(year, month, 1)
                timestamp = dt.timestamp()  # Convert to Unix time
                project_dates.append(timestamp)
                project_count_over_time.append(project_per_month.get((year, month), 0))

    # Print stats
    print("\nFMTM Stats")
    print("----------\n")
    print(f"Total overall projects: {total_projects}\n")
    print(f"Total project per year: {projects_per_year}\n")
    print(f"Active projects in last year: {active_past_year}\n")
    print(f"Active projects in last month: {active_past_month}\n")
    print(f"Active projects in last week: {active_past_week}\n")
    print(f"Average number of new projects per month this year so far: {project_monthly_average:.2f}\n")

    # Bar chart: Total projects per month in the current year
    print("Total project per month this year:")
    itrm.bars(
        list(projects_per_named_month.values()), list(projects_per_named_month.keys())
    )
    print()

    # Line chart: Total projects over time since START_YEAR
    # Interpolation: Create a smooth x-axis
    x_axis_points_num = (
        len(projects_per_year.keys()) * 1000
    )  # 1000 points on graph per year
    x_smooth = np.linspace(
        min(project_dates), max(project_dates), num=x_axis_points_num
    )
    # Interpolation: Smooth y-values (projects over time)
    y_smooth = np.interp(x_smooth, project_dates, project_count_over_time)
    print(f"Total project per month since {START_YEAR}:")
    itrm.plot(x_smooth, y_smooth, "Projects Over Time")
    print()


async def main():
    print(f"Connecting to server: {API_BASE_URL}")

    async with httpx.AsyncClient() as client:
        projects = await fetch_projects(client)
        if not projects:
            print("No projects found.")
            return

        await process_projects(projects)


if __name__ == "__main__":
    asyncio.run(main())
