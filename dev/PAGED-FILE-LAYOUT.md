# Paged file layout: design draft

Status: discussion draft. None of the candidate syntax in this document is
normative until Edmond approves its numbered syntax case.

## Purpose

This document tests one idea through a complete example: a `layout` describes a
logical memory space and the algorithms that realize it through several physical
memory areas.

The example treats an entire file as the logical population `Records`, while
only two file pages may be resident in the RAM population `Frames`. Ordinary
access through `Records.Pointer` may transparently load, pin, modify and release
a frame. A logical write succeeds when the RAM copy becomes authoritative.
Durability is requested separately through `flush()`.

The example must account for:

1. opening and validating an existing file;
2. constructing logical pointers only after validation;
3. cache hits and misses;
4. reading through a two-frame cache;
5. modifying a record and making the frame authoritative;
6. evicting clean and dirty frames;
7. pinning a frame for the lifetime of a borrow;
8. explicit durability through `flush()`;
9. I/O failure at every fallible boundary;
10. closing the layout under an explicit durability policy.

## Fixed semantic premises

These premises come from the discussion and are not syntax proposals.

- A layout is a logical memory space, not one physical allocation or one
  physical resource.
- One layout may use file storage, RAM, DMA buffers, device memory and other
  physical areas at the same time.
- `Records.Pointer` is a logical pointer. It does not promise a machine address
  or permanent residency in RAM.
- A logical place may have several physical replicas. At most one replica is the
  authoritative writable version. Other replicas are current read copies,
  stale copies or unpublished copies in transit.
- A transparent access implementation may consist of several functions.
- Once that implementation is explicitly declared transparent, source code may
  use ordinary `pointer.field` access. No additional marker is required at the
  access site.
- The complete effects, exceptions and possible suspension of transparent
  access remain part of the containing function's contract.
- A logical write completes when a RAM replica becomes authoritative. It need
  not be durable yet. `flush()` requests durability separately.
- Predicates on properties express logical conditions. The design does not
  require built-in names for lists, trees, caches or replacement policies.

## Logical model

For a fixed-size record type `R`, the file contains a header followed by pages.
Each page contains `recordsPerPage` records.

```text
Records.Pointer
    = origin of this PagedFile instance
    + logical record identity

record identity
    -> page number and index within page
    -> resident frame, if one exists
    -> bytes within that frame
```

`Records.Pointer` survives cache eviction and remapping of the file. A physical
borrow into a frame keeps that frame pinned until the borrow ends.

The two-frame vertical slice permits at most one resident RAM frame for a given
file page. The file and that frame are still two physical replicas. More general
replication is a later counterexample, not an assumption hidden in this example.

The logical value of page `p` is defined as follows:

```text
if p has a Dirty or Flushing frame:
    Logical(p) = DirtyFrame(p)
else:
    Logical(p) = FilePage(p)
```

A clean resident frame is a current read replica:

```text
CleanFrame(p) = FilePage(p) = Logical(p)
```

A dirty resident frame is authoritative and the file is stale:

```text
DirtyFrame(p) = Logical(p)
FilePage(p) may contain an older version, or an unknown torn version after a
failed in-place flush
```

## Candidate surface sketch

The following block shows the complete shape. Every uncertain construct is
routed to a numbered syntax case later in this document.

