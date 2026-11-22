"""D061 fixtures F8-D (TypeScript), F8-E (Java 21 + JUnit 5), F8-F (SQL migrations), F8-G (.NET minimal API).

Each builder returns (files, reference_overlay, prompt). Expected values come from small Python mirrors of
the specification, so the reference solutions are checked against an independent implementation.
"""
import hashlib,json,pathlib,random,re
from datetime import date,timedelta

HOME=pathlib.Path.home()
NODE=str(HOME/'.local/share/fnm/node-versions/v26.13.0/installation/bin/node')
JUNIT=str(HOME/'Developer/ornith/runtimes/java-junit')
JDK='/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home/bin'

def sub(text,old,new):
    assert text.count(old)==1,old[:60]
    return text.replace(old,new)

# ---------------------------------------------------------------- F8-D
def ts_seed():
    rnd=random.Random(8104)
    verbs=['Fix','Add','Refactor','Document','Review','Migrate','Test','Deploy']
    objs=['login flow','billing page','search index','API gateway','user profile','export job','cache layer','audit log','payment retries','dark mode']
    out=[]
    for i in range(1,41):
        title=f'{rnd.choice(verbs)} {rnd.choice(objs)}'
        if rnd.random()<.25:title=title.lower()
        out.append({'id':i,'title':title,'status':rnd.choice(['todo','doing','done']),'assignee':rnd.choice(['ana','bo','chen',None,None]),
                    'tags':sorted(rnd.sample(['api','ui','db','ops','bug'],rnd.randint(0,3))),'priority':rnd.randint(1,5),
                    'dueDate':None if rnd.random()<.3 else f'2026-{rnd.randint(1,12):02d}-{rnd.randint(1,28):02d}'})
    return out

class Invalid(Exception):
    def __init__(self,field):self.field=field

def py_list(tasks,q):
    """Python mirror of README.md 'Listing tasks'."""
    statuses=None
    if 'status' in q:
        statuses=[s.strip() for s in q['status'].split(',')]
        if any(s not in ('todo','doing','done') for s in statuses):raise Invalid('status')
    parts=q.get('sort','priority:desc').split(':')
    if len(parts)!=2 or parts[0] not in ('dueDate','priority','title') or parts[1] not in ('asc','desc'):raise Invalid('sort')
    field,direction=parts
    def num(name,default,lo,hi):
        if name not in q:return default
        if not re.fullmatch(r'\d+',q[name]) or not lo<=int(q[name])<=hi:raise Invalid(name)
        return int(q[name])
    page=num('page',1,1,2**53-1);size=num('pageSize',20,1,100)
    needle=q.get('q','').strip().lower()
    want=None if q.get('assignee')=='none' else q.get('assignee')
    m=[t for t in tasks if (statuses is None or t['status'] in statuses) and ('assignee' not in q or t['assignee']==want)
       and ('tag' not in q or q['tag'] in t['tags']) and (not needle or needle in t['title'].lower())]
    key={'priority':lambda t:t['priority'],'title':lambda t:t['title'].lower(),'dueDate':lambda t:t['dueDate']}[field]
    present=[t for t in m if field!='dueDate' or t['dueDate'] is not None];missing=[t for t in m if t not in present]
    # stable sorts: id ascending is the tie-break in both directions
    present=sorted(sorted(present,key=lambda t:t['id']),key=key,reverse=direction=='desc')
    ordered=present+sorted(missing,key=lambda t:t['id'])
    return {'ids':[t['id'] for t in ordered[(page-1)*size:page*size]],'total':len(m),'page':page,'pageSize':size}

TS_TYPES='''export type Status = "todo" | "doing" | "done";

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
'''
TS_ERRORS='''export class ValidationError extends Error {
  readonly field: string;

  constructor(field: string, message: string) {
    super(message);
    this.name = "ValidationError";
    this.field = field;
  }
}
'''
TS_VALIDATION='''import { ValidationError } from "./errors.ts";

/** Parses an optional integer parameter: digits only, within [min, max]; `fallback` when absent. */
export function intParam(field: string, raw: string | undefined, fallback: number, min: number, max: number): number {
  if (raw === undefined) return fallback;
  if (!/^\\d+$/.test(raw)) throw new ValidationError(field, `${field} must be a whole number`);
  const value = Number(raw);
  if (value < min || value > max) throw new ValidationError(field, `${field} must be between ${min} and ${max}`);
  return value;
}
'''
TS_HTTP='''import { ValidationError } from "./errors.ts";
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
'''
TS_SERVICE='''import type { Page, Task, TaskQuery } from "./types.ts";
import { TASKS } from "./store.ts";

/** Filters, sorts and paginates tasks as described in README.md ("Listing tasks"). */
export function listTasks(query: TaskQuery, tasks: readonly Task[] = TASKS): Page<Task> {
  throw new Error("not implemented");
}
'''
TS_SERVICE_REF='''import { ValidationError } from "./errors.ts";
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
'''
TS_README='''# Task board service

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
'''

def ts_literal(t):
    return '  { '+', '.join(f'{k}: {json.dumps(v)}' for k,v in t.items())+' },'

