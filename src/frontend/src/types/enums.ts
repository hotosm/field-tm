export enum task_split_type {
  divide_on_square = 0,
  choose_area_as_task = 1,
  task_splitting_algorithm = 2,
}

export enum task_priority_str {
  READY = 0,
  LOCKED_FOR_MAPPING = 1,
  MAPPED = 2,
  LOCKED_FOR_VALIDATION = 3,
  VALIDATED = 4,
  INVALIDATED = 5,
  BAD = 6,
  SPLIT = 7,
  ARCHIVED = 8,
}
