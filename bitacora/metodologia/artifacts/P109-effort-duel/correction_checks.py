"""Post-hoc counterexamples; do not change the pre-call root denominator."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# Keeping old epoch-key dedup alone is insufficient after dropping transfer rows.
old_epoch_keys={(7,'x')};new_key=(8,'x');source_rights=90
retry_is_new=new_key not in old_epoch_keys
if retry_is_new:source_rights-=10
retention={'old_dedup_retained':True,'transfer_row_deleted':True,'retry_new_epoch_key':new_key,'source_rights_after_retry':source_rights,'destination_credit_reapplied':False,'unsafe':retry_is_new and source_rights==80}
# Winning the local CAS does not authorize a delayed remote command forever.
db_epoch=10;worker_epoch=10
assert db_epoch==10;db_epoch=11  # coordinator 11 commits before dispatch, then pauses
assert db_epoch==11;db_epoch=12;worker_epoch=12  # coordinator 12 commits and applies
worker_epoch=11  # delayed older command; different idempotency key, no remote fence
fence={'db_epoch':db_epoch,'worker_epoch':worker_epoch,'unsafe_despite_cas_before_dispatch':worker_epoch<db_epoch,'why':'Distinct epoch-bearing idempotency keys prevent duplicate same-command effects, not application of an older command after a newer one. Eventual reconciliation does not prevent the forbidden regression.'}
# The cheapest-first rule DOES maximize cardinality under supplied assumptions.
proof='For nonnegative independent costs, the k cheapest items have no greater total cost than any other k-item subset. A cost-sorted greedy scan accepts the longest feasible cheapest prefix (including every zero-cost item); no later cheaper item exists after the first nonfitting item. Thus any larger feasible subset would contradict the minimal-prefix cost. Its secondary net and tertiary ID objectives can still fail.'
assert retention['unsafe'] and fence['unsafe_despite_cas_before_dispatch']
result={'retained_epoch_dedup_alternative':retention,'remote_epoch_fencing':fence,'cheapest_first_cardinality':{'always_maximum_under_dossier':True,'proof':proof},'scope':'Post-hoc correction/extra checks, separate from 31 frozen roots; no production integration.'}
(ROOT/'correction-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Post-hoc retention/fencing counterexamples verified; cardinality proof recorded.')