def f8d():
    seed=ts_seed()
    store='import type { Task } from "./types.ts";\n\nexport const TASKS: readonly Task[] = [\n'+'\n'.join(ts_literal(t) for t in seed)+'\n];\n'
    cases=[('default listing',{}),('status list with due date ascending',{'status':'todo, done','sort':'dueDate:asc','pageSize':'100'}),
           ('unassigned by title',{'assignee':'none','sort':'title:asc','pageSize':'100'}),('tag and trimmed case-insensitive search',{'tag':'api','q':'  GATEWAY ','pageSize':'100'}),
           ('second page by title descending',{'sort':'title:desc','page':'2','pageSize':'7'}),('due date descending keeps missing dates last',{'status':'doing','sort':'dueDate:desc','pageSize':'100'}),
           ('assignee with priority ascending',{'assignee':'bo','sort':'priority:asc'}),('page past the end',{'page':'9','pageSize':'5'})]
    expected=[(n,q,py_list(seed,q)) for n,q in cases]
    for n,q,e in expected[:-1]:assert len(e['ids'])>=2,(n,e)
    assert expected[-1][2]['ids']==[] and expected[-1][2]['total']==40
    byid={t['id']:t for t in seed}
    assert any(byid[i]['dueDate'] is None for i in expected[5][2]['ids'])
    invalid=[({'status':'blocked'},'status'),({'status':'todo,'},'status'),({'sort':'owner:asc'},'sort'),({'sort':'priority:up'},'sort'),({'sort':'priority'},'sort'),
             ({'page':'0'},'page'),({'page':'1.5'},'page'),({'pageSize':'101'},'pageSize'),({'pageSize':''},'pageSize'),({'pageSize':'-3'},'pageSize')]
    for q,f in invalid:
        try:py_list(seed,q);raise AssertionError(q)
        except Invalid as e:assert e.field==f
    http=py_list(seed,{'assignee':'ana','pageSize':'2'})
    tests=['import { test } from "node:test";','import assert from "node:assert/strict";','import { ValidationError } from "../src/errors.ts";',
           'import { handle } from "../src/http.ts";','import { listTasks } from "../src/service.ts";','import type { TaskQuery } from "../src/types.ts";','',
           'function check(query: TaskQuery, ids: number[], total: number, page: number, pageSize: number): void {',
           '  const result = listTasks(query);','  assert.deepEqual(result.items.map((t) => t.id), ids);',
           '  assert.deepEqual([result.total, result.page, result.pageSize], [total, page, pageSize]);','}','']
    for n,q,e in expected:
        tests.append(f'test({json.dumps(n)}, () => check({json.dumps(q)}, {json.dumps(e["ids"])}, {e["total"]}, {e["page"]}, {e["pageSize"]}));')
    tests+=['','const INVALID: [TaskQuery, string][] = [']+[f'  [{json.dumps(q)}, {json.dumps(f)}],' for q,f in invalid]+['];','',
            'for (const [query, field] of INVALID) {','  test(`rejects ${JSON.stringify(query)}`, () => {',
            '    assert.throws(() => listTasks(query), (error: unknown) => error instanceof ValidationError && error.field === field);','  });','}','',
            'test("items are the stored task objects", () => {','  const [first] = listTasks({ q: "gateway" }).items;','  assert.equal(typeof first.title, "string");',
            '  assert.ok(first.title.toLowerCase().includes("gateway"));','});','','test("http handler", () => {',
            '  const ok = handle("/tasks?assignee=ana&pageSize=2");','  assert.equal(ok.status, 200);',
            f'  assert.deepEqual((ok.body as {{ items: {{ id: number }}[] }}).items.map((t) => t.id), {json.dumps(http["ids"])});',
            '  assert.deepEqual(handle("/tasks?status=bogus"), { status: 400, body: { error: "validation", field: "status" } });',
            '  assert.deepEqual(handle("/tasks?sort=title:sideways"), { status: 400, body: { error: "validation", field: "sort" } });','});']
    f={'package.json':'{\n  "name": "task-board",\n  "private": true,\n  "type": "module"\n}','README.md':TS_README,'src/types.ts':TS_TYPES,
       'src/errors.ts':TS_ERRORS,'src/validation.ts':TS_VALIDATION,'src/store.ts':store,'src/service.ts':TS_SERVICE,'src/http.ts':TS_HTTP,
       'tests/tasks.test.ts':'\n'.join(tests)}
    prompt='Implement listTasks() in src/service.ts following the "Listing tasks" contract in README.md, so the acceptance tests pass. Node 26 runs the TypeScript sources directly.'
    return f,{'src/service.ts':TS_SERVICE_REF},prompt

