import type { Page, Task, TaskQuery } from "./types.ts";
import { TASKS } from "./store.ts";

/** Filters, sorts and paginates tasks as described in README.md ("Listing tasks"). */
export function listTasks(query: TaskQuery, tasks: readonly Task[] = TASKS): Page<Task> {
  throw new Error("not implemented");
}
