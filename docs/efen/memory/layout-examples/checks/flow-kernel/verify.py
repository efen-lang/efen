#!/usr/bin/env python3
"""Check transition lemmas and complete finite CFGs, including failure cleanup."""

import argparse
from dataclasses import replace
import json
from pathlib import Path

import z3 as z

from kernel import (Allocate, Binding, Branch, DEAD, Exit, Heap, INT, LOCAL, OUT,
                    Proofs, Rejected, SOURCE, State, Verifier, transition, wf)


RETURN, THROW = Exit('return'), Exit('throw')
PAYLOAD, UPDATED = z.Ints('payload updated')
VALID = z.Bool('valid')


def empty():
    return State(Heap.empty())


def incoming(kind, tag):
    """Symbolic contract with arbitrarily many disjoint ambient objects/loans."""
    i, q, epoch = z.Ints(tag + '_item ' + tag + '_q ' + tag + '_epoch')
    occupied = z.Array(tag + '_occupied', INT, z.BoolSort())
    outside = z.Array(tag + '_outside', INT, z.BoolSort())
    ready = z.Array(tag + '_initialized', INT, z.BoolSort())
    loans = z.Array(tag + '_loans', INT, z.BoolSort())
    # Construct the complete WF family instead of asking for a model of an
    # unrestricted quantified array axiom. epoch is unbounded, not an unroll cap.
    owner = z.Store(z.Lambda(q, z.If(z.And(q > 0, q <= epoch, occupied[q]),
                                     z.If(outside[q], OUT, SOURCE), DEAD)),
                    i, LOCAL if kind == 'own' else SOURCE)
    live = z.Lambda(q, owner[q] != DEAD)
    init = z.Store(z.Lambda(q, z.And(live[q], z.Or(owner[q] == SOURCE, ready[q]))), i, True)
    lent = z.Store(z.Lambda(q, z.And(owner[q] == SOURCE, loans[q])), i, kind == 'loan')
    h = Heap(epoch, z.BoolVal(True), live, init, owner, lent, z.Array(tag + '_value', INT, INT))
    facts = [i > 0, i <= epoch]
    if kind == 'own':
        return State(h, facts, {'x': Binding('own', i, 1)},
                     ambient_loans=h.lent, next_cap=1)
    if kind == 'loan':
        return State(h, facts, {'loan': Binding('loan', i, 1)}, {'item': i},
                     z.Store(h.lent, i, False), next_cap=1)
    if kind == 'source':
        return State(h, facts, ids={'item': i}, ambient_loans=h.lent)
    raise ValueError(kind)


def check_lemmas(p):
    h = Heap.symbolic('lemma')
    i, q = z.Ints('lemma_i lemma_q')
    p.prove('base.empty', [], wf(Heap.empty(), q))
    ops = ('alloc', 'init', 'publish', 'reclaim', 'lend', 'release', 'free',
           'export', 'write_source', 'read_own', 'read_loan', 'close_source')
    for op in ops:
        target = h.epoch + 1 if op == 'alloc' else i
        pre, after = transition(op, h, target, PAYLOAD)
        assumptions = [wf(h, q), wf(h, target), pre]
        if not p.feasible(assumptions, op + '.nonvacuous'):
            raise Rejected('unreachable primitive: ' + op)
        p.prove(op + '.preserves_WF', assumptions, wf(after, q))
        fields = ('live', 'init', 'owner', 'lent', 'value')
        p.prove(op + '.frame', [*assumptions, q != target],
                z.And(*[getattr(after, f)[q] == getattr(h, f)[q] for f in fields]))
        # The fixed repayment continuation depends only on these source facts.
        exempt = q != target if op == 'release' else z.BoolVal(True)
        p.prove(op + '.preserves_ReturnReady', [*assumptions, h.lent[q], exempt],
                z.And(after.lent[q], after.source, after.live[q], after.init[q],
                      after.owner[q] == SOURCE))
    p.prove('alloc.fresh_identity', [wf(h, h.epoch + 1)], z.Not(h.live[h.epoch + 1]))
    pre, after = transition('free', h, i)
    second_pre, _ = transition('free', after, i)
    p.prove('free.cannot_free_twice', [wf(h, i), pre], z.Not(second_pre))
    pre, after = transition('release', h, i)
    second_pre, _ = transition('release', after, i)
    p.prove('release.consumes_obligation', [wf(h, i), pre], z.Not(second_pre))
    for op in ('read_own', 'read_loan'):
        pre, _ = transition(op, h, i)
        p.prove(op + '.initialized_live', [wf(h, i), pre], z.And(h.live[i], h.init[i]))