# ---------------------------------------------------------------- F8-E
LOAN_DAYS={'STANDARD':(3,14),'STUDENT':(5,30),'STAFF':(10,45)}
J='package lab.loans;\n\n'
JAVA={
'MemberType.java':J+'''/** Borrowing limits per membership type. */
public enum MemberType {
    STANDARD(3, 14),
    STUDENT(5, 30),
    STAFF(10, 45);

    private final int maxLoans;
    private final int loanDays;

    MemberType(int maxLoans, int loanDays) {
        this.maxLoans = maxLoans;
        this.loanDays = loanDays;
    }

    public int maxLoans() {
        return maxLoans;
    }

    public int loanDays() {
        return loanDays;
    }
}''',
'Member.java':J+'public record Member(String id, MemberType type) {\n}',
'Book.java':J+'public record Book(String isbn, String title) {\n}',
'LoanException.java':J+'''public class LoanException extends RuntimeException {
    public LoanException(String message) {
        super(message);
    }
}''',
'Loan.java':J+'''import java.time.LocalDate;

public final class Loan {
    private final String id;
    private final String memberId;
    private final String isbn;
    private final LocalDate borrowedOn;
    private LocalDate dueOn;
    private LocalDate returnedOn;
    private int renewals;

    Loan(String id, String memberId, String isbn, LocalDate borrowedOn, LocalDate dueOn) {
        this.id = id;
        this.memberId = memberId;
        this.isbn = isbn;
        this.borrowedOn = borrowedOn;
        this.dueOn = dueOn;
    }

    public String getId() {
        return id;
    }

    public String getMemberId() {
        return memberId;
    }

    public String getIsbn() {
        return isbn;
    }

    public LocalDate getBorrowedOn() {
        return borrowedOn;
    }

    public LocalDate getDueOn() {
        return dueOn;
    }

    public LocalDate getReturnedOn() {
        return returnedOn;
    }

    public int getRenewals() {
        return renewals;
    }

    public boolean isOpen() {
        return returnedOn == null;
    }

    void markReturned(LocalDate day) {
        this.returnedOn = day;
    }
}''',
'LoanRepository.java':J+'''import java.util.List;
import java.util.Optional;

public interface LoanRepository {
    void save(Loan loan);

    Optional<Loan> find(String loanId);

    List<Loan> openLoansOf(String memberId);

    Optional<Loan> openLoanFor(String isbn);
}''',
'InMemoryLoanRepository.java':J+'''import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public final class InMemoryLoanRepository implements LoanRepository {
    private final Map<String, Loan> loans = new LinkedHashMap<>();

    @Override
    public void save(Loan loan) {
        loans.put(loan.getId(), loan);
    }

    @Override
    public Optional<Loan> find(String loanId) {
        return Optional.ofNullable(loans.get(loanId));
    }

    @Override
    public List<Loan> openLoansOf(String memberId) {
        return loans.values().stream().filter(l -> l.isOpen() && l.getMemberId().equals(memberId)).toList();
    }

    @Override
    public Optional<Loan> openLoanFor(String isbn) {
        return loans.values().stream().filter(l -> l.isOpen() && l.getIsbn().equals(isbn)).findFirst();
    }
}''',
'LoanPolicy.java':J+'''import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

/**
 * Library lending policy.
 * <ul>
 *   <li>A loan is due {@link MemberType#loanDays()} days after it starts; a due date that falls on a Saturday or
 *       Sunday moves to the following Monday.</li>
 *   <li>Late fee: 0.25 for every day the book is returned after its due date (returning on the due date is free),
 *       capped at 10.00 per loan.</li>
 * </ul>
 */
public final class LoanPolicy {
    private static final BigDecimal DAILY_FEE = new BigDecimal("0.25");
    private static final BigDecimal MAX_FEE = new BigDecimal("10.00");

    public LocalDate dueDate(LocalDate start, MemberType type) {
        return nextBusinessDay(start.plusDays(type.loanDays()));
    }

    LocalDate nextBusinessDay(LocalDate day) {
        switch (day.getDayOfWeek()) {
            case SATURDAY:
            case SUNDAY:
                return day.plusDays(1);
            default:
                return day;
        }
    }

    public BigDecimal lateFee(LocalDate dueOn, LocalDate returnedOn) {
        if (!returnedOn.isAfter(dueOn)) {
            return BigDecimal.ZERO.setScale(2);
        }
        long days = ChronoUnit.DAYS.between(dueOn, returnedOn) + 1;
        return DAILY_FEE.multiply(BigDecimal.valueOf(days)).setScale(2);
    }
}''',
'LoanService.java':J+'''import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

/** Lending operations of the branch library. Dates are passed in explicitly. */
public class LoanService {
    private final LoanRepository loans;
    private final LoanPolicy policy;
    private final Map<String, Member> members = new HashMap<>();
    private int sequence;

    public LoanService(LoanRepository loans, LoanPolicy policy) {
        this.loans = loans;
        this.policy = policy;
    }

    public void register(Member member) {
        members.put(member.id(), member);
    }

    /** Lends a book. A member holds at most {@link MemberType#maxLoans()} open loans; a book is on at most one open loan. */
    public Loan borrow(String memberId, String isbn, LocalDate today) {
        Member member = member(memberId);
        if (loans.openLoansOf(memberId).size() >= member.type().maxLoans()) {
            throw new LoanException("loan limit reached for " + memberId);
        }
        if (loans.openLoanFor(isbn).isPresent()) {
            throw new LoanException("book already on loan: " + isbn);
        }
        Loan loan = new Loan("L" + (++sequence), memberId, isbn, today, policy.dueDate(today, member.type()));
        loans.save(loan);
        return loan;
    }

    /** Ends an open loan and returns the late fee owed (zero when on time). */
    public BigDecimal giveBack(String loanId, LocalDate today) {
        Loan loan = open(loanId);
        loan.markReturned(today);
        loans.save(loan);
        return policy.lateFee(loan.getDueOn(), today);
    }

    /**
     * Renews an open loan once. The new due date is the current due date plus the member type's loan days,
     * moved to the following Monday when it falls on a weekend. Renewing on the due date itself is allowed.
     *
     * @throws LoanException when the loan does not exist, was returned, is overdue on {@code today},
     *                       or has already been renewed
     */
    public Loan renew(String loanId, LocalDate today) {
        throw new UnsupportedOperationException("not implemented");
    }

    private Member member(String memberId) {
        Member member = members.get(memberId);
        if (member == null) {
            throw new LoanException("unknown member " + memberId);
        }
        return member;
    }

    private Loan open(String loanId) {
        Loan loan = loans.find(loanId).orElseThrow(() -> new LoanException("unknown loan " + loanId));
        if (!loan.isOpen()) {
            throw new LoanException("loan already returned: " + loanId);
        }
        return loan;
    }
}''',
}
RUN_SH=f'''#!/bin/sh
# Compiles the sources and the acceptance tests with Java 21, then runs JUnit 5 (no Maven, no network).
set -eu
JDK={JDK}
CP='{JUNIT}/*'
rm -rf build
mkdir -p build/main build/test
"$JDK/javac" -J-XX:-UsePerfData -d build/main $(find src/main/java -name '*.java')
"$JDK/javac" -J-XX:-UsePerfData -d build/test -cp "build/main:$CP" $(find tests -name '*.java')
exec "$JDK/java" -XX:-UsePerfData -cp "build/main:build/test:$CP" LabTestMain'''
LAB_MAIN='''import java.io.PrintWriter;

import org.junit.platform.launcher.LauncherDiscoveryRequest;
import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
import org.junit.platform.launcher.core.LauncherFactory;
import org.junit.platform.launcher.listeners.SummaryGeneratingListener;
import org.junit.platform.launcher.listeners.TestExecutionSummary;

import static org.junit.platform.engine.discovery.DiscoverySelectors.selectPackage;

/** Minimal JUnit Platform console: runs every test in package lab.loans; exit code 0 only when all pass. */
public class LabTestMain {
    public static void main(String[] args) {
        LauncherDiscoveryRequest request = LauncherDiscoveryRequestBuilder.request().selectors(selectPackage("lab.loans")).build();
        SummaryGeneratingListener listener = new SummaryGeneratingListener();
        LauncherFactory.create().execute(request, listener);
        TestExecutionSummary summary = listener.getSummary();
        PrintWriter out = new PrintWriter(System.out);
        summary.printTo(out);
        summary.printFailuresTo(out, 15);
        out.flush();
        System.exit(summary.getTotalFailureCount() == 0 && summary.getTestsFoundCount() > 0 ? 0 : 1);
    }
}'''

