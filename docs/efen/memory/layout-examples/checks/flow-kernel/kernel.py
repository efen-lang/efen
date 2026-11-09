"""Small symbolic FLOW experiment. Not the efen compiler or its complete model.

The IR has no arbitrary assumptions, user summaries, loops, pointer fields, or
implicit cleanup. Every allocation failure and resource transfer is explicit.
Run verify.py; see ../../../flow-kernel.md for the semantics and limitations.
"""

from dataclasses import dataclass, field, replace
from pathlib import Path
import re

import z3 as z


DEAD, SOURCE, LOCAL, OUT = range(4)
INT, BOOL = z.IntSort(), z.BoolSort()


@dataclass(frozen=True)
class Heap:
    epoch: object
    source: object
    live: object
    init: object
    owner: object
    lent: object
    value: object

    @classmethod
    def empty(cls):
        return cls(z.IntVal(0), z.BoolVal(True), z.K(INT, False),
                   z.K(INT, False), z.K(INT, DEAD), z.K(INT, False), z.K(INT, 0))

    @classmethod
    def symbolic(cls, prefix):
        return cls(z.Int(prefix + '_epoch'), z.Bool(prefix + '_source'),
                   z.Array(prefix + '_live', INT, BOOL),
                   z.Array(prefix + '_init', INT, BOOL),
                   z.Array(prefix + '_owner', INT, INT),
                   z.Array(prefix + '_lent', INT, BOOL),
                   z.Array(prefix + '_value', INT, INT))


def wf(h, i):
    """Pointwise invariant; WF(H) means forall i: wf(H, i)."""
    return z.And(h.epoch >= 0, h.owner[i] >= DEAD, h.owner[i] <= OUT,
                 h.live[i] == (h.owner[i] != DEAD),
                 z.Implies(h.live[i], z.And(i > 0, i <= h.epoch)),
                 z.Implies(h.init[i], h.live[i]),
                 z.Implies(h.owner[i] == SOURCE, z.And(h.source, h.init[i])),
                 z.Implies(h.lent[i], z.And(h.source, h.owner[i] == SOURCE)))


def patch(h, i, **fields):
    return replace(h, **{name: z.Store(getattr(h, name), i, value)
                         for name, value in fields.items()})


def transition(op, h, i=None, value=None):
    """Return (required precondition, post-heap). No solver assumptions here."""
    if op == 'alloc':
        i = h.epoch + 1
        return z.BoolVal(True), replace(
            patch(h, i, live=True, init=False, owner=LOCAL, lent=False), epoch=i)
    if op == 'close_source':
        q = z.Int('close_source_q')
        return z.And(h.source, z.ForAll(q, h.owner[q] != SOURCE)), replace(h, source=z.BoolVal(False))
    own = z.And(h.live[i], h.owner[i] == LOCAL, z.Not(h.lent[i]))
    src = z.And(h.source, h.live[i], h.owner[i] == SOURCE, h.init[i])
    if op == 'init':
        return z.And(own, z.Not(h.init[i])), patch(h, i, init=True, value=value)
    if op == 'publish':
        return z.And(own, h.init[i], h.source), patch(h, i, owner=SOURCE)
    if op == 'reclaim':
        return z.And(src, z.Not(h.lent[i])), patch(h, i, owner=LOCAL)
    if op == 'lend':
        return z.And(src, z.Not(h.lent[i])), patch(h, i, lent=True)
    if op == 'release':
        return z.And(src, h.lent[i]), patch(h, i, lent=False)
    if op == 'free':
        # Payload is a scalar without a destructor; freeing uninitialized
        # storage is valid. This is not a general resource-bearing destructor.
        return own, patch(h, i, live=False, init=False, owner=DEAD, lent=False)
    if op == 'export':
        # Each object has independent backing storage. No area-backed escape.
        return z.And(own, h.init[i]), patch(h, i, owner=OUT)
    if op == 'write_source':
        return z.And(src, z.Not(h.lent[i])), patch(h, i, value=value)
    if op == 'read_own':
        return z.And(own, h.init[i]), h
    if op == 'read_loan':
        return z.And(src, h.lent[i]), h
    raise ValueError('unsupported primitive: ' + op)


class Rejected(Exception):
    pass


