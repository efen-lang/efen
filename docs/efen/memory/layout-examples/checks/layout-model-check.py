#!/usr/bin/env python3
"""Finite executable models for layout-algorithm.md, NOT an efen/FLOW test.

Run with Python 3 (without -O). No dependencies. Passing bounded enumeration
does not prove the unbounded algorithms or the proposed inference rules.
"""

from collections import deque
from functools import lru_cache
from itertools import permutations, product


def graph_checks():
    deleted = copied = 0
    for n in range(1, 5):
        for bits in range(1 << (n * n)):
            original = [[v for v in range(n) if bits & (1 << (u * n + v))]
                        for u in range(n)]
            reverse = [[u for u in range(n) if v in original[u]] for v in range(n)]
            for victim in range(n):
                out = [row[:] for row in original]
                inc = [row[:] for row in reverse]
                for w in inc[victim]:
                    out[w] = [v for v in out[w] if v != victim]
                for w in out[victim]:
                    inc[w] = [v for v in inc[w] if v != victim]
                # The two passes suffice for deleting the node, but strict own
                # also requires clearing a surviving pointer from the node to itself.
                inc[victim] = [v for v in inc[victim] if v != victim]
                assert all(victim not in out[u] + inc[u] for u in range(n))
                for u in range(n):
                    if u == victim:
                        continue
                    assert out[u] == [v for v in original[u] if v != victim]
                    assert inc[u] == [v for v in reverse[u] if v != victim]
                    for v in range(n):
                        if v != victim:
                            assert (v in out[u]) == (u in inc[v])
                deleted += 1

                # Copy reachable objects; all old forwarding records remain live
                # until the queue is empty and roots/new pointers are rewritten.
                forwarding, new_heap, queue = {}, {}, deque()

                def evacuate(old):
                    if old not in forwarding:
                        fresh = n + len(forwarding)
                        forwarding[old] = fresh
                        new_heap[fresh] = None
                        queue.append(old)
                    return forwarding[old]

                root = evacuate(victim)
                while queue:
                    old = queue.popleft()
                    new_heap[forwarding[old]] = [evacuate(v) for v in original[old]]
                reachable, todo = set(), [victim]
                while todo:
                    u = todo.pop()
                    if u not in reachable:
                        reachable.add(u)
                        todo.extend(original[u])
                assert set(forwarding) == reachable
                assert root == forwarding[victim]
                assert len(set(forwarding.values())) == len(forwarding)
                for old, fresh in forwarding.items():
                    assert new_heap[fresh] == [forwarding[v] for v in original[old]]
                    assert all(v >= n for v in new_heap[fresh])
                copied += 1
    return deleted, copied


def list_checks():
    cases = 0
    for n in range(9):
        original = list(range(n))
        for at in range(n + 1):
            nxt = {i: i + 1 if i + 1 < n else None for i in original}
            prev = {i: i - 1 if i else None for i in original}
            head = 0 if n else None
            fresh = n
            left = at - 1 if at else None
            right = at if at < n else None
            prev[fresh], nxt[fresh] = left, right
            if right is not None:
                prev[right] = fresh
            if left is None:
                head = fresh
            else:
                nxt[left] = fresh
            visited, p, u = [], None, head
            while u is not None:
                assert u not in visited and prev[u] == p
                visited.append(u)
                p, u = u, nxt[u]
            assert visited == original[:at] + [fresh] + original[at:]
            cases += 1
        for victim in original:
            nxt = {i: i + 1 if i + 1 < n else None for i in original}
            prev = {i: i - 1 if i else None for i in original}
            left, right = prev[victim], nxt[victim]
            head = 0
            if left is None:
                head = right
            else:
                nxt[left] = right
            if right is not None:
                prev[right] = left
            del nxt[victim], prev[victim]
            assert victim not in nxt.values() and victim not in prev.values()
            visited, p, u = [], None, head
            while u is not None:
                assert u not in visited and prev[u] == p
                visited.append(u)
                p, u = u, nxt[u]
            assert visited == [i for i in original if i != victim]
            cases += 1
    return cases