def next_business(d):
    return d+timedelta(days={5:2,6:1}.get(d.weekday(),0))

def f8e():
    start=date(2026,3,2);assert start.weekday()==0
    due=lambda d,t:next_business(d+timedelta(days=LOAN_DAYS[t][1]))
    find=lambda pred:next(start+timedelta(days=i) for i in range(400) if pred(start+timedelta(days=i)))
    sat=find(lambda d:(d+timedelta(days=14)).weekday()==5)  # STANDARD due on a Saturday
    sun=find(lambda d:(d+timedelta(days=30)).weekday()==6)  # STUDENT due on a Sunday
    staff_sat=find(lambda d:(d+timedelta(days=45)).weekday()==5)
    ren=find(lambda d:(due(d,'STUDENT')+timedelta(days=30)).weekday()==5)  # STUDENT renewal lands on a Saturday
    d0=due(start,'STANDARD');assert d0==date(2026,3,16)
    fee=lambda days:min(days*0.25,10.0)
    q=lambda d:f'd("{d.isoformat()}")'
    tests=f'''package lab.loans;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.math.BigDecimal;
import java.time.LocalDate;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class LoanServiceTest {{
    private LoanService service;

    private static LocalDate d(String iso) {{
        return LocalDate.parse(iso);
    }}

    private static void assertMoney(String expected, BigDecimal actual) {{
        assertEquals(0, new BigDecimal(expected).compareTo(actual), () -> "expected " + expected + " but was " + actual);
    }}

    @BeforeEach
    void setUp() {{
        service = new LoanService(new InMemoryLoanRepository(), new LoanPolicy());
        service.register(new Member("std", MemberType.STANDARD));
        service.register(new Member("stu", MemberType.STUDENT));
        service.register(new Member("staff", MemberType.STAFF));
    }}

    @Test
    void weekdayDueDateIsKept() {{
        assertEquals({q(d0)}, service.borrow("std", "isbn-1", {q(start)}).getDueOn());
    }}

    @Test
    void saturdayDueDateMovesToMonday() {{
        assertEquals({q(due(sat,'STANDARD'))}, service.borrow("std", "isbn-1", {q(sat)}).getDueOn());
        assertEquals({q(due(staff_sat,'STAFF'))}, service.borrow("staff", "isbn-2", {q(staff_sat)}).getDueOn());
    }}

    @Test
    void sundayDueDateMovesToMonday() {{
        assertEquals({q(due(sun,'STUDENT'))}, service.borrow("stu", "isbn-1", {q(sun)}).getDueOn());
    }}

    @Test
    void returningOnTheDueDateIsFree() {{
        Loan loan = service.borrow("std", "isbn-1", {q(start)});
        assertMoney("0.00", service.giveBack(loan.getId(), {q(d0)}));
    }}

    @Test
    void lateFeeCountsDaysAfterTheDueDate() {{
        Loan one = service.borrow("std", "isbn-1", {q(start)});
        Loan ten = service.borrow("std", "isbn-2", {q(start)});
        assertMoney("{fee(1):.2f}", service.giveBack(one.getId(), {q(d0+timedelta(days=1))}));
        assertMoney("{fee(10):.2f}", service.giveBack(ten.getId(), {q(d0+timedelta(days=10))}));
    }}

    @Test
    void lateFeeIsCapped() {{
        Loan loan = service.borrow("std", "isbn-1", {q(start)});
        assertMoney("{fee(77):.2f}", service.giveBack(loan.getId(), {q(d0+timedelta(days=77))}));
    }}

    @Test
    void memberTypeLimitsOpenLoans() {{
        Loan first = service.borrow("std", "isbn-1", {q(start)});
        service.borrow("std", "isbn-2", {q(start)});
        service.borrow("std", "isbn-3", {q(start)});
        assertThrows(LoanException.class, () -> service.borrow("std", "isbn-4", {q(start)}));
        service.giveBack(first.getId(), {q(start+timedelta(days=1))});
        service.borrow("std", "isbn-4", {q(start+timedelta(days=1))});
    }}

    @Test
    void bookIsLentOnceAtATime() {{
        service.borrow("std", "isbn-1", {q(start)});
        assertThrows(LoanException.class, () -> service.borrow("stu", "isbn-1", {q(start)}));
    }}

    @Test
    void renewExtendsFromTheCurrentDueDate() {{
        Loan loan = service.borrow("std", "isbn-1", {q(start)});
        Loan renewed = service.renew(loan.getId(), {q(start+timedelta(days=8))});
        assertEquals({q(next_business(d0+timedelta(days=14)))}, renewed.getDueOn());
        assertEquals(1, renewed.getRenewals());
        Loan student = service.borrow("stu", "isbn-2", {q(start)});
        assertEquals({q(next_business(due(start,'STUDENT')+timedelta(days=30)))}, service.renew(student.getId(), {q(start)}).getDueOn());
    }}

    @Test
    void renewalOnTheDueDateIsAllowed() {{
        Loan loan = service.borrow("std", "isbn-1", {q(start)});
        assertEquals({q(next_business(d0+timedelta(days=14)))}, service.renew(loan.getId(), {q(d0)}).getDueOn());
    }}

    @Test
    void renewalMovesWeekendDueDateToMonday() {{
        Loan loan = service.borrow("stu", "isbn-1", {q(ren)});
        assertEquals({q(due(ren,'STUDENT'))}, loan.getDueOn());
        assertEquals({q(next_business(due(ren,'STUDENT')+timedelta(days=30)))}, service.renew(loan.getId(), {q(ren)}).getDueOn());
    }}

    @Test
    void renewOnlyOnce() {{
        Loan loan = service.borrow("std", "isbn-1", {q(start)});
        service.renew(loan.getId(), {q(start)});
        assertThrows(LoanException.class, () -> service.renew(loan.getId(), {q(start)}));
    }}

    @Test
    void overdueLoansCannotBeRenewed() {{
        Loan loan = service.borrow("std", "isbn-1", {q(start)});
        assertThrows(LoanException.class, () -> service.renew(loan.getId(), {q(d0+timedelta(days=1))}));
        assertEquals({q(d0)}, loan.getDueOn());
    }}

    @Test
    void returnedOrUnknownLoansCannotBeRenewed() {{
        Loan loan = service.borrow("std", "isbn-1", {q(start)});
        service.giveBack(loan.getId(), {q(start)});
        assertThrows(LoanException.class, () -> service.renew(loan.getId(), {q(start)}));
        assertThrows(LoanException.class, () -> service.renew("L999", {q(start)}));
    }}
}}'''
    f={f'src/main/java/lab/loans/{k}':v for k,v in JAVA.items()}
    f.update({'tests/run.sh':RUN_SH,'tests/LabTestMain.java':LAB_MAIN,'tests/lab/loans/LoanServiceTest.java':tests})
    ref={'src/main/java/lab/loans/LoanPolicy.java':sub(sub(sub(JAVA['LoanPolicy.java'],'''            case SATURDAY:
            case SUNDAY:
                return day.plusDays(1);''','''            case SATURDAY:
                return day.plusDays(2);
            case SUNDAY:
                return day.plusDays(1);'''),' + 1;',';'),'.setScale(2);\n    }\n}','.setScale(2).min(MAX_FEE);\n    }\n}'),
         'src/main/java/lab/loans/Loan.java':sub(JAVA['Loan.java'],'''    void markReturned(LocalDate day) {''','''    void renew(LocalDate newDueOn) {
        this.dueOn = newDueOn;
        this.renewals++;
    }

    void markReturned(LocalDate day) {'''),
         'src/main/java/lab/loans/LoanService.java':sub(JAVA['LoanService.java'],'''        throw new UnsupportedOperationException("not implemented");''','''        Loan loan = open(loanId);
        if (today.isAfter(loan.getDueOn())) {
            throw new LoanException("loan is overdue: " + loanId);
        }
        if (loan.getRenewals() > 0) {
            throw new LoanException("loan already renewed: " + loanId);
        }
        MemberType type = member(loan.getMemberId()).type();
        loan.renew(policy.nextBusinessDay(loan.getDueOn().plusDays(type.loanDays())));
        loans.save(loan);
        return loan;''')}
    prompt=('The library lending code in src/main/java/lab/loans is wrong about weekend due dates and late fees, and LoanService.renew() is not implemented. '
            'Fix it so the code follows the Javadoc of LoanPolicy and LoanService and the acceptance tests pass. Java 21; tests/run.sh compiles and runs JUnit 5 without Maven.')
    return f,ref,prompt

