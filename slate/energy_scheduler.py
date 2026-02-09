#!/usr/bin/env python3
# Modified: 2026-02-09T12:39:00-05:00 | Author: Gemini (Antigravity)
# Change: Create SLATE energy-aware scheduling engine
# NOTE: All AIs modifying this file must add a dated comment.
"""
SLATE Energy-Aware Scheduler
=============================

Integrates with the user's electrical provider billing schedule to
automatically shift heavy compute operations to off-peak hours when
electricity is cheapest.

Operation Classification:
  HEAVY:  Nightly CI, model training, batch inference, Docker builds,
          benchmark runs, large spec-kit analysis
  NORMAL: Interactive inference, code analysis, PR review, live coding
  LIGHT:  Git sync, status checks, documentation, notifications

The scheduler respects user choice: if energy config is disabled or
not configured, all operations run immediately (no scheduling).

Usage:
    from slate.energy_scheduler import EnergyScheduler

    scheduler = EnergyScheduler()
    decision = scheduler.should_execute("nightly_ci")
    if decision.execute_now:
        run_ci()
    else:
        print(f"Deferred to {decision.next_window}: {decision.reason}")

CLI:
    python slate/energy_scheduler.py --status
    python slate/energy_scheduler.py --schedule
    python slate/energy_scheduler.py --cost
    python slate/energy_scheduler.py --providers --zip 19103
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# ──────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(os.environ.get("SLATE_WORKSPACE", Path(__file__).parent.parent))
ENERGY_CONFIG_PATH = WORKSPACE_ROOT / ".slate_config" / "energy.yaml"
QUEUE_PATH = WORKSPACE_ROOT / ".slate_analytics" / "energy_queue.json"

# ──────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────

class RateTier(Enum):
    """Electricity rate tiers."""
    SUPER_OFF_PEAK = "super_off_peak"
    OFF_PEAK = "off_peak"
    PEAK = "peak"


class OperationWeight(Enum):
    """Operation weight classification."""
    HEAVY = "heavy"
    NORMAL = "normal"
    LIGHT = "light"


@dataclass
class ScheduleDecision:
    """Result of a scheduling decision."""
    execute_now: bool
    reason: str
    operation: str
    operation_weight: str
    current_tier: str
    cost_per_kwh: float
    next_window: Optional[str] = None     # ISO datetime of next allowed window
    cost_estimate_usd: float = 0.0        # Estimated cost for this operation
    savings_if_deferred: float = 0.0      # USD saved by deferring


@dataclass
class MonthlyCostEstimate:
    """Monthly cost projection."""
    actual_cost_usd: float = 0.0
    projected_cost_usd: float = 0.0
    unscheduled_cost_usd: float = 0.0
    savings_usd: float = 0.0
    savings_percent: float = 0.0
    budget_limit_usd: float = 0.0
    budget_used_percent: float = 0.0
    days_in_period: int = 0
    days_elapsed: int = 0


@dataclass
class QueuedOperation:
    """An operation queued for a future rate window."""
    operation: str
    weight: str
    queued_at: str                        # ISO datetime
    target_window: str                    # Rate tier to wait for
    target_time: str                      # Estimated execution time
    context: str = ""
    callback: str = ""                    # Module.function to call


@dataclass
class RateSchedule:
    """A provider's rate schedule."""
    provider_name: str
    plan_name: str
    rates: Dict[str, Dict[str, Any]]     # tier -> {hours: [...], cost_per_kwh: float}


# ──────────────────────────────────────────────────────────
# Operation Classification
# ──────────────────────────────────────────────────────────

# Keywords that map operations to weight classes
HEAVY_KEYWORDS = [
    "ci", "build", "docker", "train", "fine-tune", "finetune",
    "batch", "benchmark", "nightly", "deploy", "large", "bulk",
    "model_training", "spec_kit_batch", "runner_build",
]