```efen
layout PagedFile<R> {
    // Syntax case S1: physical areas inside one logical layout.
    source file: FileMemory
    source cache: RamMemory

    // Syntax case S2: the logical contents of an existing file.
    set Records: R

    enum ReplicaState {
        Empty
        Clean
        Dirty
    }

    enum IoState {
        Idle
        Loading
        Flushing
    }

    set Frames: Frame from cache

    struct Frame {
        var page: Records.Page? {
            (replica == Empty) == (page == null) &&
            (page == null || Frames.count(where: it.page == page) == 1)
        }

        var bytes: [Byte] {
            bytes.count == pageSize &&
            (replica != Clean || decodesAsCurrentFilePage(bytes, page)) &&
            (replica != Dirty || decodesAsLogicalPage(bytes, page, version))
        }

        var replica: ReplicaState {
            replica == Empty || page != null
        }

        var io: IoState {
            io != Flushing || replica == Dirty
        }

        var version: Version {
            replica == Empty || version == logicalVersion(page)
        }

        // Derived from live access leases; user code cannot modify it.
        var pins: UInt { get { return liveLoans(to: self).count } }
    }

    let pageSize: Size
    let recordsPerPage: Size
    let frameLimit: Size {
        frameLimit == 2
    }

    // Syntax case S3: mapping validated external storage into a population.
    constructor(path: Path) throws IOError | InvalidFile {
        file = FileMemory.open(path, access: exclusiveReadWrite)
        Records.map(file)
    }

    // Syntax case S4: a group of operations hidden behind Records.Pointer
    // reads, writes and borrows.
    transparent access Records {
        fn acquireRead(pointer: read Records.Pointer)
            -> ReadLease<R>
            throws IOError

        fn acquireWrite(pointer: read write Records.Pointer)
            -> WriteLease<R>
            throws IOError

        fn release(lease: AccessLease<R>)
    }

    fn findResident(page: Records.Page) -> read Frames.Pointer?

    fn acquireFrame(page: Records.Page)
        -> read write Frames.Pointer
        throws IOError

    fn load(page: Records.Page, into: read write Frames.Pointer)
        throws IOError

    fn evict(frame: read write Frames.Pointer)
        throws IOError

    fn flush(frame: read write Frames.Pointer)
        throws IOError

    fn flush() throws IOError
}
```

This is a semantic sketch. It does not assert that `source`, `Records.Page`,
`ReadLease`, `WriteLease`, `transparent access` or `Records.map` are their final
spellings.

## Runtime state for two frames

Assume pages `4` and `9` are resident:

```text
Frames
    F0 = { page: 4, replica: Clean, io: Idle, version: 12, pins: 0 }
    F1 = { page: 9, replica: Dirty, io: Idle, version: 8, pins: 1 }

Page 4
    file version 12
    frame version 12
    either copy may satisfy a read

Page 9
    file version 7
    frame version 8
    F1 is authoritative
    F1 cannot be evicted because it is dirty and pinned
```

The implementation may keep versions only as proof or debug metadata when a
cheaper representation proves the same facts. Versions are part of this model,
not necessarily bytes stored beside every production frame.

## Operation A: open an existing file

Opening is not logical creation of records. The bytes already exist.

The operation performs:

```text
open the physical file with exclusive ownership or a stable snapshot
-> validate magic, format version and codec witness
-> validate file length, record count and arithmetic overflow
-> scan and validate every encoded R through the bounded frame buffer
-> establish which logical identities are valid records
-> publish Records and its origin
```

No `Records.Pointer` may be constructed before bounds, structural validation and
decoding validation make it a live `R`. This vertical slice uses eager validation
at open while retaining only two frames. A possible lazy design is a separate
future semantic case: it cannot call unvalidated slots a `set Records: R`.

Candidate syntax:

```efen
var records = PagedFile<User>(path: "users.dat")
```

Inside the layout, the draft writes the decisive operation as:

```efen
Records.map(file)
```

Its semantic distinction from the other population operations is:

```efen
Records.create(...)       // create one new logical member
Records.create(count: n)  // create several new logical members
Records.reserve(capacity: n)
Records.map(bytes)        // recognize existing physical contents as members
```

`map` borrows the file source owned by the layout; it does not consume the
source binding. Rehoming an already typed population changes origin and is left
out of this slice until its pointer and ownership semantics are designed.

## Operation B: transparent read on a cache hit

User code remains ordinary:

```efen
let name = user.name
```

The transparent implementation performs:

```text
page = pageOf(user)
frame = findResident(page)
require frame.replica is Clean or Dirty
require frame.io == Idle
increment frame.pins
project user.name through frame.bytes
read the projected place
decrement frame.pins when the logical borrow ends
```

Cache metadata may change. The logical value does not.

## Operation C: transparent read on a cache miss

The same user code:

```efen
let name = user.name
```

may perform:

```text
page = pageOf(user)
frame = acquireFrame(page)
load(page, into: frame)
publish frame as Clean
pin frame
project and read user.name
release the pin
```