# ---------------------------------------------------------------- F8-F
MIGRATE='''"""Forward-only SQLite migrations: db/migrations/NNN_name.sql, applied once each, in version order."""
import pathlib

MIGRATIONS = pathlib.Path(__file__).resolve().parent / "db" / "migrations"


def _ensure(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")


def applied(conn):
    _ensure(conn)
    return [row[0] for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]


def apply_file(conn, path):
    """Apply one migration file atomically and record its version (the digits before the first underscore)."""
    path = pathlib.Path(path)
    version = path.name.split("_", 1)[0]
    if not version.isdigit():
        raise ValueError(f"bad migration name: {path.name}")
    _ensure(conn)
    try:
        conn.executescript(f"BEGIN;\\n{path.read_text()}\\nINSERT INTO schema_migrations (version) VALUES ('{version}');\\nCOMMIT;")
    except Exception:
        conn.rollback()
        raise
    return version


def apply_all(conn, directory=MIGRATIONS):
    """Apply every pending migration in `directory`; return the versions applied by this call."""
    done = set(applied(conn))
    return [apply_file(conn, path) for path in sorted(pathlib.Path(directory).glob("*.sql")) if path.name.split("_", 1)[0] not in done]
'''
REPORTS='''"""Sales reports. Amounts are integer cents."""


def monthly_revenue(conn, year):
    """Revenue of every month of `year`: twelve ("YYYY-MM", cents) pairs in calendar order, 0 for months without sales."""
    rows = conn.execute(
        "SELECT strftime('%Y-%m', ordered_on) AS month, SUM(total_cents) FROM orders "
        "WHERE strftime('%Y', ordered_on) = ? GROUP BY month ORDER BY month",
        (str(year),),
    ).fetchall()
    return [(month, total) for month, total in rows]


def top_customers(conn, limit=3):
    """Customers by total amount ordered (all time), highest first, ties by name: [(name, cents)]."""
    return conn.execute(
        "SELECT c.name, SUM(o.total_cents) AS total FROM customers c "
        "JOIN orders o ON o.customer_id = c.id "
        "JOIN payments p ON p.order_id = o.id "
        "GROUP BY c.id ORDER BY total DESC, c.name LIMIT ?",
        (limit,),
    ).fetchall()
'''
REPORTS_REF='''"""Sales reports. Amounts are integer cents."""


def monthly_revenue(conn, year):
    """Revenue of every month of `year`: twelve ("YYYY-MM", cents) pairs in calendar order, 0 for months without sales."""
    totals = dict(conn.execute(
        "SELECT strftime('%Y-%m', ordered_on), SUM(total_cents) FROM orders "
        "WHERE strftime('%Y', ordered_on) = ? AND status = 'paid' GROUP BY 1",
        (str(year),),
    ).fetchall())
    return [(f"{year}-{m:02d}", totals.get(f"{year}-{m:02d}", 0)) for m in range(1, 13)]


def top_customers(conn, limit=3):
    """Customers by total amount ordered (all time), highest first, ties by name: [(name, cents)]."""
    return conn.execute(
        "SELECT c.name, SUM(o.total_cents) AS total FROM customers c "
        "JOIN orders o ON o.customer_id = c.id WHERE o.status = 'paid' "
        "GROUP BY c.id ORDER BY total DESC, c.name LIMIT ?",
        (limit,),
    ).fetchall()
'''
ORDERS_SQL="CREATE TABLE orders (\n    id INTEGER PRIMARY KEY,\n    customer_id INTEGER NOT NULL REFERENCES customers(id),\n    ordered_on TEXT NOT NULL, -- YYYY-MM-DD\n    total_cents INTEGER NOT NULL CHECK (total_cents >= 0)\n);\nCREATE INDEX orders_by_date ON orders(ordered_on);"
# D061 negative control: the shortcut the prompt forbids (edit released 002, backfill-only 004) must fail.
NEGATIVES={'F8-F':{'neg-edit-released':{'db/migrations/002_orders.sql':ORDERS_SQL.replace("CHECK (total_cents >= 0)\n","CHECK (total_cents >= 0),\n    status TEXT NOT NULL DEFAULT 'paid' CHECK (status IN ('paid', 'refunded'))\n"),
                                        'db/migrations/004_order_status.sql':"UPDATE orders SET status = 'refunded' WHERE id IN (SELECT order_id FROM payments WHERE kind = 'refund');",
                                        'reports.py':REPORTS_REF}}}
