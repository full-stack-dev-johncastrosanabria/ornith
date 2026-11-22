export type Status = "todo" | "doing" | "done";

export interface Task {
  readonly id: number;
  readonly title: string;
  readonly status: Status;
  readonly assignee: string | null;
  readonly tags: readonly string[];
  readonly priority: number; // 1 (lowest) .. 5 (highest)
  readonly dueDate: string | null; // YYYY-MM-DD
}

/** Raw query-string values, exactly as received. Absent parameters are undefined. */
export interface TaskQuery {
  status?: string;
  assignee?: string;
  tag?: string;
  q?: string;
  sort?: string;
  page?: string;
  pageSize?: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}