@lru_cache(None)
def tree_shapes(n):
    if n == 0:
        return (None,)
    return tuple((left, right) for k in range(n)
                 for left in tree_shapes(k) for right in tree_shapes(n - 1 - k))


def rotation_checks():
    cases = 0
    for n in range(1, 8):
        for shape in tree_shapes(n):
            nodes = {}

            def build(s, parent=None):
                if s is None:
                    return None
                ident = len(nodes)
                nodes[ident] = [None, None, parent]
                nodes[ident][0] = build(s[0], ident)
                nodes[ident][1] = build(s[1], ident)
                return ident

            root = build(shape)

            def inorder(heap, r):
                if r is None:
                    return []
                return inorder(heap, heap[r][0]) + [r] + inorder(heap, heap[r][1])

            expected = inorder(nodes, root)
            for x in nodes:
                if nodes[x][1] is None:
                    continue
                h = {u: row[:] for u, row in nodes.items()}
                p = h[x][2]
                # Caller detaches x; callee owns the root x during rotation.
                if p is not None:
                    side = 0 if h[p][0] == x else 1
                    h[p][side] = None
                y = h[x][1]
                h[x][1] = None
                beta = h[y][0]
                h[y][0] = None
                h[x][1] = beta
                if beta is not None:
                    h[beta][2] = x
                h[y][2] = p
                h[x][2] = y
                h[y][0] = x
                if p is None:
                    new_root = y
                else:
                    h[p][side] = y
                    new_root = root
                assert inorder(h, new_root) == expected
                incoming = {u: 0 for u in h}
                for u, (l, r, _) in h.items():
                    for child in (l, r):
                        if child is not None:
                            incoming[child] += 1
                            assert h[child][2] == u
                assert h[new_root][2] is None
                assert all(v == (0 if u == new_root else 1) for u, v in incoming.items())
                cases += 1
    return cases


def array_checks():
    cases = 0
    hole = object()
    for n in range(9):
        original = list(range(n))
        for at in range(n + 1):
            a = original + [hole]
            cursor = n
            while cursor > at:
                assert a[cursor] is hole and a[cursor - 1] is not hole
                a[cursor], a[cursor - 1] = a[cursor - 1], hole
                cursor -= 1
            assert a[at] is hole
            a[at] = n
            assert a == original[:at] + [n] + original[at:]
            cases += 1
        for at in range(n):
            a = original[:]
            removed, a[at] = a[at], hole
            cursor = at
            while cursor + 1 < n:
                assert a[cursor] is hole and a[cursor + 1] is not hole
                a[cursor], a[cursor + 1] = a[cursor + 1], hole
                cursor += 1
            assert a[-1] is hole and removed == at
            assert a[:-1] == original[:at] + original[at + 1:]
            cases += 1
    return cases


def pool_and_ring_checks():
    pool = ring = 0
    for capacity in range(1, 7):
        for frontier in range(capacity + 1):
            for flags in product((False, True), repeat=frontier):
                taken = {k for k, flag in enumerate(flags) if flag}
                free = set(range(frontier)) - taken
                if free or frontier < capacity:
                    k = min(free) if free else frontier
                    assert 0 <= k < capacity and k not in taken
                    new_frontier = frontier if free else frontier + 1
                    new_taken = taken | {k}
                    new_free = free - {k}
                    assert new_taken.isdisjoint(new_free)
                    assert new_taken | new_free == set(range(new_frontier))
                    pool += 1
                for k in taken:
                    returned = taken - {k}
                    available = free | {k}
                    assert returned.isdisjoint(available)
                    assert returned | available == set(range(frontier))
                    pool += 1
    for capacity in range(1, 17):
        for head in range(capacity):
            for count in range(capacity + 1):
                occupied = {(head + i) % capacity for i in range(count)}
                assert len(occupied) == count
                if count < capacity:
                    pos = (head + count) % capacity
                    assert pos not in occupied
                if count:
                    assert head in occupied
                    after = {((head + 1) % capacity + i) % capacity for i in range(count - 1)}
                    assert after == occupied - {head}
                ring += 1
    return pool, ring