SEED=[(1,'Ada'),(2,'Bruno'),(3,'Chen'),(4,'Dalia'),(5,'Eve')]
ORDERS=[(1,1,'2026-01-15',12000,[('charge',12000)]),(2,1,'2026-03-02',5000,[('charge',2500),('charge',2500)]),
        (3,2,'2026-03-20',9000,[('charge',9000),('refund',9000)]),(4,2,'2026-07-01',7000,[('charge',3500),('charge',3500)]),
        (5,3,'2026-07-31',15000,[('charge',15000)]),(6,4,'2025-12-31',99999,[('charge',99999)]),(7,4,'2026-11-11',4000,[('charge',4000)]),
        (8,3,'2026-03-05',1000,[('charge',1000)]),(9,5,'2026-05-09',7000,[('charge',7000)])]

def f8f():
    refunded={o for o,_,_,_,p in ORDERS if any(k=='refund' for k,_ in p)}
    month={}
    for o,c,d,cents,_ in ORDERS:
        if d.startswith('2026') and o not in refunded:month[d[:7]]=month.get(d[:7],0)+cents
    monthly=[(f'2026-{m:02d}',month.get(f'2026-{m:02d}',0)) for m in range(1,13)]
    names=dict(SEED);tot={}
    for o,c,_,cents,_ in ORDERS:
        if o not in refunded:tot[names[c]]=tot.get(names[c],0)+cents
    top=sorted(tot.items(),key=lambda kv:(-kv[1],kv[0]))
    assert top[3][1]==top[4][1]  # a tie resolved by name
    seed=('\n'.join(f'INSERT INTO customers (id, name) VALUES ({i}, \'{n}\');' for i,n in SEED)+'\n'
          +'\n'.join(f"INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES ({o}, {c}, '{d}', {cents});" for o,c,d,cents,_ in ORDERS)+'\n'
          +'\n'.join(f"INSERT INTO payments (order_id, kind, amount_cents) VALUES ({o}, '{k}', {a});" for o,_,_,_,p in ORDERS for k,a in p))
    mig={'db/migrations/001_customers.sql':'CREATE TABLE customers (\n    id INTEGER PRIMARY KEY,\n    name TEXT NOT NULL UNIQUE\n);',
         'db/migrations/002_orders.sql':ORDERS_SQL,
         'db/migrations/003_payments.sql':"CREATE TABLE payments (\n    id INTEGER PRIMARY KEY,\n    order_id INTEGER NOT NULL REFERENCES orders(id),\n    kind TEXT NOT NULL CHECK (kind IN ('charge', 'refund')),\n    amount_cents INTEGER NOT NULL\n);"}
    # write() stores text.strip()+'\n'; released migrations are pinned by hash so editing them cannot pass (D061).
    released={k.split('/')[-1]:hashlib.sha256((v.strip()+'\n').encode()).hexdigest() for k,v in mig.items()}
    tests=f'''import hashlib
import sqlite3

import pytest

import migrate
import reports

LEGACY = ["001_customers.sql", "002_orders.sql", "003_payments.sql"]
RELEASED = {released!r}
SEED = """
{seed}
"""


@pytest.fixture
def db():
    """A production-like database created before migration 004, then upgraded."""
    conn = sqlite3.connect(":memory:")
    for name in LEGACY:
        migrate.apply_file(conn, migrate.MIGRATIONS / name)
    conn.executescript(SEED)
    assert migrate.apply_all(conn) == ["004"]
    return conn


def test_released_migrations_are_unchanged():
    for name, digest in RELEASED.items():
        assert hashlib.sha256((migrate.MIGRATIONS / name).read_bytes()).hexdigest() == digest, f"{{name}} was already released"


def test_fresh_database_gets_every_migration_once():
    conn = sqlite3.connect(":memory:")
    assert migrate.apply_all(conn) == ["001", "002", "003", "004"]
    assert migrate.applied(conn) == ["001", "002", "003", "004"]
    assert migrate.apply_all(conn) == []


def test_status_is_backfilled(db):
    status = dict(db.execute("SELECT id, status FROM orders"))
    assert status == {{{', '.join(f'{o}: {"refunded" if o in refunded else "paid"!r}' for o,*_ in ORDERS)}}}


def test_new_orders_default_to_paid(db):
    db.execute("INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (50, 1, '2026-12-01', 100)")
    assert db.execute("SELECT status FROM orders WHERE id = 50").fetchone() == ("paid",)


def test_status_values_are_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO orders (id, customer_id, ordered_on, total_cents, status) VALUES (51, 1, '2026-12-01', 100, 'lost')")


def test_monthly_revenue_lists_every_month(db):
    assert reports.monthly_revenue(db, 2026) == {monthly!r}


def test_top_customers(db):
    assert reports.top_customers(db, 3) == {top[:3]!r}
    assert reports.top_customers(db, 5) == {top!r}
'''
    f={**mig,'migrate.py':MIGRATE,'reports.py':REPORTS,'tests/__init__.py':'','tests/test_reports.py':tests}
    ref={'db/migrations/004_order_status.sql':"ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'paid' CHECK (status IN ('paid', 'refunded'));\nUPDATE orders SET status = 'refunded' WHERE id IN (SELECT order_id FROM payments WHERE kind = 'refund');",
         'reports.py':REPORTS_REF}
    prompt=('Add migration db/migrations/004_order_status.sql: orders get a status column, either paid or refunded (enforced by the database, default paid); '
            'existing orders that have a refund payment become refunded. Refunded orders must not count in reports.py. '
            'The reports are also wrong today: monthly_revenue omits months and top_customers overstates some customers. '
            'Existing databases are upgraded with migrate.apply_all; never edit migrations that were already released.')
    return f,ref,prompt