class Proofs:
    def __init__(self, directory=None, timeout_ms=5000):
        self.count = 0
        self.records = []
        self.directory = Path(directory) if directory else None
        self.timeout_ms = timeout_ms
        if self.directory:
            self.directory.mkdir(parents=True, exist_ok=True)

    def solver(self, assumptions):
        s = z.Solver()
        s.set(timeout=self.timeout_ms)
        s.add(*assumptions)
        return s

    @staticmethod
    def require_unsat(result, name, model=''):
        if result != z.unsat:
            # sat gives a counterexample; unknown/timeouts never give permission.
            raise Rejected(f'{name}: {result}' + (f'\n{model}' if model else ''))

    def prove(self, name, assumptions, goal):
        s = self.solver(assumptions)
        s.add(z.Not(goal))
        self.count += 1
        if self.directory:
            safe = re.sub(r'[^A-Za-z0-9_.-]', '_', name)
            (self.directory / f'{self.count:04d}_{safe}.smt2').write_text(s.to_smt2())
        result = s.check()
        self.records.append({'name': name, 'result': str(result)})
        self.require_unsat(result, name, str(s.model()) if result == z.sat else s.reason_unknown())

    def feasible(self, assumptions, name):
        s = self.solver(assumptions)
        result = s.check()
        if result == z.unknown:
            raise Rejected(f'{name}: unknown reachability: {s.reason_unknown()}')
        return result == z.sat


@dataclass(frozen=True)
class Binding:
    kind: str  # own, loan, read
    obj: object
    cap: int


@dataclass
class State:
    heap: Heap
    facts: list = field(default_factory=list)
    env: dict = field(default_factory=dict)
    ids: dict = field(default_factory=dict)  # source identities, NOT read rights
    ambient_loans: object = field(default_factory=lambda: z.K(INT, False))
    returned_loans: list = field(default_factory=list)
    returned_owns: list = field(default_factory=list)
    next_cap: int = 0

    def copy(self):
        return replace(self, facts=self.facts[:], env=self.env.copy(), ids=self.ids.copy(),
                       returned_loans=self.returned_loans[:], returned_owns=self.returned_owns[:])


@dataclass(frozen=True)
class Branch:
    condition: object
    yes: tuple
    no: tuple


@dataclass(frozen=True)
class Allocate:
    name: str
    success: tuple
    failure: tuple


@dataclass(frozen=True)
class Exit:
    outcome: str  # return or throw
    outputs: tuple = ()


@dataclass(frozen=True)
class Endpoint:
    outcome: str
    state: State