def positive_programs():
    # Complete createPair: no throw path abandons an already allocated cell.
    pair = (Allocate('a', (
        ('init', 'a', PAYLOAD),
        Allocate('b', (
            ('init', 'b', UPDATED),
            Branch(VALID, (Exit('return', ('a', 'b')),),
                   (('free', 'b'), ('free', 'a'), THROW)),
        ), (('free', 'a'), THROW)),
    ), (THROW,)),)

    # An exception while a derived read exists explicitly ends that read first.
    with_loan = (
        ('lend', 'item', 'loan'), ('borrow', 'loan', 'r'), ('read', 'r'),
        Branch(VALID,
               (('end', 'r'), ('release', 'loan'), RETURN),
               (('end', 'r'), ('release', 'loan'), THROW)),
    )
    loan_with_allocation = (
        ('lend', 'item', 'loan'),
        Allocate('temp',
                 (('init', 'temp', PAYLOAD), ('free', 'temp'), ('release', 'loan'), RETURN),
                 (('release', 'loan'), THROW)),
    )
    # close_source is legal while the independent cell's ordinary owner lives.
    detach_and_close = (Allocate('x', (
        ('init', 'x', PAYLOAD), ('publish', 'x', 'item'),
        ('reclaim', 'item', 'result'), ('close_source',), Exit('return', ('result',)),
    ), (('close_source',), THROW)),)
    yield 'create_pair', empty(), pair
    yield 'with_loan', incoming('source', 'use'), with_loan
    yield 'loan_allocation_cleanup', incoming('source', 'temp'), loan_with_allocation
    yield 'acquire', incoming('source', 'acquire'), (('lend', 'item', 'loan'), Exit('return', ('loan',)))
    yield 'release', incoming('loan', 'repay'), (('release', 'loan'), RETURN)
    yield 'detach', incoming('source', 'detach'), (('reclaim', 'item', 'x'), Exit('return', ('x',)))
    yield 'move_owner', incoming('own', 'move'), (
        ('move', 'x', 'y'), ('borrow', 'y', 'r'), ('read', 'r'), ('end', 'r'), Exit('return', ('y',)))
    yield 'update_after_return', incoming('source', 'update'), (
        ('lend', 'item', 'loan'), ('release', 'loan'), ('write_source', 'item', UPDATED), RETURN)
    yield 'detach_and_close', empty(), detach_and_close