# ---------------------------------------------------------------- F8-G
CS_PROGRAM='''var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton<ProductStore>();
var app = builder.Build();

app.MapGet("/products/{id:int}", (int id, ProductStore store) =>
    store.Find(id) is { } product ? Results.Ok(product) : Results.NotFound());

app.MapPost("/products", (ProductInput input, ProductStore store) =>
{
    var errors = ProductValidation.Validate(input);
    if (errors.Count > 0) return Results.ValidationProblem(errors);
    var product = store.Add(input);
    return Results.Created($"/products/{product.Id}", product);
});

// Update contract: see README.md.
app.MapPut("/products/{id:int}", (int id, ProductInput input, ProductStore store) =>
    Results.StatusCode(StatusCodes.Status501NotImplemented));

app.Run();

public partial class Program { }'''
CS_PRODUCTS='''public record ProductInput(string? Name, decimal Price, int Stock, int? Version);

public record Product(int Id, string Name, decimal Price, int Stock, int Version);

public class ProductStore
{
    private readonly object gate = new();
    private readonly Dictionary<int, Product> products = new();
    private int nextId = 1;

    public Product? Find(int id)
    {
        lock (gate) return products.GetValueOrDefault(id);
    }

    public Product Add(ProductInput input)
    {
        lock (gate)
        {
            var product = new Product(nextId++, input.Name!.Trim(), input.Price, input.Stock, 1);
            products[product.Id] = product;
            return product;
        }
    }
}

public static class ProductValidation
{
    public static Dictionary<string, string[]> Validate(ProductInput input)
    {
        var errors = new Dictionary<string, string[]>();
        if (string.IsNullOrWhiteSpace(input.Name) || input.Name.Trim().Length > 80)
            errors["name"] = ["Name is required and has at most 80 characters."];
        if (input.Price < 0)
            errors["price"] = ["Price must not be negative."];
        if (input.Stock is < 0 or > 10000)
            errors["stock"] = ["Stock must be between 0 and 10000."];
        return errors;
    }
}'''
CS_README='''# Products API

`PUT /products/{id}` replaces a product's editable fields. Body: `{ "name", "price", "stock", "version" }`.

1. 404 Not Found when no product has this id.
2. 400 (validation problem) when the body breaks the same rules as POST (name not blank and at most 80
   characters after trimming, price >= 0, stock from 0 to 10000) or when `version` is missing.
3. 409 Conflict when `version` differs from the stored version (another client updated the product first);
   nothing changes.
4. Otherwise the product is updated in place: same id, name trimmed, new price and stock, version + 1.
   Respond 200 with the updated product.
'''
CS_TESTS='''using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

public class ProductUpdateTests : IClassFixture<WebApplicationFactory<Program>>
{
    readonly HttpClient client;

    public ProductUpdateTests(WebApplicationFactory<Program> app) { client = app.CreateClient(); }

    async Task<int> Create(string name = "Lamp", decimal price = 10m, int stock = 5)
    {
        var r = await client.PostAsJsonAsync("/products", new { name, price, stock });
        Assert.Equal(HttpStatusCode.Created, r.StatusCode);
        return (await r.Content.ReadFromJsonAsync<JsonElement>()).GetProperty("id").GetInt32();
    }

    Task<JsonElement> Get(int id) => client.GetFromJsonAsync<JsonElement>($"/products/{id}");

    [Fact]
    public async Task UpdateReplacesFieldsAndBumpsVersion()
    {
        var id = await Create();
        var r = await client.PutAsJsonAsync($"/products/{id}", new { name = "  Desk lamp ", price = 12.5m, stock = 4, version = 1 });
        Assert.Equal(HttpStatusCode.OK, r.StatusCode);
        var j = await r.Content.ReadFromJsonAsync<JsonElement>();
        Assert.Equal(id, j.GetProperty("id").GetInt32());
        Assert.Equal("Desk lamp", j.GetProperty("name").GetString());
        Assert.Equal(12.5m, j.GetProperty("price").GetDecimal());
        Assert.Equal(4, j.GetProperty("stock").GetInt32());
        Assert.Equal(2, j.GetProperty("version").GetInt32());
        var stored = await Get(id);
        Assert.Equal("Desk lamp", stored.GetProperty("name").GetString());
        Assert.Equal(2, stored.GetProperty("version").GetInt32());
    }

    [Fact]
    public async Task BoundaryValuesAreAccepted()
    {
        var id = await Create();
        var r = await client.PutAsJsonAsync($"/products/{id}", new { name = new string('n', 80), price = 0m, stock = 10000, version = 1 });
        Assert.Equal(HttpStatusCode.OK, r.StatusCode);
    }

    [Fact]
    public async Task MissingProductIsNotFound()
    {
        var r = await client.PutAsJsonAsync("/products/987654", new { name = "Lamp", price = 1m, stock = 1, version = 1 });
        Assert.Equal(HttpStatusCode.NotFound, r.StatusCode);
    }

    [Theory]
    [InlineData("", 1.0, 1)]
    [InlineData("   ", 1.0, 1)]
    [InlineData("TOO-LONG", 1.0, 1)]
    [InlineData("Lamp", -0.01, 1)]
    [InlineData("Lamp", 1.0, -1)]
    [InlineData("Lamp", 1.0, 10001)]
    public async Task InvalidUpdateIsRejectedAndChangesNothing(string name, double price, int stock)
    {
        var id = await Create();
        if (name == "TOO-LONG") name = new string('x', 81);
        var r = await client.PutAsJsonAsync($"/products/{id}", new { name, price = (decimal)price, stock, version = 1 });
        Assert.Equal(HttpStatusCode.BadRequest, r.StatusCode);
        var stored = await Get(id);
        Assert.Equal("Lamp", stored.GetProperty("name").GetString());
        Assert.Equal(1, stored.GetProperty("version").GetInt32());
    }

    [Fact]
    public async Task MissingVersionIsBadRequest()
    {
        var id = await Create();
        var r = await client.PutAsJsonAsync($"/products/{id}", new { name = "Lamp", price = 1m, stock = 1 });
        Assert.Equal(HttpStatusCode.BadRequest, r.StatusCode);
    }

    [Fact]
    public async Task StaleVersionIsConflict()
    {
        var id = await Create();
        var first = await client.PutAsJsonAsync($"/products/{id}", new { name = "First", price = 1m, stock = 1, version = 1 });
        Assert.Equal(HttpStatusCode.OK, first.StatusCode);
        var second = await client.PutAsJsonAsync($"/products/{id}", new { name = "Second", price = 2m, stock = 2, version = 1 });
        Assert.Equal(HttpStatusCode.Conflict, second.StatusCode);
        var stored = await Get(id);
        Assert.Equal("First", stored.GetProperty("name").GetString());
        Assert.Equal(2, stored.GetProperty("version").GetInt32());
    }

    [Fact]
    public async Task CreateStillValidates()
    {
        var r = await client.PostAsJsonAsync("/products", new { name = " ", price = 1m, stock = 1 });
        Assert.Equal(HttpStatusCode.BadRequest, r.StatusCode);
    }
}'''

