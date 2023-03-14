
export interface HomeProjectCardModel {
    id: number,
    priority: number,
    title: string,
    location_str: string,
    description: string,
    total_tasks: number,
    tasks_mapped: number,
    tasks_validated: number,
    tasks_bad_imagery: number
}