`acquireFrame` reuses an unpinned frame or, while `Frames.count < frameLimit`,
creates one through `Frames.create(...)`. `reserve` alone would not create a
frame. All fallible work occurs before the frame is published as a current
replica. If the read fails, the previous cache mappings and the logical file
remain valid.

## Operation D: logical write

User code:

```efen
user.name = "Alice"
```

performs:

```text
acquire or load the page for write
obtain exclusive logical write authority
pin its frame
project the selected field
prepare the encoded replacement and every fallible auxiliary allocation
perform a no-throw physical commit of the prepared replacement
advance the logical version without wrap
publish the frame as Dirty and authoritative in the same commit
release the pin at the end of the borrow
```

An implementation may update in place only when it proves that the physical
write and the publication of `Dirty` cannot throw or suspend. A fallible field
encoding never mutates a frame still described as `Clean`.

When the assignment returns, later reads through this layout observe `Alice`.
The durable file may still contain the earlier value.

## Operation E: borrow and pin

```efen
let name = &read user.name
consume(name)
```

The borrow's origin includes the logical record and the access lease. The frame
remains pinned until the last use of `name`. During that interval the layout
rejects or delays operations that would evict, remap or destructively rewrite
the frame.

The lease itself need not be user-visible. It is the lowering evidence carried
by the ordinary Efen borrow.

## Operation F: select an eviction victim

Replacement policy is ordinary layout code. An LRU implementation may inspect
access metadata and select any unpinned frame.

```text
candidate.pins must equal 0

candidate.replica == Clean and candidate.io == Idle:
    remove the page-to-frame mapping
    reuse the frame

candidate.replica == Dirty and candidate.io == Idle:
    flush the candidate
    remove the mapping only after successful flush
    reuse the frame
```

If every frame is pinned, transparent access may wait, suspend or return an
error according to its published effect contract. Storage may not silently
invalidate a live borrow.

## Operation G: flush one dirty frame

```text
require frame.replica == Dirty
capture version v and immutable bytes for that version
mark frame.io as Flushing while the frame remains authoritative
write version v to a fresh page image or through the chosen recovery protocol
wait for the requested durability boundary
if frame.version == v on success, publish frame as Clean and io as Idle
if a later write produced version v+1, retain Dirty authority and publish io as Idle
on failure, retain Dirty authority, publish io as Idle and mark durable state
    Unknown if the protocol cannot prove that the old durable image survived
```

The destination file page must not become current merely because the operating
system accepted part of a write. Publication follows the source's declared
durability boundary. A plain in-place page write may tear on failure; a layout
that promises reopen after failure must supply journal, copy-on-write or an
equivalent recovery protocol.

## Operation H: flush the layout

User code explicitly requests durability:

```efen
records.flush()
```

The operation flushes every dirty authoritative frame. With exclusive write
authority for the duration, success establishes:

```text
for every logical page p:
    FilePage(p) == Logical(p)
```

A concurrent variant must repeat until no newer dirty version remains, or state
a weaker snapshot durability guarantee. A multi-page `flush()` does not
automatically promise crash-atomic replacement of all pages. That stronger
property requires a journal, copy-on-write root or another persistent
transaction algorithm inside the layout.

## Operation I: close and destruction

The semantic choices are deliberately left open for approval:

- `close()` may flush and report `IOError`;
- destruction may require that no dirty frame remains;
- an explicit discard operation may abandon non-durable logical writes only
  when the type's public contract permits it;
- a journaled layout may commit or roll back according to its own protocol.

An ordinary destructor cannot silently discard acknowledged logical writes and
cannot report an asynchronous flush failure. A likely safe shape is an explicit
fallible `close()` that reaches a clean closed typestate, followed by no-throw
resource destruction. Exact policy remains a semantic case below. Whatever
policy is selected, frame memory, mappings and the file handle are released
after all outstanding access leases end.

## Extension case J: append records

Append is deliberately outside the read/write/flush vertical slice. It exposes
an additional persistent-publication problem rather than a new cache-access
primitive. Candidate logical creation remains:

```efen
var user = Records.create(
    id: id,
    name: name
)
```

Bulk creation uses the same population operation:

```efen
var users = Records.create(
    count: input.count,
    initializer: (i) => User(
        id: input[i].id,
        name: input[i].name
    )
)
```