def f8g():
    f={'README.md':CS_README,'src/App.csproj':'<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup><TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings></PropertyGroup></Project>',
       'src/Program.cs':CS_PROGRAM,'src/Products.cs':CS_PRODUCTS,
       'tests/Acceptance.csproj':'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><IsTestProject>true</IsTestProject><ImplicitUsings>enable</ImplicitUsings></PropertyGroup><ItemGroup><PackageReference Include="Microsoft.AspNetCore.Mvc.Testing" Version="10.0.1"/><PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.14.1"/><PackageReference Include="xunit" Version="2.9.3"/><PackageReference Include="xunit.runner.visualstudio" Version="3.1.1"/><ProjectReference Include="../src/App.csproj"/></ItemGroup></Project>',
       'tests/ProductUpdateTests.cs':CS_TESTS}
    ref={'src/Program.cs':sub(CS_PROGRAM,'''app.MapPut("/products/{id:int}", (int id, ProductInput input, ProductStore store) =>
    Results.StatusCode(StatusCodes.Status501NotImplemented));''','''app.MapPut("/products/{id:int}", (int id, ProductInput input, ProductStore store) =>
{
    if (store.Find(id) is null) return Results.NotFound();
    var errors = ProductValidation.Validate(input);
    if (input.Version is null) errors["version"] = ["Version is required."];
    if (errors.Count > 0) return Results.ValidationProblem(errors);
    var (outcome, product) = store.Update(id, input);
    return outcome switch
    {
        UpdateOutcome.Updated => Results.Ok(product),
        UpdateOutcome.NotFound => Results.NotFound(),
        _ => Results.Conflict(),
    };
});'''),
         'src/Products.cs':sub(CS_PRODUCTS,'''            return product;
        }
    }
}''','''            return product;
        }
    }

    public (UpdateOutcome Outcome, Product? Product) Update(int id, ProductInput input)
    {
        lock (gate)
        {
            if (!products.TryGetValue(id, out var current)) return (UpdateOutcome.NotFound, null);
            if (input.Version != current.Version) return (UpdateOutcome.Conflict, current);
            var updated = current with { Name = input.Name!.Trim(), Price = input.Price, Stock = input.Stock, Version = current.Version + 1 };
            products[id] = updated;
            return (UpdateOutcome.Updated, updated);
        }
    }
}

public enum UpdateOutcome { Updated, NotFound, Conflict }''')}
    prompt='Implement PUT /products/{id} in the ASP.NET Core API (src/) following the contract in README.md, with optimistic concurrency on version, so the acceptance tests pass.'
    return f,ref,prompt
