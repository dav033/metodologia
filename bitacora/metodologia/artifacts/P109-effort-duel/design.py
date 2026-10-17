"""Freeze three difficult dossiers and independent expected roots before calls."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CASES=[]
def add(ident,title,text,roots):
    CASES.append({'id':ident,'title':title,'input':text.strip(),'oracle':[{'id':f'{ident}-D{i}','root':root} for i,root in enumerate(roots,1)]})
add('E1','Multi-region transfer cutover, replicated decisions and escrow recovery',r'''
CURRENT CONTRACT — authoritative over old memos
R1. Transfer ID identifies exactly (source tenant, source account, destination tenant, destination account, currency, amount_minor), all immutable. All IDs are arbitrary Unicode strings. A repeated ID with another tuple is rejected; a true retry returns its previous decision. Every accepted transfer debits source once and credits destination once, and source available money cannot go negative. All integers are exact and signed at arbitrary precision; amount is validated strictly positive and currencies equal before these snippets.
R2. Each account has escrow rights partitioned across regions. Sum of regional rights equals available account balance. An accepted transfer consumes rights exactly once at the source. Reallocating rights must neither create nor destroy them. Network delivery and worker recovery may duplicate/reorder any message. Rediscovering an accepted transfer on a new leader must remain safe. Accounts and transfers remain live indefinitely; any pruning must preserve retry safety indefinitely.
R3. Each shard commits decisions using a replicated log. Configurations have a monotonic configuration number separate from log index. During joint old→new configuration, a commit requires an old majority AND a new majority until a joint-config entry is itself committed. Servers can overlap across configurations; votes are authenticated and each server occurs once in the vote set. ACK means the server durably stored the exact entry digest at that log index; two different entries may have distinct ACK sets. A locally appended entry is not yet committed.
R4. A transfer is considered irrevocably committed only if its transaction decision has a durable commit certificate, not merely an append ACK. Participants may prepare and hold resources while its decision is uncertain. No transfer that has a durable COMMIT may later abort; after uncertainty, replay/reconciliation can wait rather than fabricate a decision. A committed ledger prefix must not be skipped during cross-region recovery.
R5. Tenant read revocation applies to every new read, including cached composite balances and historical snapshots. A composite balance response must represent ONE committed global snapshot index. Requests name their tenant and carry authenticated principal; owner authorization may change at any time, and must be evaluated at the read's linearization point.
R6. Cutover starts a new globally monotonic leader epoch. A signed read token binds tenant, committed global index and its log digest. A token cannot be used on a branch with a different digest even if the integer index is identical. Compaction may erase log bytes only after both an authenticated complete checkpoint and all needed dedup/decision obligations are preserved.
VERIFIED BASELINE — do not re-audit these components
G1. Serial transactions and row locks are correct within one region. A region's rights row, transfer row and outbox can be changed atomically. No cross-region ACID exists. Messages are authenticated; destination tenant/account bindings are correct. The transport gives at least once, not exactly once, delivery.
G2. Ledger append is idempotent on (leader_epoch, operation_key) within that epoch only. Distinct epochs intentionally have separate namespaces. Committed global indices are monotonic on a single branch. A durable commit certificate is obtained only by await_commit(index,digest), not by append or ACK count alone.
G3. canonical_tuple performs injective typed encoding; durable compare_and_set and SQL predicates are correct. Hash collisions and random UUID collisions are excluded. current_auth reads authoritative policy; all signatures and cryptographic encodings are correct. Checkpoint payload validation is correct but the caller chooses which obligations it includes.
G4. The ordinary debit path enforces rights >= amount atomically and its outbox is committed with its rights decrement. The destination ledger applies each credit only once per globally unique transfer ID and rejects conflicting tuples. Negative rights cannot be caused by that ordinary path alone. The routing layer validates a principal's transfer privileges and separates tenants correctly.
G5. snapshot_component(account,index) returns that account's exact value at index; latest_component returns its latest committed value, potentially at different indices. Revocation does not purge old caches automatically.
CANDIDATE INTEGRATED PATHS
C1 request deduplication, before ordinary debit:
    fingerprint = sha256(canonical_tuple((src_tenant,src_account,dst_tenant,dst_account,currency)))
    prior = lookup_transfer(transfer_id)
    if prior:
        if prior.fingerprint != fingerprint: reject_conflict()
        return prior.decision
    # persist fingerprint with transfer tuple, then enter ordinary debit path
The stored row retains the amount too, but retries only compare fingerprint. T1 tests conflicting currencies/destinations and exact retries; same ID/new amount is not tested.
C2 regional rights rebalance, sender A (one serial local transaction):
    rights[A] -= n                  # prevalidated n <= current A rights
    outbox.append({'move_id':uuid,'to':B,'amount':n})
Receiver B, each delivery in a serial local transaction:
    rights[B] += message.amount
    receipt_table.insert_if_absent(message.move_id)  # diagnostic only; result ignored
The sender never repeats its decrement when its outbox retries. T2 tests one successful delivery and source conservation.
C3 source transfer failover recovery (accepted transfer row already exists):
    if row.state == 'ACCEPTED' and row.source_ledger_receipt is None:
        append_debit(epoch=current_leader_epoch,operation_key=transfer_id,amount=row.amount)
        # at this point worker can die; receipt saved after append succeeds
The accepted row and rights decrement are already durable. The ledger may have accepted the old-epoch debit while the receipt was lost. Ledger debits here record the already-authorized consumption; they do not consume rights again. T3 resumes only without leader change.
C4 replicate a decision while joint configuration is active:
    union = old_servers | new_servers
    committed = len(ack_servers & union) >= len(union)//2 + 1
This drives the same await_commit certificate facility used by callers. The voters always ACK the candidate's exact digest; there is no mixed-digest bug. T4 checks only old={a,b,c}, new={b,c,d}, ACK={b,c,d} and a full-union ACK.
C5 prepare/commit coordinator:
    # both participant prepares are durable, timeout responses remain UNKNOWN
    index,digest = append_log('COMMIT',transfer_id)
    durable_decision_index = index
    send_commit_to_participants(transfer_id)
    # return accepted to client; await_commit deferred to background
A leadership loss can truncate an uncommitted suffix. Participants trust this authenticated coordinator message and credit/debit according to it. T5 never loses leadership between append and commitment.
C6 participant recovery sweeper:
    if state == 'PREPARED' and now - prepared_at > 60:
        rollback_prepare(); mark_aborted()
A PREPARED participant may have missed a delayed commit message even while the coordinator has a durable certificate. No maximum delay/lease for decisions exists. T6 covers only transactions with no coordinator decision.
C7 recovery after snapshot install:
    if local_checkpoint.config_number >= remote_log_last_index:
        skip_remote_replay()
    else:
        replay_remote_committed_suffix()
The checkpoint contains its own exact committed_log_index too, but C7 never compares it. Configuration number and log index are independent dimensions; each monotonic within its dimension. T7 uses equal config and log indices.
C8 composite read endpoint:
    authorize = current_auth(principal,tenant)
    require(authorize)
    parts = [latest_component(a) for a in requested_accounts]
    return sum(p.balance for p in parts), max(p.global_index for p in parts)
Account list is tenant-scoped and current policy stays unchanged through this call. An atomic transfer between requested accounts can commit between component reads. T8 reads only a quiescent ledger.
C9 signed historical read endpoint (separate from C8):
    cached = cache.get((tenant,token.index))
    if cached: return cached.payload
    require(current_auth(principal,tenant))
    verify_signature(token)
    require(token.tenant == tenant)
    require(token.index <= local_committed_index)
    payload = snapshot_component(account,token.index)
    cache.put((tenant,token.index),payload)
    return payload
The cache stores the complete authorized response with account/request digest bound in a verified outer key; ignore omitted key fields. Signature verification is enforced by middleware BEFORE this function, even on cache hits. The cache is shared by principals of the same tenant. On misses this function does NOT check token.digest against the local branch at token.index. T9 tests cache fill, hit with same principal, and valid tokens on the same branch. Distinct branches at equal indices are possible after disaster recovery, even though indices on one branch never regress.
C10 checkpoint and retention policy:
    checkpoint includes account balances, remaining regional rights, current config,
    committed index/digest, and only ACTIVE transfer/prepare rows.
    after checkpoint is durably replicated: delete COMPLETED transfer rows older than 30 days;
    remove their source-ledger operation-key dedup entries too.
Destination global transfer dedup is independently retained forever (G4). The API promises indefinitely retry-safe transfers and transfer IDs are never expired by the API. A caller may retry an old transfer on a new source leader. T10 exercises restore after 7 days only.
DESIGN NOTES TO RECONCILE
Old memo M1 says union-majority, prepared TTL and latest-value sum are simpler and sufficient; it predates R3/R4/R5. Proposed rollout orders T1/T2, then T3–T7, then T8–T10. Each test named above passes against these candidates. The ordinary debit validation, destination credit idempotency, cryptography, row locks and tenant routing are already correct. Only report concrete violations supported by this dossier. Where C9 has multiple independent failures, keep their causes distinct; where C5/C6 both risk a split outcome, identify whether their witnesses need the other candidate defect.
''',[
'C1 fingerprint omits immutable amount so conflicting retry accepted',
'C2 ignores duplicate receipt result, duplicates rights on redelivery',
'C3 epoch-scoped ledger dedup repeats debit after failover lost receipt',
'C4 union majority does not enforce both old and new majorities',
'C5 sends commit before log commitment; uncommitted suffix can be lost',
'C6 TTL aborts prepared participant despite independently durable COMMIT',
'C7 compares configuration number to log index and skips committed suffix',
'C8 independently latest components are not a common snapshot',
'C9 cache bypasses current authorization',
'C9 validates integer index but not signed branch digest',
'C10 drops source dedup/transfer identity for indefinite retries'])
add('E2','Bitemporal marketplace settlement, exact optimization and adversarial rounding',r'''
AUTHORITATIVE CONTRACT
R1. Orders are tenant-scoped; each order has immutable currency and an exact integer gross_minor. Corrections are full replacements, NOT deltas: each identifies the same order and a strictly monotonic revision. Events may arrive late/out of order. At cutoff C use the greatest revision whose effective_at <= C AND recorded_at <= K, where K is the report's pinned knowledge time. Effective time and knowledge time are distinct. If no version qualifies, omit the order. A report must remain reproducible from its retained inputs even after later corrections and policy changes.
R2. A tenant's commission is a signed rational p/q (q>0), versioned by effective time. The commission version is selected by ORDER effective_at, not by report generation time or payment time. Per-order net is gross*(q-p)/q as an exact rational. Aggregate eligible order nets by tenant/currency first; round that aggregate ONCE to an integer minor unit, ties AWAY from zero. Reversals are negative gross and obey the same rule. Rounding may not depend on row order, machine float precision or a finite Decimal context.
R3. Net cents are allocated among owners by rational weights summing to one. For signed integer N, allocate |N| by floor(|N|*weight) plus largest remainders; ties by ascending immutable owner ID; then restore N's sign to every allocation. Allocations sum exactly N, including negative N, and reversing N negates every owner's amount. An owner ID can be Unicode; the verified canonical ordering is bytewise on canonical UTF-8 IDs, supplied by owner_sort_key.
R4. Settlement payouts are grouped per tenant/currency and may be netted with negative obligations only in that same group. Every selected payout has positive exact integer net value, a recipient, a nonnegative exact integer resource cost and a risk class. Daily capacity is 10 units shared across eligible payouts. Primary optimization is maximum number of payouts, secondary maximum total integer net value, tertiary lexicographically smallest sorted payout-ID list. Risk classes are eligibility restrictions already validated, not ranking terms. Zero-cost payouts are allowed. The optimizer must match the exact optimum, not a heuristic approximation. Output has no more than capacity worth of costs.
R5. Payout dedup identity is (tenant,payout_id), both arbitrary strings; currency is immutable for that identity. Provider IDs are globally unique UUIDs returned by the provider. Provider requests are idempotent only for the exact same request body with the same key. A payout's amount is frozen at selection; cancellation or later correction may stop an unsent payout but may never change a possibly submitted request body. Unknown remote acceptance must be reconciled before reusing its money. Provider lookup_by_key returns authoritative accepted or authoritative never_accepted, possibly after a wait; timeouts are UNKNOWN.
R6. Release of report output must enforce current recipient authorization, even when the report was planned under an earlier policy. Approved report inputs and financial facts are immutable. Deleting a principal or changing permissions must not erase audit evidence. Output object access is enforced by the final application endpoint; the raw storage URLs are private and cannot bypass that endpoint.
VERIFIED COMPONENTS
G1. Exact Fraction arithmetic, integer multiplication, floor division, canonical typed tuple encoding and owner_sort_key are correct. No overflow is possible. SQL transactions use serializable isolation with retries; selection locks and reservation capacity accounting are correct. External provider calls never occur inside DB transactions.
G2. Ingest authenticates, preserves tenant/order identity, rejects duplicate (tenant,order,revision) with conflicting content, and stores all versions. ISO timestamps normalize to UTC and compare exactly. Each version has its original order effective_at and event correction effective_at separately; snippets use correction_effective_at to select corrections and order_effective_at to select commission. initial version's correction_effective_at equals order_effective_at.
G3. The optimizer gets a complete eligible list and current reserved capacity; its result is atomically reserved once. Ledger unique constraints and payout states are correct; only candidate request preparation/reconciliation below may violate remote semantics. Current authorization checks are correct when called. Output paths and content sanitization are correct. Ordinary provider success is durable and applied exactly once locally.
G4. Historical policies are append-only and queryable by effective timestamp; report K/C are stored. Provider keys use canonical_tuple, globally collision-free under the stated assumptions. The canonical currency and tenant grouping helpers are verified; the caller may choose the wrong grouping arguments.
CANDIDATE REPORT / PAYOUT PIPELINE
B1 eligible versions for each order:
    candidates = [v for v in versions if v.correction_effective_at <= C]
    row = max(candidates,key=lambda v:v.revision) if candidates else None
    # K stored in the report header but not consulted here
    # row is the entire replacement; never add revisions
B2 commission for selected order row:
    policy = policy_at(tenant, now_of_report_generation)
    net = Fraction(row.gross_minor*(policy.q-policy.p),policy.q)
Policies can change between the order date and report generation; there is no requirement that correction_effective_at changes order_effective_at.
B3 amount aggregation (separate from B2, assume policy supplied correctly when evaluating B3):
    rounded_order_nets = [half_away_to_integer(exact_net(row)) for row in selected_rows]
    tenant_currency_total = sum(rounded_order_nets)
The rounding primitive is correct for every signed rational; only its placement is in question. Tests use integer nets only.
B4 owner allocation for integer group total N:
    ordered = sorted(owners,key=owner_sort_key)
    base = {o: (N*o.weight.numerator)//o.weight.denominator for o in ordered}
    missing = N-sum(base.values())
    # rank by Fraction(N)*weight-base[owner], descending; tie owner_sort_key ascending
    for owner in ranked[:missing]: base[owner] += 1
    return base
Python // floors toward negative infinity; slices behave normally. Weights are nonnegative exact Fractions. Tests check sum and positive N, but not reversal symmetry. For this question, merely conserving a negative total is insufficient.
B5 netting before payout selection:
    groups = group_by(lambda obligation: obligation.currency)
    for currency, obligations in groups: apply_credit_offsets(obligations)
apply_credit_offsets is correct for a supplied group: it uses negative balances to reduce positives until the group's net is exhausted. It does not inspect tenant IDs. All obligations from every tenant are in this batch. Tests have one tenant per currency.
B6 optimizer:
    ranked = sorted(eligible,key=lambda x:(x.cost,-x.net,x.id))
    selected=[];remaining=capacity
    for x in ranked:
        if x.cost<=remaining: selected.append(x);remaining-=x.cost
    return selected
The candidate often maximizes count but never performs exchanges among equal-cardinality selections. Tie comparisons use correct canonical IDs. Tests use equal net values and uniform costs. Exhibit a counterexample for the declared objective, not a different objective such as highest net/cost.
B7 provider submit for each selected payout P:
    key = hash(canonical_tuple((P.tenant,P.payout_id)))
    latest = latest_report_total_for(P)  # corrections may already exist
    body = {recipient:P.recipient, amount_minor:latest, currency:P.currency}
    provider.submit(key,body)
P retains its original frozen positive amount. On first attempt a timeout may have accepted body1. A retry reevaluates latest and may submit a different body2 under the same key. The provider rejects a conflicting body; it does not replace the first request. Tests retry only with unchanged reports.
B8 unknown-acceptance timeout policy:
    if payout.state=='UNKNOWN' and now-payout.last_attempt_at > 300:
        release_money_reservation(payout)
        payout.state='CANCELLED'
No call to lookup_by_key occurs here. A separate worker may later discover provider acceptance, but capacity/money is released immediately and another payout may reserve it. No provider auto-cancel TTL exists. Tests assume timeout means no acceptance.
B9 immutable report evidence:
    report.input_evidence = {'C':C,'K':K,'version_ids':selected_version_ids,
                             'policy_ids':selected_policy_ids,'principal_id':principal_id}
    # audit copies of exact version/policy payloads are not retained here
    # historical versions/policies themselves stay queryable forever (G2/G4)
    report.owner = principal_id
Cleanup: when a principal is deleted, cascade-delete all owned reports, their input_evidence and allocations, INCLUDING reports with submitted/settled payouts. Payout receipts survive but contain only provider key and aggregate amount, not the order revision/policy list. The cleanup is called automatically by account administration. Tests delete principals only before report generation.
B10 report release endpoint:
    report = load_immutable_report(report_id)
    require(report.planning_auth_result == 'allowed')
    return report.output
This endpoint authenticates principal and binds report_id to the request's tenant in correct middleware, but does not authorize that principal's current report-read privilege. A principal may remain a tenant member while losing this privilege after planning. Tests never revoke between planning and retrieval.
REVIEW CONTEXT
Old note says the availability of an append-only policy registry makes evidence snapshots optional. Under G2/G4, that part is sound while retained report version IDs exist; don't invent a missing data-retention defect in B9's IDs themselves. Another old note treats a timeout as rejection, permits per-row rounding, and says any conserved signed allocation is fair; these contradict R2/R3/R5. The proposed rollout marks all B1–B10 production-ready based on the narrow tests above. Report independent causes with exact numerical/lifecycle witnesses; do not count the same omitted test as another defect. Do not demand fees, tax, currency conversion, ML risk models or API-dollar budgets that the contract never asked for.
''',[
'B1 ignores pinned knowledge time recorded_at <= K',
'B2 selects commission at generation time not order effective time',
'B3 rounds each order before aggregation',
'B4 signed floor allocation violates sign-restored magnitude/reversal symmetry',
'B5 nets obligations across tenants because groups omit tenant',
'B6 cheapest-first fails secondary net objective among maximum count',
'B7 resubmits unfrozen latest amount, may change body on unknown retry',
'B8 releases money despite unknown provider acceptance',
'B9 principal deletion erases immutable financial report evidence',
'B10 uses historical planning auth rather than current report-read privilege'])
add('E3','Hermetic build reuse, attested deployment and concurrent artifact garbage collection',r'''
AUTHORITATIVE CONTRACT
R1. Build output depends on source bytes, resolved transitive dependency artifacts, compiler flags, target architecture and the complete normalized environment allowlist. A reused result must be bit-for-bit equal to a fresh build of the requested inputs. Build nodes form a validated DAG. A target may be requested while a dependency is rebuilding; only completed immutable artifacts may satisfy edges. A node's build version is monotonic per node; same version on different nodes has no ordering meaning.
R2. Dependency edges include link-time generated schemas, even when no source imports a file. A deployment contains executable and schema artifact digests from one committed build generation. Compiler execution is hermetic; the verified compiler produces a deterministic output from the inputs it actually receives. Dependency hashes must reflect actual content, not just path names. No digest collision exists.
R3. Artifact tenant ownership is authoritative and each retrieval authorizes the caller before revealing bytes, including cross-tenant cache dedup hits. Identical artifact content may be physically deduplicated, but knowledge of its digest grants no read privilege. Existing references may be read only under the owning tenant's current policy. Blob transport, decompression and tar extraction are verified secure; do not re-audit them.
R4. Signed build attestations bind artifact digest, source revision, resolved dependency digests, environment/flag digest, target architecture, builder identity and build generation. Deploy authorization requires an allowed builder and all attested inputs equal the approved manifest for this deployment. A genuine signature for some other build is insufficient. The approved manifest itself is correctly authenticated and immutable.
R5. Deployment activation is atomic across the executable and schema, with a durable monotonically increasing activation epoch. Every accepted worker must run a complete pair from one approved generation; at a moment during rollout, old and new workers may coexist, but each must serve a consistent pair. A successful activation ACK must imply the durable authoritative active generation changed. A stale worker must not overwrite newer activation state; local fencing and remote worker state are distinct.
R6. Cleanup must not delete artifacts referenced by active or rollback-pinned deployments, or by an accepted in-progress activation. Listing roots and deleting blobs occur concurrently with activation. A verified deletion tombstone prevents NEW references only after the tombstone is committed; an already-existing activation reference cannot be discarded. Each artifact can be restored from build sources, but this does not waive the availability contract. Rollback pins live 24h after the LAST deactivation that could need them.
R7. Incremental build reuse must remain correct after process crash. A worker can die after output upload and before a DB transaction commits. Output objects are immutable, globally content-addressed and staged until published. Build status COMPLETE implies its exact resolved-input manifest and output digest are durable together. Failed builds must never be used as dependencies.
VERIFIED BASELINE
G1. SHA-256, canonical typed encodings and signature verification are correct. Object storage is strongly consistent and immutable by digest; finalize blob makes it readable, but DB COMPLETE publication is a separate operation. Compiler sandbox, declared input tracing and normalized allowlist enumeration are correct WHEN invoked. Secrets are absent from the allowlist; do not propose storing them.
G2. The artifact DB is serializable and supports atomic CAS, reference insert, tombstone check and activation transaction. The candidate explicitly shows each transaction boundary. Each worker can atomically activate a local complete pair when given one; it does not need to be sent two separate commands. The remote worker API supports an idempotency key for an activation command but does not itself check global activation epochs against other keys.
G3. Generic source import scanning is correct, but generated schema B has no source import in executable A. Its role is a link-time input. Source/dependency versions and flags are available to the coordinator; the candidate chooses which to hash. Current artifact policy, tenant mapping and root enumeration are correct at the instant called. Cron timings and network latency have no upper bound. The initial deployment is valid.
G4. A deployment reference inserted in the DB makes its artifacts roots immediately, INCLUDING while activation is pending. Published successful build manifests are immutable and retained; no dependency-output mutation happens after publication. Other unrelated build graph edges are complete. Unknown remote activations may be reconciled; callers may wait rather than claim success.
CANDIDATE PATHS
A1 incremental cache key for executable A:
    key = hash(canonical_tuple((source_digest, tuple(d.id for d in direct_dependencies), target_arch)))
    if cache.has(key): return cache.result(key)
    # flags, normalized env and dependency content digests are all available but not in key
The caller correctly includes source content, typed framing and target architecture. A dependency ID is a stable name, not an artifact digest. The output can depend on any supplied flag/env variable and dependency content. Treat these omitted build inputs as one key-completeness cause, not one finding per field. Tests alter only source or architecture.
A2 DAG edge construction:
    edges = generic_source_import_edges(nodes)
    # A links to generated schema B via its command line; no import edge exists
    ready_nodes = nodes_with_completed_predecessors(edges)
A uses B's schema artifact content in code generation. Independent file ownership keeps A and B outputs in separate paths; it does not enforce dependency order. Tests start with B already built at the requested generation.
A3 collect dependency outputs for any ready node:
    outputs = [artifact_for(dep, version=max_completed_version_across_all_nodes)
               for dep in node.dependencies]
artifact_for(dep,version=v) returns dep's latest completed artifact with its own version <= v; it is a legacy "as of" API. Requested manifest separately contains exact desired versions per dependency. Version maxima are local to each node and incomparable across nodes. Example permitted inputs: desired B version2 exists, unrelated C completed version100, B version3 also completed; build asks B2 and C100. Tests use equal versions for all nodes.
A4 publish successful build after compile:
    upload_immutable(output_digest, bytes)
    tx1: build.status='COMPLETE'; build.output_digest=output_digest
    # crash possible here; resolver's COMPLETE rows are immediately visible
    tx2: build.resolved_input_manifest=resolved_inputs
The bytes upload is complete before tx1. On recovery, COMPLETE rows are reused and missing input manifests are filled from the then-current mutable request record; requests can have moved to another revision while the process was dead. R7 requires durable exact inputs/output together. Tests stop workers only before compilation.
A5 artifact GET:
    if physical_blob_exists(digest): return physical_blob(digest)
    require(current_artifact_policy(principal,tenant,digest))
    return not_found()
Digest syntax and request tenant are validated; caller is authenticated. Private storage is accessible only through this endpoint. Object existence is global due dedup; the policy would deny a caller without a tenant-owned reference even if identical content exists for another tenant. Tests exercise only owned blobs.
A6 attestation gate:
    attest=verify_signature(attestation)
    require(attest.builder in allowed_builders)
    require(attest.artifact_digest==deployment.executable_digest)
    # other fields kept for audit but not checked against approved manifest
    approve_activation(deployment)
The schema digest is provided in the attestation's dependency list. A legitimate builder can sign many source revisions/flags/architectures. Approved deployment manifest names exact fields R4. The candidate verifies no equality for them. Tests provide matching manifests only.
A7 dispatch activation:
    # DB has durable pending deployment reference with complete new pair (Anew,Bnew)
    worker.activate_executable(Anew,idempotency_key=deployment_id+':exe')
    worker.activate_schema(Bnew,idempotency_key=deployment_id+':schema')
The worker APIs above change one component immediately; a request may be served between them. Old pair is (Aold,Bold). Versions have incompatible schema layouts, and both API calls can succeed. The API also offers activate_pair(pair,key) as G2 states. Tests send no requests during the gap.
A8 global activation completion:
    result = worker.activate_pair(pair,key=deployment_id)
    if result.accepted:
        send_success_ack_to_operator()
        tx: CAS(active_epoch,expected=old_epoch,new=new_epoch); set_active_pair(pair)
A remote accepted result is not a durable global CAS result. A newer coordinator can commit epoch12 while the earlier epoch11 worker is paused. On CAS failure, A8 returns without a DB change but the ACK has already been sent. For this path the remote worker correctly activates its own complete pair (no A7 split). Do not assume a local CAS can revert an already-sent ACK.
A9 garbage collection:
    roots = list_referenced_artifact_digests()  # exact snapshot at time t0
    candidates = [d for d in blobs if d not in roots]
    for d in candidates:
        tx: insert_tombstone(d)  # no reference recheck in transaction
        delete_blob(d)
New activations insert durable references after t0 and before the tombstone. Their insertion transaction correctly checks no tombstone at insert time. Existing references do not automatically reject tombstone insertion. Tombstone/delete jobs are themselves idempotent; lost ACKs do not create new keys. Tests never activate while collecting.
A10 rollback pin expiration:
    on first deactivation of generation G:
        pin_until[G] = created_at[G] + 24h
    on every later deactivation: leave pin_until unchanged
G may have run for many days; it can be reactivated and deactivated again. Correct reference roots (G4) protect active G but not a deactivated G once its pin expires. A rollback request is allowed for 24h after the latest deactivation. Tests build, activate and deactivate within one minute.
INTEGRATION REVIEW NOTES
All candidate tests above pass. The old performance memo claims stable dependency names and independent ownership make A1–A3 sufficient; current requirements govern. There is no required cross-worker global stop-the-world rollout, no malicious hash collision, and no insecure archive extraction; don't invent those defects. A3's requested-version mismatch and A1's cache-key omissions are independent: A3 can compile the wrong version on a cold cache even after fixing A1, and A1 can reuse wrong outputs with a correct resolver. A4's publication boundary and A6's attestation equality are likewise separate. Provide concrete traces that respect the verified baseline. Favor minimal sound corrections over replacing the whole compiler, DB or object store.
''',[
'A1 cache key omits resolved dependency content, flags and normalized env',
'A2 omits link-time generated schema edge',
'A3 global maximum of unrelated node versions selects wrong dependency version',
'A4 COMPLETE and exact input manifest not atomic; recovery fabricates historical inputs',
'A5 physical dedup hit bypasses current tenant artifact authorization',
'A6 authentic attestation not compared on all approved build inputs',
'A7 separately switches executable/schema causing inconsistent serving pair',
'A8 success ACK precedes authoritative activation CAS; failed CAS already ACKed',
'A9 root snapshot/tombstone race deletes artifact already referenced by activation',
'A10 rollback pin expires by creation time rather than latest deactivation'])
(ROOT/'cases.json').write_text(json.dumps(CASES,indent=2)+'\n')
print('Frozen cases:',[(c['id'],len(c['input']),len(c['oracle'])) for c in CASES])