class Verifier:
    """Path-sensitive checker for finite structured CFGs; no invariant inference."""
    def __init__(self, proofs, name, step=transition):
        self.proofs, self.name, self.step = proofs, name, step
        self.ends = []

    def need(self, s, goal, label):
        self.proofs.prove(self.name + '.' + label, s.facts, goal)
        s.facts.append(goal)  # only a proved fact enters the path state

    def binding(self, s, name, kind=None):
        b = s.env.get(name)
        if b is None or (kind and b.kind != kind):
            raise Rejected(f'{self.name}: unavailable {kind or "binding"} {name}')
        return b

    def fresh_name(self, s, name):
        if name in s.env or name in s.ids:
            raise Rejected(f'{self.name}: overwriting binding {name}')

    def add_token(self, s, name, kind, obj):
        self.fresh_name(s, name)
        s.next_cap += 1
        s.env[name] = Binding(kind, obj, s.next_cap)

    def unborrowed(self, s, b):
        if any(r.kind == 'read' and r.cap == b.cap for r in s.env.values()):
            raise Rejected(f'{self.name}: active read borrow of capability {b.cap}')

    def apply(self, s, op, obj=None, value=None):
        pre, after = self.step(op, s.heap, obj, value)
        self.need(s, pre, op + '.pre')
        s.heap = after

    @staticmethod
    def input_atom(expr, sort):
        # Host-language SMT expressions are not an escape hatch for memory reads
        # or hidden assumptions. Values/guards are constants or scalar inputs.
        if not isinstance(expr, z.ExprRef) or expr.sort() != sort or not z.is_const(expr):
            raise Rejected('IR operands must be scalar input atoms or constants')

    def ledger(self, s, label):
        """Arbitrary q checks ALL identities, including an unbounded ambient frame."""
        q = z.FreshInt('ledger_q')
        owns = [b for b in s.env.values() if b.kind == 'own']
        loans = [b for b in s.env.values() if b.kind == 'loan']
        active = owns + loans
        clauses = [wf(s.heap, q),
                   (s.heap.owner[q] == LOCAL) == z.Or(*[q == b.obj for b in owns]),
                   s.heap.lent[q] == z.Or(s.ambient_loans[q],
                                          *[q == b.obj for b in loans],
                                          *[q == i for i in s.returned_loans])]
        clauses += [s.heap.owner[b.obj] == LOCAL for b in owns]
        clauses += [z.And(s.heap.lent[b.obj], z.Not(s.ambient_loans[b.obj])) for b in loans]
        clauses += [z.And(s.heap.owner[i] == OUT, s.heap.init[i]) for i in s.returned_owns]
        clauses += [z.And(s.heap.lent[i], z.Not(s.ambient_loans[i])) for i in s.returned_loans]
        outputs = s.returned_owns + s.returned_loans
        clauses += [a != b for j, a in enumerate(outputs) for b in outputs[j + 1:]]
        clauses += [a.obj != b.obj for j, a in enumerate(active) for b in active[j + 1:]]
        if len({b.cap for b in active}) != len(active):
            raise Rejected(f'{self.name}: duplicate capability identity')
        for b in s.env.values():
            if b.kind == 'read':
                roots = [t for t in active if t.cap == b.cap]
                if len(roots) != 1:
                    raise Rejected(f'{self.name}: orphaned read borrow')
                clauses.append(b.obj == roots[0].obj)
        self.need(s, z.And(*clauses), label + '.ledger')

    def instruction(self, s, ins):
        op, *args = ins
        if op == 'init':
            name, value = args
            self.input_atom(value, INT)
            b = self.binding(s, name, 'own')
            self.unborrowed(s, b)
            self.apply(s, 'init', b.obj, value)
        elif op == 'move':
            src, dst = args
            b = self.binding(s, src)
            if b.kind not in ('own', 'loan'):
                raise Rejected('move requires a linear token')
            self.unborrowed(s, b)
            self.fresh_name(s, dst)
            s.env[dst] = s.env.pop(src)
        elif op == 'borrow':
            src, dst = args
            b = self.binding(s, src)
            if b.kind not in ('own', 'loan'):
                raise Rejected('borrow requires an owner or loan token')
            self.fresh_name(s, dst)
            s.env[dst] = Binding('read', b.obj, b.cap)
        elif op == 'read':
            b = self.binding(s, args[0], 'read')
            roots = [r for r in s.env.values() if r.cap == b.cap and r.kind in ('own', 'loan')]
            if len(roots) != 1:
                raise Rejected('read has no unique capability root')
            self.apply(s, 'read_' + roots[0].kind, b.obj)
        elif op == 'end':
            self.binding(s, args[0], 'read')
            del s.env[args[0]]
        elif op in ('free', 'release', 'publish'):
            b = self.binding(s, args[0], 'loan' if op == 'release' else 'own')
            self.unborrowed(s, b)
            if op == 'publish':
                self.fresh_name(s, args[1])
                s.ids[args[1]] = b.obj
            self.apply(s, op, b.obj)
            del s.env[args[0]]
        elif op in ('lend', 'reclaim'):
            src, dst = args
            if src not in s.ids:
                raise Rejected('source operation requires a known source identity')
            self.apply(s, op, s.ids[src])
            self.add_token(s, dst, 'loan' if op == 'lend' else 'own', s.ids[src])
        elif op == 'write_source':
            src, value = args
            self.input_atom(value, INT)
            if src not in s.ids:
                raise Rejected('write requires a known source identity')
            self.apply(s, op, s.ids[src], value)
        elif op == 'close_source':
            self.apply(s, op)
        else:
            raise Rejected('unsupported instruction: ' + str(op))
        self.ledger(s, op)

    def walk(self, s, code):
        if not self.proofs.feasible(s.facts, self.name):
            return  # only solver-proved unreachable paths are skipped
        if not code:
            raise Rejected(self.name + ': missing explicit return/throw')
        head, *tail = code
        if isinstance(head, (Branch, Allocate)):
            condition = head.condition if isinstance(head, Branch) else z.FreshBool('alloc_ok')
            self.input_atom(condition, BOOL)
            for positive in (True, False):
                child = s.copy()
                child.facts.append(condition if positive else z.Not(condition))
                if not self.proofs.feasible(child.facts, self.name):
                    continue
                if isinstance(head, Allocate):
                    if positive:
                        obj = child.heap.epoch + 1
                        self.apply(child, 'alloc')
                        self.add_token(child, head.name, 'own', obj)
                        self.ledger(child, 'alloc')
                    arm = head.success if positive else head.failure
                else:
                    arm = head.yes if positive else head.no
                self.walk(child, (*arm, *tail))
        elif isinstance(head, Exit):
            if head.outcome not in ('return', 'throw') or (head.outcome == 'throw' and head.outputs):
                raise Rejected('invalid exit')
            for name in head.outputs:
                b = self.binding(s, name)
                self.unborrowed(s, b)
                if b.kind == 'own':
                    self.apply(s, 'export', b.obj)
                    s.returned_owns.append(b.obj)
                elif b.kind == 'loan':
                    s.returned_loans.append(b.obj)
                else:
                    raise Rejected('cannot return a derived read borrow')
                del s.env[name]
            if s.env:
                raise Rejected(self.name + ': unconsumed resources/borrows at ' + head.outcome)
            self.ledger(s, head.outcome)
            self.ends.append(Endpoint(head.outcome, s.copy()))
        else:
            self.instruction(s, head)
            self.walk(s, tail)

    def verify(self, entry, code):
        if not self.proofs.feasible(entry.facts, self.name + '.entry'):
            raise Rejected(self.name + ': inconsistent entry contract')
        self.ledger(entry, 'entry')
        self.walk(entry, code)
        if not self.ends:
            raise Rejected(self.name + ': no reachable exit')
        return self.ends