def check_postconditions(p, name, initial, ends):
    for endpoint in ends:
        s = endpoint.state
        q = z.FreshInt('function_frame_q')
        footprint = [b.obj for b in initial.env.values()] + list(initial.ids.values())
        p.prove(name + '.function_frame',
                [*s.facts, q <= initial.heap.epoch, *[q != i for i in footprint]],
                z.And(*[getattr(s.heap, f)[q] == getattr(initial.heap, f)[q]
                        for f in ('live', 'init', 'owner', 'lent', 'value')]))
        if name == 'create_pair':
            expected = 2 if endpoint.outcome == 'return' else 0
            if len(s.returned_owns) != expected:
                raise Rejected('wrong create_pair result arity')
            if expected:
                a, b = s.returned_owns
                p.prove(name + '.values', s.facts, z.And(s.heap.value[a] == PAYLOAD,
                                                       s.heap.value[b] == UPDATED))
            else:
                q = z.FreshInt('pair_cleanup_q')
                p.prove(name + '.exception_no_allocations', s.facts, z.Not(s.heap.live[q]))
        if name in ('with_loan', 'loan_allocation_cleanup', 'release', 'update_after_return'):
            i = initial.ids['item']
            p.prove(name + '.repaid', s.facts,
                    z.And(s.heap.owner[i] == SOURCE, z.Not(s.heap.lent[i])))
        if name == 'update_after_return':
            p.prove(name + '.updated_value', s.facts, s.heap.value[initial.ids['item']] == UPDATED)
        if name in ('with_loan', 'loan_allocation_cleanup', 'release', 'acquire', 'detach'):
            i = initial.ids['item']
            p.prove(name + '.payload_preserved', s.facts, s.heap.value[i] == initial.heap.value[i])
        if name == 'detach_and_close':
            p.prove(name + '.source_closed', s.facts, z.Not(s.heap.source))
            if endpoint.outcome == 'return':
                i, = s.returned_owns
                p.prove(name + '.owner_outlives_source', s.facts,
                        z.And(s.heap.live[i], s.heap.init[i], s.heap.owner[i] == OUT))


def expect_rejected(name, action, fragment):
    try:
        action()
    except Rejected as error:
        if name != 'unknown_is_rejection' and ('unknown' in str(error) or 'timeout' in str(error)):
            raise AssertionError(f'{name}: rejection without a confirmed counterexample: {error}') from error
        if fragment not in str(error):
            raise AssertionError(f'{name}: wrong rejection: {error}') from error
        return {'name': name, 'diagnostic': str(error).splitlines()[0]}
    raise AssertionError(name + ': incorrectly accepted')


