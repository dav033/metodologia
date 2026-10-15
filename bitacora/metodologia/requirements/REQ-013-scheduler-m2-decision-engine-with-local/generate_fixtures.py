"""Generate the frozen, synthetic M2 choice corpus before its first Laya inference."""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[4] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import bt_agents  # noqa: E402
import bt_profiles  # noqa: E402
import bt_subscriptions  # noqa: E402
import bt_agy  # noqa: E402
from bt_scheduler_decision import account_reference, candidate_route_id, sha256_json  # noqa: E402

HERE = Path(__file__).resolve().parent
CORPUS_PATH = HERE / "fixtures-v1.json"
MANIFEST_PATH = HERE / "fixture-manifest-v1.json"
DATASET_VERSION = "scheduler-m2-synthetic-choice-v1"
DATASET_SEED = 20261014
FAMILIES = ("quota_capacity", "risk_effort", "history", "resource_dependency", "ambiguous_tradeoff")
FEATURES = ("quality_fit", "quota_headroom", "latency_fit", "verified_record", "risk_fit", "resource_fit",
            "effort_fit")
BASE_WEIGHTS = {
    "quota_capacity": {"quality_fit": .16, "quota_headroom": .32, "latency_fit": .16,
                       "verified_record": .14, "risk_fit": .08, "resource_fit": .06, "effort_fit": .08},
    "risk_effort": {"quality_fit": .16, "quota_headroom": .04, "latency_fit": .06,
                    "verified_record": .12, "risk_fit": .32, "resource_fit": .06, "effort_fit": .24},
    "history": {"quality_fit": .16, "quota_headroom": .10, "latency_fit": .10,
                "verified_record": .38, "risk_fit": .10, "resource_fit": .06, "effort_fit": .10},
    "resource_dependency": {"quality_fit": .16, "quota_headroom": .08, "latency_fit": .06,
                             "verified_record": .12, "risk_fit": .08, "resource_fit": .36, "effort_fit": .14},
}
TASK_TEMPLATES = {
    "en": (
        "Select a route for {object}: preserve subscription headroom while still finishing the requested change.",
        "Select a route for {object}: the change has elevated impact and needs adequate model effort.",
        "Select a route for {object}: prioritize routes with independently verified prior outcomes.",
        "Select a route for {object}: the change spans shared resources and has dependent work.",
        "Select a route for {object}: balance the stated quality, quota, speed, risk, resource and effort priorities.",
    ),
    "es": (
        "Elige una ruta para {object}: conserva margen de suscripción y termina el cambio solicitado.",
        "Elige una ruta para {object}: el cambio tiene impacto alto y requiere esfuerzo suficiente del modelo.",
        "Elige una ruta para {object}: prioriza resultados previos verificados de forma independiente.",
        "Elige una ruta para {object}: el cambio abarca recursos compartidos y trabajo dependiente.",
        "Elige una ruta para {object}: equilibra las prioridades indicadas de calidad, cuota, velocidad, riesgo, recursos y esfuerzo.",
    ),
}
OBJECTS = ("the scheduler adapter", "the task approval flow", "the quota reader", "the profile resolver",
           "the recovery policy", "the verifier boundary", "the local worker", "the dependency planner",
           "the audit ledger", "the route selector", "el adaptador del planificador", "el flujo de aprobaciones",
           "el lector de cuotas", "el resolvedor de perfiles", "la política de recuperación", "el límite del verificador",
           "el worker local", "el planificador de dependencias", "el registro de auditoría", "el selector de rutas")
PROFILE_SPECS = {
    "claude-a": {"provider": "claude", "bin": "claude", "env": {"CLAUDE_CONFIG_DIR": "/fixture/claude-a"},
                 "work_only": False},
    "claude-b": {"provider": "claude", "bin": "claude", "env": {"CLAUDE_CONFIG_DIR": "/fixture/claude-b"},
                 "work_only": False},
    "codex-a": {"provider": "codex", "bin": "codex", "env": {"CODEX_HOME": "/fixture/codex-a"},
                "work_only": False},
    "codex-b": {"provider": "codex", "bin": "codex", "env": {"CODEX_HOME": "/fixture/codex-b"},
                "work_only": False},
    "antigravity": {"provider": "antigravity", "bin": "agy", "env": {}, "work_only": False},
}
POOL = tuple(PROFILE_SPECS)