def dsu_checks():
    finds = unions = 0
    for n in range(1, 5):
        for rank in product(range(n), repeat=n):
            for parent in product(range(n), repeat=n):
                def valid(p, ranks):
                    return all(p[u] == u or ranks[p[u]] > ranks[u] for u in range(n))

                if not valid(parent, rank):
                    continue
                roots = {u for u in range(n) if parent[u] == u}

                def find(p, x):
                    root = x
                    steps = 0
                    while p[root] != root:
                        root = p[root]
                        steps += 1
                        assert steps < n
                    y = x
                    while p[y] != root:
                        nxt = p[y]
                        p[y] = root
                        y = nxt
                    return root

                for x in range(n):
                    p = list(parent)
                    root = find(p, x)
                    assert valid(p, rank) and p[root] == root
                    assert all(p[u] == u for u in roots)
                    finds += 1
                for a, b in product(range(n), repeat=2):
                    p, r = list(parent), list(rank)
                    ra, rb = find(p, a), find(p, b)
                    if ra != rb:
                        if r[ra] < r[rb]:
                            p[ra] = rb
                        elif r[ra] > r[rb]:
                            p[rb] = ra
                        else:
                            new_rank = r[ra] + 1  # checked before changing topology
                            p[rb], r[ra] = ra, new_rank
                    assert valid(p, r)
                    unions += 1
    return finds, unions


def rehash_checks():
    cases = 0
    for n in range(6):
        for keys in product(range(4), repeat=n):
            old = [[u for u in range(n) if keys[u] % 2 == b] for b in range(2)]
            new = [[] for _ in range(4)]
            for b in range(2):
                while old[b]:
                    entry = old[b].pop(0)
                    dest = keys[entry] % 4
                    new[dest].insert(0, entry)
                    owners = [u for row in old + new for u in row]
                    assert sorted(owners) == list(range(n))
                    assert all(keys[u] % 2 == k for k, row in enumerate(old) for u in row)
                    assert all(keys[u] % 4 == k for k, row in enumerate(new) for u in row)
            assert all(not row for row in old)
            assert sum(map(len, new)) == n
            cases += 1
    return cases


