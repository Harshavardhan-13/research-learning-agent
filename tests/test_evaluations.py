from pathlib import Path

from google.adk.evaluation.eval_config import EvalConfig
from google.adk.evaluation.eval_set import EvalSet

_PROJECT_ROOT = Path(__file__).parents[1]


def test_evaluation_artifacts_match_installed_adk_schema() -> None:
    eval_set = EvalSet.model_validate_json(
        (_PROJECT_ROOT / "evals/research_agent.evalset.json").read_text()
    )
    eval_config = EvalConfig.model_validate_json(
        (_PROJECT_ROOT / "evals/test_config.json").read_text()
    )

    assert {case.eval_id for case in eval_set.eval_cases} == {
        "kubernetes_from_scratch",
        "continue_to_next_module",
    }
    assert "rubric_based_final_response_quality_v1" in eval_config.criteria