The result contains the new `Records.Pointer` identities. Whether those pointers
own removal of their records or merely carry authority to access a population-
owned persistent member is an unresolved semantic case below. Physical code may
grow the file once, but a batch larger than the two-frame cache cannot retain
every new logical value solely as dirty RAM authority. It must stream provisional
pages to non-authoritative file space and atomically publish a new header/root,
or use a journal. Until that publication protocol is selected, the document does
not claim all-or-none persistent bulk `create`.

## Lowering outline

The expression:

```efen
user.name = "Alice"
```

has a lowering equivalent to:

```text
lease = PagedFile.Records.access.acquireWrite(user)
place = lease.project(field: User.name)
replacement = prepareWrite(place, "Alice")
commitWriteAndPublishDirty(lease, place, replacement)
lease.release()
```

`release()` is placed on every normal and exceptional exit. The actual emitted
code may inline the hit path and move the miss path into a cold helper:

```text
if directory[page].resident:
    fast projected access
else:
    loadPageSlow(page)
```

The semantic contract is the same for both forms.

## Safety obligations

The compiler or verification backend must establish all of the following.

### Logical safety

- Every `Records.Pointer` belongs to this layout instance.
- Its identity denotes a live record.
- A record identity remains stable across cache movement and file remapping.
- Reads observe the current logical version.
- Writes require exclusive logical authority.

### Physical safety

- A frame contains at most one page at a time.
- A logical page has at most one resident writable authority.
- A `Clean` idle frame matches the corresponding durable page.
- A `Dirty` or `Flushing` frame is the authority for its logical page.
- At most one RAM frame is published for one logical page in this slice.
- An unpublished loading frame cannot satisfy a read.
- A pinned frame cannot be evicted or moved incompatibly with its borrows.
- Failed loading does not publish uninitialized bytes.
- Failed flushing does not discard dirty authority.

### Construction and destruction

- Structural file validation precedes publication of addressable identities.
- Encoded values are validated before they are published as values of `R`.
- Partially initialized records are not live members.
- Every published field is initialized exactly once.
- Every logical value is destroyed exactly once when removed.
- Physical replicas do not cause duplicate logical destruction.
- Closing waits for or rejects outstanding leases according to its contract.

## Semantic cases that precede final syntax

The example exposed questions that cannot be settled by renaming methods.

### P1. Ownership of persistent population members

Dropping a local pointer returned by `Records.create(...)` must not silently
delete a durable record. The eventual population contract must distinguish
access/removal authority from the lifetime of a member owned by persistent
storage. This document does not yet choose the exact return type of `create`.

### P2. Eager and lazy value validation

This slice chooses eager validation: open scans the file with bounded RAM and
publishes `Records` only after every encoded value is known to be an `R`. A lazy
variant requires a separate population of encoded slots; successful decoding
may then produce an `R`. It cannot publish the unvalidated population itself as
`set Records: R`.

### P3. External mutation of the file

This slice opens an exclusive file or immutable snapshot. A source that permits
external writers needs epochs, invalidation and repeated validation; otherwise
the predicate equating a clean frame with its file page is false.

### P4. Failure of persistent writes

Dirty RAM remains the logical authority after a failed flush. An in-place file
write may nevertheless leave a torn durable image. Reopening after such failure
requires a journal, copy-on-write publication or another recovery algorithm.

### P5. Closing

An explicit fallible close can flush and enter a clean closed typestate. A
no-throw destructor can then release resources. Explicit discard, retry after
failed flush and process-crash recovery remain separate policies.

## Syntax cases for sequential approval

The semantic example above leaves these surface questions independent.

### S1. Declaring several physical areas

Candidate:

```efen
source file: FileMemory
source cache: RamMemory
```

Required meaning: both areas participate in one logical layout. `layout` is not
identified with either source.

### S2. Declaring logical and physical populations

Candidate:

```efen
set Records: R
set Frames: Frame
```

Required meaning: both are high-level populations with their own pointer types.
Their role as logical contents or physical realization follows from the
algorithms and relations, not from two different kinds of `set`.

### S3. Accepting existing physical contents

Candidates:

```efen
Records.map(file)
```

Required meaning: `map` validates/interprets physical contents through a source
that remains owned by the layout. Transfer and rehoming of an already typed
population is a separate future case because it changes origin.

