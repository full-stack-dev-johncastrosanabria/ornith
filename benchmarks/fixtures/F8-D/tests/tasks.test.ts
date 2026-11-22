import { test } from "node:test";
import assert from "node:assert/strict";
import { ValidationError } from "../src/errors.ts";
import { handle } from "../src/http.ts";
import { listTasks } from "../src/service.ts";
import type { TaskQuery } from "../src/types.ts";

function check(query: TaskQuery, ids: number[], total: number, page: number, pageSize: number): void {
  const result = listTasks(query);
  assert.deepEqual(result.items.map((t) => t.id), ids);
  assert.deepEqual([result.total, result.page, result.pageSize], [total, page, pageSize]);
}

test("default listing", () => check({}, [3, 16, 19, 24, 30, 40, 6, 18, 25, 26, 27, 34, 35, 36, 39, 2, 10, 12, 15, 20], 40, 1, 20));
test("status list with due date ascending", () => check({"status": "todo, done", "sort": "dueDate:asc", "pageSize": "100"}, [22, 23, 27, 29, 13, 2, 9, 4, 1, 40, 34, 10, 25, 7, 6, 20, 21, 32, 33], 19, 1, 100));
test("unassigned by title", () => check({"assignee": "none", "sort": "title:asc", "pageSize": "100"}, [35, 7, 14, 39, 9, 33, 4, 6, 11, 18, 28, 29, 5, 17, 37, 19, 1, 21, 36], 19, 1, 100));
test("tag and trimmed case-insensitive search", () => check({"tag": "api", "q": "  GATEWAY ", "pageSize": "100"}, [2, 20], 2, 1, 100));
test("second page by title descending", () => check({"sort": "title:desc", "page": "2", "pageSize": "7"}, [17, 30, 16, 23, 5, 10, 25], 40, 2, 7));
test("due date descending keeps missing dates last", () => check({"status": "doing", "sort": "dueDate:desc", "pageSize": "100"}, [37, 17, 3, 38, 16, 35, 11, 19, 26, 31, 30, 5, 39, 14, 36, 12, 8, 15, 18, 24, 28], 21, 1, 100));
test("assignee with priority ascending", () => check({"assignee": "bo", "sort": "priority:asc"}, [8, 20, 31, 32, 27, 3, 24], 7, 1, 20));
test("page past the end", () => check({"page": "9", "pageSize": "5"}, [], 40, 9, 5));

const INVALID: [TaskQuery, string][] = [
  [{"status": "blocked"}, "status"],
  [{"status": "todo,"}, "status"],
  [{"sort": "owner:asc"}, "sort"],
  [{"sort": "priority:up"}, "sort"],
  [{"sort": "priority"}, "sort"],
  [{"page": "0"}, "page"],
  [{"page": "1.5"}, "page"],
  [{"pageSize": "101"}, "pageSize"],
  [{"pageSize": ""}, "pageSize"],
  [{"pageSize": "-3"}, "pageSize"],
];

for (const [query, field] of INVALID) {
  test(`rejects ${JSON.stringify(query)}`, () => {
    assert.throws(() => listTasks(query), (error: unknown) => error instanceof ValidationError && error.field === field);
  });
}

test("items are the stored task objects", () => {
  const [first] = listTasks({ q: "gateway" }).items;
  assert.equal(typeof first.title, "string");
  assert.ok(first.title.toLowerCase().includes("gateway"));
});

test("http handler", () => {
  const ok = handle("/tasks?assignee=ana&pageSize=2");
  assert.equal(ok.status, 200);
  assert.deepEqual((ok.body as { items: { id: number }[] }).items.map((t) => t.id), [16, 10]);
  assert.deepEqual(handle("/tasks?status=bogus"), { status: 400, body: { error: "validation", field: "status" } });
  assert.deepEqual(handle("/tasks?sort=title:sideways"), { status: 400, body: { error: "validation", field: "sort" } });
});