NORMAL_KEYWORDS = [
    "inference", "analyze", "review", "code", "chat", "assist",
    "copilot", "interactive", "pr_review", "code_analysis",
]

LIGHT_KEYWORDS = [
    "sync", "status", "check", "notification", "doc", "log",
    "git", "health", "ping", "webhook",
]


def classify_operation(operation: str) -> OperationWeight:
    """
    Classify an operation as heavy, normal, or light.

    Uses keyword matching against the operation name.
    Unknown operations default to NORMAL.
    """
    op_lower = operation.lower().replace("-", "_").replace(" ", "_")

    for kw in HEAVY_KEYWORDS:
        if kw in op_lower:
            return OperationWeight.HEAVY

    for kw in LIGHT_KEYWORDS:
        if kw in op_lower:
            return OperationWeight.LIGHT

    for kw in NORMAL_KEYWORDS:
        if kw in op_lower:
            return OperationWeight.NORMAL

    return OperationWeight.NORMAL


# ──────────────────────────────────────────────────────────
# Energy Provider Database
# ──────────────────────────────────────────────────────────

class EnergyProviderDatabase:
    """
    Database of US electrical providers and their rate schedules.

    Initially covers major metro providers. Community can contribute
    additional providers via SLATE Discussions.
    """

    # Provider database — initial US metro coverage
    PROVIDERS: Dict[str, Dict[str, Any]] = {
        "PECO Energy": {
            "region": "Philadelphia, PA",
            "zip_prefixes": ["190", "191", "193", "194"],
            "plans": {
                "Time-of-Use (TOU)": {
                    "super_off_peak": {"hours": [0,1,2,3,4,5], "cost_per_kwh": 0.04},
                    "off_peak": {"hours": [6,7,8,9,10,11,12,13,19,20,21,22,23], "cost_per_kwh": 0.08},
                    "peak": {"hours": [14,15,16,17,18], "cost_per_kwh": 0.22},
                },
                "Flat Rate": {
                    "off_peak": {"hours": list(range(24)), "cost_per_kwh": 0.11},
                },
            },
        },
        "ComEd": {
            "region": "Chicago, IL",
            "zip_prefixes": ["600", "601", "602", "603", "604", "605", "606"],
            "plans": {
                "Time-of-Use (TOU)": {
                    "super_off_peak": {"hours": [0,1,2,3,4,5], "cost_per_kwh": 0.03},
                    "off_peak": {"hours": [6,7,8,9,10,11,12,13,20,21,22,23], "cost_per_kwh": 0.07},
                    "peak": {"hours": [14,15,16,17,18,19], "cost_per_kwh": 0.19},
                },
            },
        },
        "PG&E": {
            "region": "Northern California",
            "zip_prefixes": ["940", "941", "942", "943", "944", "945", "946", "947", "948", "949", "950", "951"],
            "plans": {
                "Time-of-Use (E-TOU-C)": {
                    "super_off_peak": {"hours": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14], "cost_per_kwh": 0.30},
                    "peak": {"hours": [16,17,18,19,20], "cost_per_kwh": 0.49},
                    "off_peak": {"hours": [15,21,22,23], "cost_per_kwh": 0.35},
                },
            },
        },
        "Con Edison": {
            "region": "New York, NY",
            "zip_prefixes": ["100", "101", "102", "103", "104"],
            "plans": {
                "Time-of-Use": {
                    "super_off_peak": {"hours": [0,1,2,3,4,5,6,7], "cost_per_kwh": 0.05},
                    "off_peak": {"hours": [8,9,10,11,12,13,14,15,20,21,22,23], "cost_per_kwh": 0.12},
                    "peak": {"hours": [16,17,18,19], "cost_per_kwh": 0.30},
                },
            },
        },
        "Duke Energy": {
            "region": "Southeast US (NC, SC, FL, IN, OH, KY)",
            "zip_prefixes": ["270", "271", "272", "273", "274", "275", "276", "277", "278", "279",
                            "290", "291", "292", "293", "294", "295", "296",
                            "320", "321", "322", "323", "324", "325", "326", "327", "328", "329",
                            "330", "331", "332", "334", "335", "336", "337", "338", "339",
                            "460", "461", "462"],
            "plans": {
                "Time-of-Use": {
                    "off_peak": {"hours": [0,1,2,3,4,5,6,7,8,9,10,11,12,21,22,23], "cost_per_kwh": 0.06},
                    "peak": {"hours": [13,14,15,16,17,18,19,20], "cost_per_kwh": 0.18},
                },
            },
        },
        "Xcel Energy": {
            "region": "Colorado/Minnesota",
            "zip_prefixes": ["800", "801", "802", "803", "804", "805", "806",
                            "550", "551", "553", "554", "555", "556", "557", "558", "559", "560", "561", "562"],
            "plans": {
                "Time-of-Use": {
                    "off_peak": {"hours": [0,1,2,3,4,5,6,7,8,9,18,19,20,21,22,23], "cost_per_kwh": 0.07},
                    "peak": {"hours": [10,11,12,13,14,15,16,17], "cost_per_kwh": 0.16},
                },
            },
        },
        "SCE": {
            "region": "Southern California",
            "zip_prefixes": ["900", "901", "902", "903", "904", "905", "906", "907", "908", "910",
                            "911", "912", "913", "914", "915", "916", "917", "918"],
            "plans": {
                "TOU-D-PRIME": {
                    "super_off_peak": {"hours": [0,1,2,3,4,5,6,7], "cost_per_kwh": 0.15},
                    "off_peak": {"hours": [8,9,10,11,12,13,14,15,21,22,23], "cost_per_kwh": 0.25},
                    "peak": {"hours": [16,17,18,19,20], "cost_per_kwh": 0.45},
                },
            },
        },
        "Dominion Energy": {
            "region": "Virginia",
            "zip_prefixes": ["220", "221", "222", "223", "224", "225", "226", "227", "228", "229",
                            "230", "231", "232", "233", "234", "235", "236", "237", "238", "239",
                            "240", "241", "242", "243", "244", "245", "246"],
            "plans": {
                "Schedule 1G (TOU)": {
                    "off_peak": {"hours": [0,1,2,3,4,5,6,7,8,9,10,11,12,21,22,23], "cost_per_kwh": 0.06},
                    "peak": {"hours": [13,14,15,16,17,18,19,20], "cost_per_kwh": 0.15},
                },
            },
        },
        "AEP": {
            "region": "Ohio/Texas",
            "zip_prefixes": ["430", "431", "432", "433", "434", "435", "436", "437", "438", "439",
                            "440", "441", "442", "443", "444", "445", "446", "447", "448", "449",
                            "750", "751", "752", "753", "754", "755", "756", "757", "758", "759"],
            "plans": {
                "Time-of-Use": {
                    "off_peak": {"hours": [0,1,2,3,4,5,6,7,8,9,10,11,21,22,23], "cost_per_kwh": 0.05},
                    "peak": {"hours": [12,13,14,15,16,17,18,19,20], "cost_per_kwh": 0.14},
                },
            },
        },
        "Entergy": {
            "region": "Gulf States (LA, MS, AR, TX)",
            "zip_prefixes": ["700", "701", "710", "711", "712", "713", "714",
                            "386", "387", "388", "389", "390", "391", "392", "393", "394", "395", "396", "397",
                            "716", "717", "718", "719", "720", "721", "722", "723"],
            "plans": {
                "Flat Rate": {
                    "off_peak": {"hours": list(range(24)), "cost_per_kwh": 0.09},
                },
            },
        },
    }

    @classmethod
    def lookup_by_zip(cls, zip_code: str) -> List[Dict[str, Any]]:
        """Find providers serving a ZIP code."""
        results = []
        prefix = zip_code[:3]
        for name, data in cls.PROVIDERS.items():
            if prefix in data.get("zip_prefixes", []):
                plans = list(data.get("plans", {}).keys())
                results.append({
                    "name": name,
                    "region": data["region"],
                    "plans": plans,
                    "default_plan": plans[0] if plans else None,
                })
        return results

    @classmethod
    def get_rate_schedule(cls, provider: str, plan: str = None) -> Optional[RateSchedule]:
        """Get rate tiers for a specific provider/plan."""
        provider_data = cls.PROVIDERS.get(provider)
        if not provider_data:
            return None

        plans = provider_data.get("plans", {})
        if plan is None:
            plan = list(plans.keys())[0] if plans else None
        if plan not in plans:
            return None

        return RateSchedule(
            provider_name=provider,
            plan_name=plan,
            rates=plans[plan],
        )

    @classmethod
    def list_all_providers(cls) -> List[Dict[str, str]]:
        """List all available providers."""
        return [
            {"name": name, "region": data["region"],
             "plans": list(data.get("plans", {}).keys())}
            for name, data in cls.PROVIDERS.items()
        ]