### S4. Declaring a transparent access implementation

Candidate:

```efen
transparent access Records {
    fn acquireRead(...)
    fn acquireWrite(...)
    fn release(...)
}
```

Required meaning: the whole operation group, rather than one function, may be
used to realize ordinary pointer field access.

### S5. User syntax for transparent access

Direction agreed in the current discussion:

```efen
let value = pointer.field
pointer.field = value
```

No marker is required at the use site. Effects and suspension remain visible in
the containing function's inferred or declared contract.

### S6. The internal access result

Candidates:

```efen
ReadLease<R>
WriteLease<R>
AccessLease<R, Mode>
```

Required meaning: the result keeps physical storage pinned for the logical
borrow lifetime and provides field projection. It need not be nameable by
ordinary user code.

### S7. Logical creation and capacity

Direction agreed in the current discussion:

```efen
Records.create(...)
Records.create(count: n, initializer: ...)
Records.reserve(capacity: n)
```

`create` changes logical membership. `reserve` changes only available physical
capacity.

### S8. Durability

Direction agreed in the current discussion:

```efen
pointer.field = value
records.flush()
```

The assignment completes after a RAM replica becomes logically authoritative.
`flush()` separately requests durability.

### S9. Closing policy

Candidates:

```efen
records.close() throws IOError
records.close(discard: true)
```

Required decision: whether ordinary close flushes, rejects dirty state or may
explicitly discard it.

### S10. Observable waiting for a frame

Required decision: when all frames are pinned, transparent access may suspend,
throw a resource error or use a policy chosen by the access implementation. The
selected behaviour must remain in the public effect contract.

### S11. File representation witness

`R` alone cannot describe bytes in a file. The layout needs a retained witness
that supplies encoded size, alignment, endian, valid bit patterns, field
projections and lifecycle rules. Candidate shape:

```efen
generic Format: RecordFormat<R>
let format: Format
```

The exact generic placement and name remain open; the semantic requirement does
not.

### S12. Relational predicates on physical properties

The frame sketch uses property predicates such as:

```efen
var page: Records.Page? {
    page == null || Frames.count(where: it.page == page) == 1
}
```

Required meaning: a frame page is unique among the live `Frames`; the condition
is attached to the property whose mutation can break it. The exact spelling for
quantifying another population remains open.

### S13. Stable page identity

The sketch writes `Records.Page` for the stable page containing a logical
record. It is not an array index invalidated by append or file growth. The exact
derived-type spelling remains open; its required semantics are stable identity,
origin in this layout and checked conversion to the current file range.

## Validation scenarios

The design is acceptable only if its eventual implementation passes at least
these behaviour tests.

1. Repeated reads of one record load its page once and return the same value.
2. Reading records on three pages through two frames performs a valid eviction.
3. A dirty unpinned victim is flushed before reuse.
4. A failed victim flush leaves the dirty page logically authoritative.
5. A live field borrow prevents eviction of its frame.
6. A failed page load publishes neither a mapping nor initialized records.
7. A logical write is immediately visible to later reads before `flush()`.
8. A successful exclusive `flush()` makes every acknowledged logical write
   durable.
9. A remap preserves `Records.Pointer` identities.
10. A raw or address-dependent borrow prevents an incompatible remap.
11. A fallible field encoding never leaves mutated bytes marked `Clean`.
12. A flush of version `v` cannot mark a later version `v + 1` clean.
13. An external writer cannot invalidate a live clean-frame predicate.
14. Closing with dirty frames follows the selected and documented policy.

Bulk `create` receives its own validation cases after its header/root publication
protocol is selected.

## Generalization boundary

The same structure is a hypothesis to test against the following cases before
adding new language primitives:

- register allocation: logical values realized by registers and spill slots;
- DMA: logical buffers realized by host, in-flight and device copies;
- GPU memory: host and device replicas with explicit authority transfer;
- NUMA: one logical object with node-local read replicas;
- compressed storage: logical fields realized by decoded cache blocks;
- database pages: RAM frames backed by journaled or copy-on-write file pages.

Only the physical populations, access functions and predicates change. Logical
pointers, ownership, borrows, effects and publication rules remain the same.
