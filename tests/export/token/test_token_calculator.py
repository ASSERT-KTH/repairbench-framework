import pytest
from elleelleaime.export.token.token_calculator import TokenCalculator


def test_compute_usage_with_invalid_provider():
    samples = [
        {"generation": {"usage": {"prompt_tokens": 10, "completion_tokens": 20}}}
    ]
    result = TokenCalculator.compute_usage(samples, "invalid_provider", "model1")
    assert result is None


def test_compute_usage_with_openai():
    samples = [
        {"generation": [{"usage": {"prompt_tokens": 10, "completion_tokens": 20}}]}
    ]
    result = TokenCalculator.compute_usage(
        samples, "openai-chatcompletion", "gpt-4o-2024-08-06"
    )
    assert result is not None
    assert result["prompt_tokens"] == 10
    assert result["completion_tokens"] == 20
    assert result["total_tokens"] == 30
    assert (
        result["prompt_cost"] == 10 * 2.5 / 1_000_000
    )  # Based on OpenAI's cost per million tokens
    assert (
        result["completion_cost"] == 20 * 10 / 1_000_000
    )  # Based on OpenAI's cost per million tokens
    assert result["total_cost"] == result["prompt_cost"] + result["completion_cost"]


def test_compute_usage_with_mistral():
    samples = [
        {"generation": {"usage": {"prompt_tokens": 15, "completion_tokens": 25}}}
    ]
    result = TokenCalculator.compute_usage(samples, "mistral", "mistral-large-2411")
    assert result is not None
    assert result["prompt_tokens"] == 15
    assert result["completion_tokens"] == 25
    assert result["total_tokens"] == 40
    assert (
        result["prompt_cost"] == 15 * 2 / 1_000_000
    )  # Based on Mistral's cost per million tokens
    assert (
        result["completion_cost"] == 25 * 6 / 1_000_000
    )  # Based on Mistral's cost per million tokens
    assert result["total_cost"] == result["prompt_cost"] + result["completion_cost"]


def test_compute_usage_with_google():
    samples = [
        {
            "generation": [
                {
                    "usage_metadata": {
                        "prompt_token_count": 30,
                        "candidates_token_count": 40,
                    }
                }
            ]
        }
    ]
    result = TokenCalculator.compute_usage(samples, "google", "gemini-2.0-flash-001")
    assert result is not None
    assert result["prompt_tokens"] == 30
    assert result["completion_tokens"] == 40
    assert result["total_tokens"] == 70
    assert (
        result["prompt_cost"] == 30 * 0.125 / 1_000_000
    )  # Based on Google's cost per million tokens
    assert (
        result["completion_cost"] == 40 * 0.375 / 1_000_000
    )  # Based on Google's cost per million tokens
    assert result["total_cost"] == result["prompt_cost"] + result["completion_cost"]


def test_compute_usage_with_openrouter():
    samples = [
        {"generation": [{"usage": {"prompt_tokens": 20, "completion_tokens": 30}}]}
    ]
    result = TokenCalculator.compute_usage(
        samples, "openrouter", "claude-3-haiku-20240307"
    )
    assert result is not None
    assert result["prompt_tokens"] == 20
    assert result["completion_tokens"] == 30
    assert result["total_tokens"] == 50
    assert (
        result["prompt_cost"] == 20 * 0.25 / 1_000_000
    )  # Based on OpenRouter's cost per million tokens
    assert (
        result["completion_cost"] == 30 * 1.25 / 1_000_000
    )  # Based on OpenRouter's cost per million tokens
    assert result["total_cost"] == result["prompt_cost"] + result["completion_cost"]


def test_compute_usage_with_anthropic():
    samples = [{"generation": [{"usage": {"input_tokens": 25, "output_tokens": 35}}]}]
    result = TokenCalculator.compute_usage(
        samples, "anthropic", "claude-3-haiku-20240307"
    )
    assert result is not None
    assert result["prompt_tokens"] == 25
    assert result["completion_tokens"] == 35
    assert result["total_tokens"] == 60
    assert (
        result["prompt_cost"] == 25 * 0.25 / 1_000_000
    )  # Based on Anthropic's cost per million tokens
    assert (
        result["completion_cost"] == 35 * 1.25 / 1_000_000
    )  # Based on Anthropic's cost per million tokens
    assert result["total_cost"] == result["prompt_cost"] + result["completion_cost"]