# ──────────────────────────────────────────────────────────
# Energy Scheduler
# ──────────────────────────────────────────────────────────

class EnergyScheduler:
    """
    Energy-aware task scheduling engine.

    Classifies every SLATE operation into heavy/normal/light,
    checks the current rate tier, and either:
    - Executes immediately (if allowed in current tier)
    - Queues for the next allowed window
    - Warns the user about cost implications
    """

    def __init__(self, config_path: Path = ENERGY_CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()
        self._queue: List[QueuedOperation] = []
        self._load_queue()

    def _load_config(self) -> Dict[str, Any]:
        """Load energy.yaml configuration."""
        if not self.config_path.exists():
            return {"energy": {"enabled": False}}

        try:
            import yaml
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {"energy": {"enabled": False}}
        except ImportError:
            # Minimal fallback parser
            try:
                text = self.config_path.read_text(encoding="utf-8")
                if "enabled: true" in text:
                    return {"energy": {"enabled": True}}
            except Exception:
                pass
            return {"energy": {"enabled": False}}
        except Exception:
            return {"energy": {"enabled": False}}

    @property
    def enabled(self) -> bool:
        """Whether energy scheduling is active."""
        return self.config.get("energy", {}).get("enabled", False)

    # ──── Rate Tier ────

    def current_rate_tier(self) -> Tuple[str, float]:
        """
        Returns (tier_name, cost_per_kwh) based on current local time.

        If energy config is disabled, returns ("off_peak", 0.10) as default.
        """
        if not self.enabled:
            return ("off_peak", 0.10)

        energy = self.config.get("energy", {})
        rates = energy.get("provider", {}).get("rates", {})
        hour = datetime.now().hour

        for tier_name, tier_data in rates.items():
            if isinstance(tier_data, dict) and hour in tier_data.get("hours", []):
                return (tier_name, tier_data.get("cost_per_kwh", 0.10))

        return ("off_peak", 0.10)

    # ──── Scheduling Decision ────

    def should_execute(self, operation: str, duration_estimate_ms: int = 30000) -> ScheduleDecision:
        """
        Determine whether an operation should execute now or be deferred.

        Returns a ScheduleDecision with execute_now, reason, and cost data.
        """
        weight = classify_operation(operation)
        current_tier, current_cost = self.current_rate_tier()

        # If scheduling is disabled, always execute
        if not self.enabled:
            return ScheduleDecision(
                execute_now=True,
                reason="Energy scheduling disabled — executing immediately",
                operation=operation,
                operation_weight=weight.value,
                current_tier=current_tier,
                cost_per_kwh=current_cost,
            )

        # Check schedule policy for this weight class
        energy = self.config.get("energy", {})
        schedule = energy.get("schedule", {})
        weight_key = f"{weight.value}_operations"
        policy = schedule.get(weight_key, {})

        allowed_tiers = policy.get("allowed", ["super_off_peak", "off_peak", "peak"])
        forbidden_tiers = policy.get("forbidden", [])

        # Check if current tier is allowed
        tier_allowed = current_tier in allowed_tiers and current_tier not in forbidden_tiers

        # Estimate cost
        power_draw = energy.get("power_draw", {})
        watts_key = "dual_gpu_inference" if weight == OperationWeight.HEAVY else "single_gpu_inference"
        watts = power_draw.get(watts_key, 250)
        hours = (duration_estimate_ms / 1000) / 3600
        kwh = (watts / 1000) * hours
        cost_now = kwh * current_cost

        if tier_allowed:
            return ScheduleDecision(
                execute_now=True,
                reason=f"Current tier '{current_tier}' is allowed for {weight.value} ops",
                operation=operation,
                operation_weight=weight.value,
                current_tier=current_tier,
                cost_per_kwh=current_cost,
                cost_estimate_usd=round(cost_now, 6),
            )
        else:
            # Find next allowed window
            next_window, next_cost = self._find_next_window(allowed_tiers)

            cost_deferred = kwh * next_cost
            savings = cost_now - cost_deferred

            return ScheduleDecision(
                execute_now=False,
                reason=(f"Current tier '{current_tier}' (${current_cost}/kWh) is forbidden "
                        f"for {weight.value} ops. Next allowed: '{allowed_tiers[0]}' at {next_window}"),
                operation=operation,
                operation_weight=weight.value,
                current_tier=current_tier,
                cost_per_kwh=current_cost,
                next_window=next_window,
                cost_estimate_usd=round(cost_deferred, 6),
                savings_if_deferred=round(savings, 6),
            )

    def _find_next_window(self, target_tiers: List[str]) -> Tuple[str, float]:
        """Find the next time one of the target rate tiers is active."""
        energy = self.config.get("energy", {})
        rates = energy.get("provider", {}).get("rates", {})

        now = datetime.now()
        current_hour = now.hour

        # Search up to 24 hours ahead
        for offset in range(1, 25):
            check_hour = (current_hour + offset) % 24
            for tier_name in target_tiers:
                tier_data = rates.get(tier_name, {})
                if isinstance(tier_data, dict) and check_hour in tier_data.get("hours", []):
                    next_time = now + timedelta(hours=offset)
                    next_time = next_time.replace(minute=0, second=0, microsecond=0)
                    cost = tier_data.get("cost_per_kwh", 0.10)
                    return (next_time.isoformat(), cost)

        # Fallback
        return ((now + timedelta(hours=6)).isoformat(), 0.10)

    # ──── Queue ────

    def queue_for_window(self, operation: str, target_tier: str = "super_off_peak",
                          context: str = "", callback: str = ""):
        """Queue an operation for the next matching rate window."""
        target_time, _ = self._find_next_window([target_tier])

        entry = QueuedOperation(
            operation=operation,
            weight=classify_operation(operation).value,
            queued_at=datetime.now(timezone.utc).isoformat(),
            target_window=target_tier,
            target_time=target_time,
            context=context,
            callback=callback,
        )
        self._queue.append(entry)
        self._save_queue()
        return entry

    def get_queue(self) -> List[Dict[str, Any]]:
        """Get all queued operations."""
        return [asdict(q) for q in self._queue]

    def clear_queue(self):
        """Clear the operation queue."""
        self._queue.clear()
        self._save_queue()

    def _load_queue(self):
        """Load queued operations from disk."""
        if QUEUE_PATH.exists():
            try:
                data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
                self._queue = [QueuedOperation(**d) for d in data]
            except Exception:
                self._queue = []

    def _save_queue(self):
        """Save queued operations to disk."""
        QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = [asdict(q) for q in self._queue]
            QUEUE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[EnergyScheduler] Queue save error: {e}", file=sys.stderr)

    # ──── Cost Estimation ────

    def estimate_monthly_cost(self) -> MonthlyCostEstimate:
        """
        Estimate monthly cost based on historical token ledger data.

        Compares actual (scheduled) vs hypothetical (unscheduled) cost.
        """
        energy = self.config.get("energy", {})
        budget = energy.get("budget", {})
        monthly_limit = budget.get("monthly_limit_usd", 25.0)

        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        days_elapsed = (now - month_start).days + 1
        days_in_month = 30  # Approximation

        # Try to read actual cost from token ledger
        ledger_path = WORKSPACE_ROOT / ".slate_analytics" / "token_ledger.jsonl"
        actual_cost = 0.0
        unscheduled_cost = 0.0

        if ledger_path.exists():
            try:
                month_prefix = now.strftime("%Y-%m")
                with open(ledger_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            d = json.loads(line)
                            if d.get("ts", "").startswith(month_prefix):
                                actual_cost += d.get("cost_usd", 0)
                                # Estimate unscheduled: assume all at average rate
                                dur_ms = d.get("dur_ms", 0)
                                hours = (dur_ms / 1000) / 3600
                                kwh = 0.25 * hours  # 250W
                                unscheduled_cost += kwh * 0.15  # Average rate
                        except Exception:
                            continue
            except Exception:
                pass

        # Project cost for full month
        if days_elapsed > 0:
            daily_rate = actual_cost / days_elapsed
            projected = daily_rate * days_in_month
        else:
            projected = 0.0

        savings = unscheduled_cost - actual_cost
        budget_used = (actual_cost / monthly_limit * 100) if monthly_limit > 0 else 0

        return MonthlyCostEstimate(
            actual_cost_usd=round(actual_cost, 4),
            projected_cost_usd=round(projected, 4),
            unscheduled_cost_usd=round(unscheduled_cost, 4),
            savings_usd=round(max(0, savings), 4),
            savings_percent=round((savings / max(unscheduled_cost, 0.01)) * 100, 1),
            budget_limit_usd=monthly_limit,
            budget_used_percent=round(budget_used, 1),
            days_in_period=days_in_month,
            days_elapsed=days_elapsed,
        )

    def check_budget(self) -> Dict[str, Any]:
        """Check current budget status."""
        estimate = self.estimate_monthly_cost()
        energy = self.config.get("energy", {})
        budget_config = energy.get("budget", {})
        alert_pct = budget_config.get("alert_at_percent", 80)
        hard_cap = budget_config.get("hard_cap", False)

        return {
            "cost_this_month": estimate.actual_cost_usd,
            "budget_limit": estimate.budget_limit_usd,
            "budget_used_percent": estimate.budget_used_percent,
            "projected_end_of_month": estimate.projected_cost_usd,
            "alert_triggered": estimate.budget_used_percent >= alert_pct,
            "hard_cap_active": hard_cap and estimate.budget_used_percent >= 100,
            "savings_this_month": estimate.savings_usd,
        }


# ──────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────

def main():
    """CLI: slate energy [--status|--schedule|--cost|--providers]"""
    import argparse
    parser = argparse.ArgumentParser(description="SLATE Energy-Aware Scheduler")
    parser.add_argument("--status", action="store_true", help="Current rate tier and schedule")
    parser.add_argument("--schedule", action="store_true", help="Today's full schedule")
    parser.add_argument("--cost", action="store_true", help="Monthly cost estimate")
    parser.add_argument("--queue", action="store_true", help="Show queued operations")
    parser.add_argument("--providers", action="store_true", help="List available providers")
    parser.add_argument("--zip", type=str, help="ZIP code for provider lookup")
    parser.add_argument("--check", type=str, help="Check scheduling for an operation")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()
    scheduler = EnergyScheduler()

    if args.status:
        tier, cost = scheduler.current_rate_tier()
        icons = {"super_off_peak": "🟢", "off_peak": "🟡", "peak": "🔴"}
        icon = icons.get(tier, "⚪")
        enabled_str = "ACTIVE" if scheduler.enabled else "DISABLED"
        print(f"\n  ⚡ SLATE Energy Scheduler — {enabled_str}")
        print(f"  {'─' * 45}")
        print(f"  Current rate: {icon} {tier.upper()} (${cost}/kWh)")
        print(f"  Time: {datetime.now().strftime('%I:%M %p')}")

        budget = scheduler.check_budget()
        print(f"\n  Budget: ${budget['cost_this_month']:.2f} / ${budget['budget_limit']:.2f}"
              f" ({budget['budget_used_percent']:.0f}%)")
        if budget['alert_triggered']:
            print(f"  ⚠️  Budget alert threshold reached!")
        print()

    elif args.schedule:
        print(f"\n  ⚡ SLATE Energy Schedule — Today")
        print(f"  {'─' * 55}")
        energy = scheduler.config.get("energy", {})
        rates = energy.get("provider", {}).get("rates", {})
        icons = {"super_off_peak": "🟢", "off_peak": "🟡", "peak": "🔴"}

        for hour in range(24):
            tier_name = "unknown"
            cost = 0.0
            for tn, td in rates.items():
                if isinstance(td, dict) and hour in td.get("hours", []):
                    tier_name = tn
                    cost = td.get("cost_per_kwh", 0)
                    break
            icon = icons.get(tier_name, "⚪")
            time_str = f"{hour:02d}:00"
            marker = " ◄ NOW" if hour == datetime.now().hour else ""
            print(f"  {time_str}  {icon} {tier_name:18s} ${cost:.2f}/kWh{marker}")
        print()

    elif args.cost:
        estimate = scheduler.estimate_monthly_cost()
        if args.json:
            print(json.dumps(asdict(estimate), indent=2))
        else:
            print(f"\n  💰 SLATE Monthly Cost Estimate")
            print(f"  {'─' * 45}")
            print(f"  Actual (MTD):     ${estimate.actual_cost_usd:.4f}")
            print(f"  Projected (EOM):  ${estimate.projected_cost_usd:.4f}")
            print(f"  Without sched.:   ${estimate.unscheduled_cost_usd:.4f}")
            print(f"  Savings:          ${estimate.savings_usd:.4f} ({estimate.savings_percent:.0f}%)")
            print(f"  Budget:           ${estimate.budget_limit_usd:.2f}")
            bar_filled = int(estimate.budget_used_percent / 5)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)
            print(f"  Usage:            {bar} {estimate.budget_used_percent:.0f}%")
            print()

    elif args.queue:
        queue = scheduler.get_queue()
        if not queue:
            print(f"\n  No operations queued.")
        else:
            print(f"\n  📋 Queued Operations ({len(queue)})")
            print(f"  {'─' * 55}")
            for q in queue:
                print(f"  {q['operation']:30s} → {q['target_time'][:16]} ({q['target_window']})")
        print()

    elif args.providers:
        if args.zip:
            providers = EnergyProviderDatabase.lookup_by_zip(args.zip)
            if providers:
                print(f"\n  ⚡ Providers for ZIP {args.zip}:")
                for p in providers:
                    print(f"  • {p['name']} ({p['region']}) — Plans: {', '.join(p['plans'])}")
            else:
                print(f"\n  No providers found for ZIP {args.zip}")
                print(f"  Submit your provider via SLATE Discussions!")
        else:
            print(f"\n  ⚡ Available Energy Providers:")
            for p in EnergyProviderDatabase.list_all_providers():
                print(f"  • {p['name']:20s} {p['region']:30s} Plans: {', '.join(p['plans'])}")
        print()

    elif args.check:
        decision = scheduler.should_execute(args.check)
        icon = "✅" if decision.execute_now else "⏳"
        print(f"\n  {icon} {decision.operation}: {decision.reason}")
        if not decision.execute_now:
            print(f"     Next window: {decision.next_window}")
            print(f"     Savings if deferred: ${decision.savings_if_deferred:.4f}")
        print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
