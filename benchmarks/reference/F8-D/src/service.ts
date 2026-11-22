import { ValidationError } from "./errors.ts";
import type { Page, Task, TaskQuery } from "./types.ts";
import { TASKS } from "./store.ts";
import { intParam } from "./validation.ts";

const STATUSES: readonly string[] = ["todo", "doing", "done"];
const FIELDS: readonly string[] = ["dueDate", "priority", "title"];

function compare(field: string, a: Task, b: Task): number {
  if (field === "priority") return a.priority - b.priority;
  const x = field === "title" ? a.title.toLowerCase() : (a.dueDate as string);
  const y = field === "title" ? b.title.toLowerCase() : (b.dueDate as string);
  return x < y ? -1 : x > y ? 1 : 0;
}

/** Filters, sorts and paginates tasks as described in README.md ("Listing tasks"). */
export function listTasks(query: TaskQuery, tasks: readonly Task[] = TASKS): Page<Task> {
  let statuses: string[] | undefined;
  if (query.status !== undefined) {
    statuses = query.status.split(",").map((s) => s.trim());
    if (statuses.some((s) => !STATUSES.includes(s))) throw new ValidationError("status", "unknown status");
  }
  const parts = (query.sort ?? "priority:desc").split(":");
  const [field, direction] = parts;
  if (parts.length !== 2 || !FIELDS.includes(field) || (direction !== "asc" && direction !== "desc")) {
    throw new ValidationError("sort", "sort must be field:asc or field:desc");
  }
  const page = intParam("page", query.page, 1, 1, Number.MAX_SAFE_INTEGER);
  const pageSize = intParam("pageSize", query.pageSize, 20, 1, 100);
  const needle = (query.q ?? "").trim().toLowerCase();
  const assignee = query.assignee === "none" ? null : query.assignee;
  const matches = tasks.filter((t) =>
    (statuses === undefined || statuses.includes(t.status)) &&
    (query.assignee === undefined || t.assignee === assignee) &&
    (query.tag === undefined || t.tags.includes(query.tag)) &&
    (needle === "" || t.title.toLowerCase().includes(needle)));
  const sign = direction === "asc" ? 1 : -1;
  const sorted = [...matches].sort((a, b) => {
    if (field === "dueDate" && (a.dueDate === null || b.dueDate === null)) {
      if (a.dueDate === b.dueDate) return a.id - b.id;
      return a.dueDate === null ? 1 : -1;
    }
    return sign * compare(field, a, b) || a.id - b.id;
  });
  const start = (page - 1) * pageSize;
  return { items: sorted.slice(start, start + pageSize), total: matches.length, page, pageSize };
}
