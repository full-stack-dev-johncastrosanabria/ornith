# Task board service

Node runs the TypeScript sources directly (type stripping, no build step): import with explicit `.ts`
extensions, use `import type` for type-only imports, and avoid enums, namespaces and constructor
parameter properties.

## Listing tasks

`listTasks(query, tasks = TASKS)` receives the raw query-string values (`TaskQuery`, all strings) and returns a `Page<Task>`.

Filters (all optional, combined with AND):

- `status`: comma-separated list of statuses (`todo`, `doing`, `done`); whitespace around each entry is ignored. A task matches when its status is in the list. Any other value is invalid.
- `assignee`: exact assignee name; the special value `none` selects unassigned tasks (`assignee === null`).
- `tag`: the task's `tags` contain this tag.
- `q`: case-insensitive substring of the title, after trimming the query; an empty or blank `q` is ignored.

Sorting: `sort` is `field:direction` with field `dueDate`, `priority` or `title` and direction `asc` or `desc`.
The default is `priority:desc`. Titles compare case-insensitively (lower-cased, by code unit). Ties are always
broken by `id` ascending, whatever the direction. Tasks without a `dueDate` always come last when sorting by
`dueDate`, in both directions (among themselves, by `id`).

Pagination: `page` (default 1, at least 1) and `pageSize` (default 20, from 1 to 100) are whole numbers written
with digits only. A page past the end has no items. `total` is the number of tasks matching the filters.

Invalid input throws `ValidationError` whose `field` names the parameter (`status`, `sort`, `page` or `pageSize`).