def negative_witnesses():
    # An untouched node's invariant can depend on the written node.
    key, nxt = [0, 0], [1, None]
    invariant = lambda u: nxt[u] is None or key[u] == key[nxt[u]]
    assert all(invariant(u) for u in range(2))
    key[1] = 1
    assert invariant(1) and not invariant(0)

    # Unique incoming owner per node does not exclude an ownership cycle.
    owners = {0: 1, 1: 0}
    assert len(set(owners.values())) == 2 and owners[owners[0]] == 0

    # The pool's published laws allow an already-issued frontier slot.
    capacity, frontier, taken, free, used = 1, 0, {0}, set(), 1
    assert used == len(taken) and frontier <= capacity
    assert all(0 <= k < frontier and k not in taken for k in free)
    assert frontier < capacity and frontier in taken

    # Global length and each block's bound do not establish a dense prefix.
    block_size, lengths, length = 2, [0, 1], 1
    assert sum(lengths) == length and all(0 <= n <= block_size for n in lengths)
    index = 0
    assert index < length and index % block_size >= lengths[index // block_size]

    # makePair must account for the previous peers.
    peer = [2, None, 0]
    pair_law = lambda u: peer[u] is None or peer[peer[u]] == u
    assert all(pair_law(u) for u in range(3))
    peer[0], peer[1] = 1, 0
    assert pair_law(0) and pair_law(1) and not pair_law(2)

    # Overflow in the second step of union leaves a false rank invariant.
    rank, parent, maximum = [255, 255], [0, 1], 255
    parent[1] = 0
    assert rank[0] == maximum and not rank[parent[1]] > rank[1]

    # Freeing an old forwarding record before processing the cycle is unsafe.
    old_live, old_edges = {0, 1}, {0: [1], 1: [0]}
    old_live.remove(0)
    assert old_edges[1][0] not in old_live

    # A cursor's next field is stable but its invariant's data need not be.
    values, links = [0, 0], [1, None]
    original_links = links[:]
    values[0] = 1
    assert links == original_links and values[0] != values[1]

    # Local DCEL holder enumeration alone does not prove naive pair removal.
    twin = (1, 0, 3, 2)
    witness = None
    for nexts in permutations(range(4)):
        for origin in product(range(2), repeat=4):
            if not all(origin[twin[h]] == origin[nexts[h]] for h in range(4)):
                continue
            after = {}
            for h in (2, 3):
                cur = nexts[h]
                while cur in (0, 1):
                    cur = nexts[cur]
                after[h] = cur
            if any(origin[twin[h]] != origin[after[h]] for h in (2, 3)):
                witness = (nexts, origin, after)
                break
        if witness:
            break
    assert witness is not None
    print("DCEL naive-splice counterexample:", witness)

    # The old reverse-graph deletion leaves a self reference before strict own.
    out, inc = [[0]], [[0]]
    for w in inc[0]:
        out[w] = [v for v in out[w] if v != 0]
    for w in out[0]:
        inc[w] = [v for v in inc[w] if v != 0]
    assert out[0] == [] and inc[0] == [0]

    # Return code can become inapplicable without invalidating its target.
    live, head, issued = {0, 1}, 0, 0
    assert head == issued and issued in live
    head = 1
    assert issued in live and head != issued

    # A stable borrowed target does not keep a raw capture of source Self valid.
    captured_source_address, live_source_address, target_address = 0, 0, 2
    live_source_address = 1
    assert target_address == 2 and captured_source_address != live_source_address

    # An unsigned count-1 in the empty-list invariant is not defined.
    count = 0
    assert count - 1 < 0
    assert all(i == 0 or i - 1 >= 0 for i in range(count))

    # Forward anchor laws alone permit an unanchored/set-owned extra holder X.
    nexts, prevs = {0: 1, 1: 2, 2: None, 3: None}, {0: None, 1: 0, 2: 1, 3: 1}
    assert all(nexts[u] is None or prevs[nexts[u]] == u for u in nexts)
    nexts[0], prevs[2] = 2, 0
    del nexts[1], prevs[1]
    assert prevs[3] == 1  # remove needs AllAnchored or a scan of this extra holder

    # Preserving source A alone is insufficient if repayment also needs B.flag.
    source_a, source_b = {"issued": True}, {"flag": 0}
    can_repay = lambda: source_a["issued"] and source_b["flag"] == 0
    assert can_repay()
    source_b["flag"] = 1
    assert source_a["issued"] and not can_repay()
    # A local B invariant can survive while a foreign A invariant is broken.
    a, b = {"back": 1}, {"target": 0}
    a_law = lambda: a["back"] is None or b["target"] == 0
    b_law = lambda: b["target"] is None or a["back"] == 1
    assert a_law() and b_law()
    b["target"] = None
    assert b_law() and not a_law()
    live_holders = {1}
    live_holders.remove(1)
    assert a["back"] not in live_holders
    # Detaching t in this function does not keep it disjoint from a later r.
    q, t, r = 0, 1, 2
    child = {q: t, t: None, r: None}
    detached, child[q] = child[q], None
    child[r] = detached
    assert child[t] is None and t != r and child[r] == t
    child[t] = r  # the stale "detached here" criterion would accept a cycle
    assert child[child[t]] == t
    return 17


def main():
    if not __debug__:
        raise SystemExit("Run without -O: assertions are the checks.")
    print("graph deletion, delayed-reclamation copying:", graph_checks())
    print("list insertion/deletion:", list_checks())
    print("binary-tree rotation:", rotation_checks())
    print("array shifts with initialized masks:", array_checks())
    print("pool and ring transitions:", pool_and_ring_checks())
    print("union-find find/union over bounded ranks:", dsu_checks())
    print("two-to-four-bucket rehash:", rehash_checks())
    print("negative witnesses:", negative_witnesses())
    print("Finite models passed; this is not a compiler test or an unbounded proof.")


if __name__ == "__main__":
    main()