class Rates(dict):
    def __init__(self, *args, samples=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.samples = samples or {}


def _quota_row(now: float, used_percent: float) -> dict:
    return {"status": "ok", "observed_at": now - 30, "windows": {
        "five_hour": {"used_percent": used_percent, "resets_at": now + 3600, "window_minutes": 300},
        "seven_day": {"used_percent": min(99.0, used_percent + 3), "resets_at": now + 86_400,
                       "window_minutes": 10080},
        "seven_day_sonnet": {"used_percent": min(99.0, used_percent + 5), "resets_at": now + 86_400,
                             "window_minutes": 10080},
        "seven_day_opus": {"used_percent": min(99.0, used_percent + 7), "resets_at": now + 86_400,
                           "window_minutes": 10080},
    }}


def _priority_weights(family: str, rng: random.Random) -> dict[str, float]:
    if family != "ambiguous_tradeoff":
        return BASE_WEIGHTS[family]
    raw = {feature: rng.uniform(.2, 1.0) for feature in FEATURES}
    total = sum(raw.values())
    return {feature: round(value / total, 4) for feature, value in raw.items()}


def _router_routes(tier: int, now: float, usage: dict, rates: Rates, loads: dict):
    profiles = {key: dict(value) for key, value in PROFILE_SPECS.items()}
    with patch.object(bt_profiles, "load", return_value=profiles), \
            patch.object(bt_profiles, "is_work_project", return_value=True), \
            patch.object(bt_agents, "_stats", return_value=(rates, loads)), \
            patch.object(bt_agents, "cooling_until", return_value=None), \
            patch.object(bt_subscriptions, "load", return_value=usage), \
            patch.object(bt_agy, "capacity", return_value=(usage["antigravity"]["pressure"], None)):
        # Only the existing deterministic router decides the baseline rank; no credential or provider inference runs.
        routes, _ = bt_agents.candidates("fixture-work", list(POOL), tier, "implement")
    return routes


def _make_case(split: str, family: str, number: int, language: str, rng: random.Random,
               now: float) -> dict:
    family_index = FAMILIES.index(family)
    tier = 2 if family == "risk_effort" else 1 if family in {"history", "resource_dependency"} else \
        rng.randrange(3) if family == "ambiguous_tradeoff" else rng.choice((0, 1))
    features_by_profile = {}
    rates_data: dict[tuple[str, str, str], float] = {}
    sample_data: dict[tuple[str, str, str], int] = {}
    usage_rows, loads = {}, {}
    for index, (profile, spec) in enumerate(PROFILE_SPECS.items()):
        provider = spec["provider"]
        model, effort = bt_agents.model_for(provider, tier)
        key = bt_agents.account_key(profile, provider)
        used = round(rng.uniform(8, 92), 1)
        usage_rows[key] = _quota_row(now, used)
        loads[key] = round(rng.uniform(0, 18) * 60)
        if provider == "antigravity":
            usage_rows[profile] = {"pressure": used}
        rate_key = (provider, model, "implement")
        rates_data.setdefault(rate_key, round(rng.uniform(.52, .99), 3))
        sample_data.setdefault(rate_key, rng.choice((0, 2, 4, 5, 8, 16, 32)))
        effort_rank = {"low": 0, "medium": 1, "high": 2, "xhigh": 2, "max": 2}.get(
            effort, bt_agents.rank_of(model))
        features_by_profile[profile] = {
            "quality_fit": round(rng.uniform(.35, 1.0), 3),
            "quota_headroom": round((100 - used) / 100, 3),
            "latency_fit": round(rng.uniform(.2, 1.0), 3),
            "verified_record": rates_data[rate_key],
            "risk_fit": round(rng.uniform(.25, 1.0), 3),
            "resource_fit": round(rng.uniform(.15, 1.0), 3),
            "effort_fit": round(max(.1, 1.0 - abs(effort_rank - tier) * .35), 3),
            "load_minutes": round(loads[key] / 60, 1),
            "history_samples": sample_data[rate_key],
            "quota_used_percent": used,
        }
    routes = _router_routes(tier, now, usage_rows, Rates(rates_data, samples=sample_data), loads)
    route_by_profile = {route["profile"]: route for route in routes}
    options = []
    weights = _priority_weights(family, rng)
    for route in routes:
        profile = route["profile"]
        features = features_by_profile[profile]
        route_id = candidate_route_id(route["agent"], route["model"], profile, route["effort"])
        utility = sum(weights[feature] * features[feature] for feature in FEATURES)
        options.append({
            "route_id": route_id,
            "provider": route["agent"],
            "model": route["model"],
            "profile": profile,
            "effort": route["effort"],
            "baseline_rank": next(index for index, item in enumerate(routes) if item["profile"] == profile),
            "eligible": True,
            "features": {key: features[key] for key in FEATURES},
            "observed_context": {key: features[key] for key in
                                  ("load_minutes", "history_samples", "quota_used_percent")},
            "oracle_utility": round(utility, 8),
        })
    by_route = {item["route_id"]: item for item in options}
    deterministic = min(options, key=lambda item: (item["baseline_rank"], item["route_id"]))
    oracle = min(options, key=lambda item: (-item["oracle_utility"], item["route_id"]))
    prompt_order = list(options)
    rng.shuffle(prompt_order)
    task_object = rng.choice(OBJECTS)
    task_text = TASK_TEMPLATES[language][family_index].format(object=task_object)
    # Include independent task-specific priorities so the selected label is a reproducible utility optimum.
    preference = ", ".join(f"{feature}={weights[feature]:.4f}" for feature in FEATURES)
    if language == "es":
        task_text += f" Prioridades rubricadas (peso): {preference}."
    else:
        task_text += f" Rubric priorities (weight): {preference}."
    task_classifications = {
        "complexity": ("high" if tier == 2 else "medium" if tier == 1 else "low"),
        "scope": "large_change" if family in {"risk_effort", "resource_dependency"} else "small_change",
        "estimated_minutes": rng.choice((15, 30, 60, 120, 240)),
        "risk": "high" if family == "risk_effort" else "medium" if family == "resource_dependency" else "low",
        "coupling": "high" if family == "resource_dependency" else "medium" if family == "ambiguous_tradeoff" else "low",
        "confidence": "high",
    }
    task_digest = sha256_json({"brief": task_text, "classifications": task_classifications,
                               "priority_weights": weights,
                               "options": {key: value["features"] for key, value in sorted(by_route.items())}})
    case_id = f"{split}-{family}-{number:03d}-{language}"
    # These excluded records are absent from the model prompt, as required by the production hard-filter boundary.
    excluded = [{"route_id": "e" * 64, "provider": "claude", "model": "sonnet", "profile": "blocked-quota",
                 "quota_status": "unknown", "eligible": False, "reason": "quota_unknown"},
                {"route_id": "f" * 64, "provider": "codex", "model": "sol", "profile": "denied-profile",
                 "quota_status": "available", "eligible": False, "reason": "profile_not_authorized"}]
    return {
        "case_id": case_id,
        "split": split,
        "family": family,
        "language": language,
        "task_sha256": task_digest,
        "task": task_text,
        "classifications": task_classifications,
        "priority_weights": weights,
        "tier": tier,
        "options": [{key: value for key, value in item.items() if key != "oracle_utility"}
                    for item in prompt_order],
        "eligible_route_ids": sorted(by_route),
        "excluded_candidates": excluded,
        "deterministic_route_id": deterministic["route_id"],
        "oracle_route_id": oracle["route_id"],
        "oracle_utilities": {item["route_id"]: item["oracle_utility"] for item in options},
    }


def generate() -> tuple[dict, dict]:
    rng = random.Random(DATASET_SEED)
    now = time.time()
    cases = []
    for split, base_number in (("calibration", 0), ("held_out", 100)):
        for family in FAMILIES:
            for within in range(20):
                language = "en" if within % 2 == 0 else "es"
                cases.append(_make_case(split, family, base_number + within, language, rng, now))
    cases.sort(key=lambda item: item["case_id"])
    corpus = {
        "dataset_version": DATASET_VERSION,
        "generator_seed": DATASET_SEED,
        "label_protocol": "synthetic utility oracle v1: sum(normalized, predeclared task priority weights * independently generated route attributes); maximum utility wins; stable route SHA-256 breaks ties; no Laya output and no baseline rank enter the label",
        "baseline_protocol": "route order returned by existing bt_agents.candidates for synthetic fixture-backed profiles, quota and telemetry at the case's bt_agents tier/kind",
        "cases": cases,
    }
    canonical = json.dumps(corpus, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    corpus_bytes = (json.dumps(corpus, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    case_ids = [item["case_id"] for item in cases]
    task_digests = [item["task_sha256"] for item in cases]
    calibration = [item["case_id"] for item in cases if item["split"] == "calibration"]
    held_out = [item["case_id"] for item in cases if item["split"] == "held_out"]
    if len(case_ids) != len(set(case_ids)) or len(task_digests) != len(set(task_digests)):
        raise RuntimeError("fixture ids or canonical task digests are not unique")
    if set(calibration) & set(held_out) or len(calibration) != 100 or len(held_out) != 100:
        raise RuntimeError("fixture splits do not satisfy their frozen sample sizes")
    manifest = {
        "dataset_version": DATASET_VERSION,
        "dataset_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "canonical_dataset_sha256": hashlib.sha256(canonical).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "frozen_before_first_laya_call": True,
        "label_protocol": corpus["label_protocol"],
        "labeler_independence": "algorithmic synthetic oracle; labels depend only on frozen feature and priority-weight data, not Laya, bt_agents baseline order, a hosted model or attempt outcomes; not human or production-outcome labels",
        "calibration_case_ids": calibration,
        "held_out_case_ids": held_out,
        "family_minimum_counts_per_split": {split: {family: 20 for family in FAMILIES}
                                             for split in ("calibration", "held_out")},
        "languages_per_split": {split: {language: 50 for language in ("en", "es")}
                                for split in ("calibration", "held_out")},
        "distinct_task_sha256_count": len(set(task_digests)),
        "duplicate_canonical_task_digests_across_splits": 0,
        "cases": len(cases),
        "outcome_label_source": "synthetic oracle, not observed task success",
        "corpus_format": "UTF-8 JSON, sorted keys, two-space indentation, final newline",
    }
    return corpus_bytes, manifest


def main() -> int:
    if CORPUS_PATH.exists() or MANIFEST_PATH.exists():
        raise SystemExit("refusing to overwrite an existing frozen fixture or manifest")
    corpus_bytes, manifest = generate()
    CORPUS_PATH.write_bytes(corpus_bytes)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    print(json.dumps({"dataset_version": DATASET_VERSION, "dataset_sha256": manifest["dataset_sha256"],
                      "cases": manifest["cases"], "frozen_before_first_laya_call": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
