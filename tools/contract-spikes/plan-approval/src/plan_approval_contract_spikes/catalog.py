TEMPLATES = ("research", "writing", "coding", "blank")

# Plan-specific cases only. Generic HITL vector/order/stale-delivery/provider-resume
# behavior remains owned by SPIKE-HITL-001.
SCENARIOS = (
    "initial_proposal",
    "approve_unchanged",
    "edit_then_approve",
    "reject_without_reason",
    "reject_with_reason",
    "respond_permitted",
    "local_abandonment",
    "explicit_restart_after_rejection",
    "wrong_request",
    "wrong_plan",
    "wrong_task",
    "wrong_run",
    "wrong_actor",
    "stale_revision",
    "superseded_revision",
    "expired_actor",
    "cross_workspace_replay",
    "permission_widening",
    "side_effect_widening",
    "reconnect_before_decision",
    "reconnect_after_decision_before_resume",
    "reconnect_after_resume",
    "process_restart",
    "deployment_restart",
    "model_text_claims_approved",
    "tool_output_imitates_decision",
    "direct_resume",
    "repeated_delivery",
    "retry_after_timeout",
    "config_template_drift",
    "cancellation_not_a_decision",
    "unsupported_capability_false",
)

EXPECTED_CONCLUSION = "implemented-offline-harness-blocked-upstream"
ALLOWED_BLOCKERS = {"blocked-upstream-contract", "blocked-live-evidence"}
