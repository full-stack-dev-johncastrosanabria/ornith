import { ValidationError } from "./errors.ts";
import { listTasks } from "./service.ts";
import type { TaskQuery } from "./types.ts";

const KEYS = ["status", "assignee", "tag", "q", "sort", "page", "pageSize"] as const;

/** GET /tasks?... -> { status, body }. Invalid parameters give 400 with the offending field. */
export function handle(url: string): { status: number; body: unknown } {
  const params = new URL(url, "http://localhost").searchParams;
  const query: TaskQuery = {};
  for (const key of KEYS) {
    const value = params.get(key);
    if (value !== null) query[key] = value;
  }
  try {
    return { status: 200, body: listTasks(query) };
  } catch (error) {
    if (error instanceof ValidationError) return { status: 400, body: { error: "validation", field: error.field } };
    throw error;
  }
}