def negative_programs():
    yield 'read_uninitialized', empty(), (Allocate('x', (
        ('borrow', 'x', 'r'), ('read', 'r'), ('end', 'r'), ('free', 'x'), RETURN), (THROW,)),), 'read_own.pre'
    yield 'double_free', incoming('own', 'bad_free'), (('free', 'x'), ('free', 'x'), RETURN), 'unavailable own'
    yield 'free_borrowed', incoming('own', 'borrowed'), (('borrow', 'x', 'r'), ('free', 'x'), RETURN), 'active read borrow'
    yield 'lost_owner_on_error', empty(), (Allocate('x', (THROW,), (THROW,)),), 'unconsumed'
    yield 'lost_loan_on_return', incoming('source', 'lost'), (('lend', 'item', 'loan'), RETURN), 'unconsumed'
    yield 'second_loan', incoming('source', 'twice'), (
        ('lend', 'item', 'a'), ('lend', 'item', 'b'), RETURN), 'lend.pre'
    yield 'reclaim_lent', incoming('source', 'reclaim_bad'), (
        ('lend', 'item', 'loan'), ('reclaim', 'item', 'x'), RETURN), 'reclaim.pre'
    yield 'destroy_lent_source', incoming('source', 'destroy'), (
        ('lend', 'item', 'loan'), ('close_source',), RETURN), 'close_source.pre'
    yield 'return_before_end_read', incoming('loan', 'early'), (
        ('borrow', 'loan', 'r'), ('release', 'loan'), RETURN), 'active read borrow'
    yield 'stale_read', incoming('loan', 'stale'), (
        ('borrow', 'loan', 'r'), ('end', 'r'), ('release', 'loan'), ('read', 'r'), RETURN), 'unavailable read'
    yield 'moved_owner', incoming('own', 'moved'), (
        ('move', 'x', 'y'), ('free', 'x'), RETURN), 'unavailable own'
    yield 'duplicate_output', incoming('own', 'dup_out'), (Exit('return', ('x', 'x')),), 'unavailable binding'
    yield 'one_bad_branch', incoming('source', 'branch'), (
        ('lend', 'item', 'loan'), Branch(VALID, (('release', 'loan'), RETURN), (THROW,))), 'unconsumed'
    duplicate = incoming('own', 'duplicate_input')
    duplicate.env['y'] = replace(duplicate.env['x'], cap=2)
    yield 'duplicate_input_owner', duplicate, (RETURN,), 'entry.ledger'
    yield 'false_entry_contract', State(Heap.empty(), [z.BoolVal(False)]), (RETURN,), 'inconsistent entry'
    yield 'unsupported_loop', empty(), (('while',), RETURN), 'unsupported instruction'
    yield 'hidden_memory_read', empty(), (Allocate('x', (
        ('init', 'x', z.Array('hidden', INT, INT)[0]), ('free', 'x'), RETURN), (THROW,)),), 'scalar input'
    yield 'write_while_lent', incoming('source', 'write_lent'), (
        ('lend', 'item', 'loan'), ('write_source', 'item', UPDATED), RETURN), 'write_source.pre'
    yield 'export_uninitialized', empty(), (Allocate('x',
        (Exit('return', ('x',)),), (THROW,)),), 'export.pre'
    yield 'old_identity_after_new_allocation', empty(), (Allocate('x', (
        ('init', 'x', PAYLOAD), ('publish', 'x', 'old'),
        ('reclaim', 'old', 'x'), ('free', 'x'),
        Allocate('y', (('init', 'y', PAYLOAD), ('publish', 'y', 'new'),
                       ('reclaim', 'old', 'z'), RETURN), (THROW,)),
    ), (THROW,)),), 'reclaim.pre'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emit-vcs', type=Path, help='write SMT-LIB obligations and report.json')
    args = parser.parse_args()
    p = Proofs(args.emit_vcs)
    check_lemmas(p)
    lemma_count = p.count
    positives = []
    for name, entry, body in positive_programs():
        before = entry.copy()
        ends = Verifier(p, name).verify(entry, body)
        check_postconditions(p, name, before, ends)
        positives.append({'name': name, 'paths': len(ends)})
    positive_count = p.count - lemma_count
    negatives = []
    for name, entry, body, fragment in negative_programs():
        negatives.append(expect_rejected(name, lambda: Verifier(p, name).verify(entry, body), fragment))

    # Deliberately corrupt transitions: heap WF alone does not prove linear
    # accounting or the validity of exported results. The ledger must catch both.
    def wrong_release(op, h, i=None, value=None):
        pre, after = transition(op, h, i, value)
        return pre, replace(after, lent=h.lent) if op == 'release' else after

    def wrong_export(op, h, i=None, value=None):
        if op == 'export':
            pre, _ = transition(op, h, i, value)
            _, after = transition('free', h, i)
            return pre, after
        return transition(op, h, i, value)

    negatives.append(expect_rejected('release_did_not_consume', lambda: Verifier(
        p, 'release_did_not_consume', wrong_release).verify(
            incoming('loan', 'mutant_release'), (('release', 'loan'), RETURN)), 'release.ledger'))
    negatives.append(expect_rejected('export_freed_result', lambda: Verifier(
        p, 'export_freed_result', wrong_export).verify(
            incoming('own', 'mutant_export'), (Exit('return', ('x',)),)), 'return.ledger'))
    negatives.append(expect_rejected('unknown_is_rejection', lambda: Proofs.require_unsat(
        z.unknown, 'solver timeout'), 'unknown'))
    report = {'z3': z.get_version_string(), 'transition_lemmas': lemma_count,
              'positive_program_vcs': positive_count, 'programs': positives,
              'negative_checks': negatives, 'obligations': p.records}
    if args.emit_vcs:
        (args.emit_vcs / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Z3:', report['z3'])
    print('Transition lemmas:', lemma_count)
    print('Accepted functions:', len(positives), 'terminal paths:', sum(x['paths'] for x in positives),
          'VCs:', positive_count)
    for item in positives:
        print('  ', item['name'], ':', item['paths'], 'paths')
    print('Rejected negative cases:', len(negatives))
    print('Symbolic checks passed. This is a restricted IR prototype, not FLOW soundness or compiler verification.')


if __name__ == '__main__':
    main()
