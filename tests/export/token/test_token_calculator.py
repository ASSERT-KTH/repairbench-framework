import pytest
from elleelleaime.export.token.token_calculator import TokenCalculator

# Token cost rates per million tokens for different providers
PROVIDER_RATES = {
    "openai-chatcompletion": {
        "prompt": 2.5,
        "completion": 10.0,
        "model": "gpt-4o-2024-08-06",
    },
    "mistral": {"prompt": 2.0, "completion": 6.0, "model": "mistral-large-2411"},
    "google": {"prompt": 0.1, "completion": 0.4, "model": "gemini-2.0-flash-001"},
    "openrouter": {
        "prompt": 2.8,
        "completion": 2.8,
        "model": "llama-3.1-405b-instruct",
    },
    "anthropic": {
        "prompt": 0.25,
        "completion": 1.25,
        "model": "claude-3-haiku-20240307",
    },
}


def calculate_expected_cost(tokens: int, rate: float) -> float:
    return tokens * rate / 1_000_000


@pytest.fixture
def sample_factory():
    def _create_sample(provider: str, prompt_tokens: int, completion_tokens: int):
        if provider == "google":
            return {
                "generation": [
                    {
                        "usage_metadata": {
                            "prompt_token_count": prompt_tokens,
                            "candidates_token_count": completion_tokens,
                        }
                    }
                ]
            }
        elif provider == "anthropic":
            return {
                "generation": [
                    {
                        "usage": {
                            "input_tokens": prompt_tokens,
                            "output_tokens": completion_tokens,
                        }
                    }
                ]
            }
        else:
            return {
                "generation": {
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                    }
                }
            }

    return _create_sample


def test_compute_usage_with_invalid_provider():
    samples = [
        {"generation": {"usage": {"prompt_tokens": 10, "completion_tokens": 20}}}
    ]
    result = TokenCalculator.compute_usage(samples, "invalid_provider", "model1")
    assert result is None


@pytest.mark.parametrize("provider", PROVIDER_RATES.keys())
def test_compute_usage(provider, sample_factory):
    prompt_tokens = 15
    completion_tokens = 25

    samples = [sample_factory(provider, prompt_tokens, completion_tokens)]
    rates = PROVIDER_RATES[provider]

    result = TokenCalculator.compute_usage(samples, provider, rates["model"])

    assert result is not None
    assert result["prompt_tokens"] == prompt_tokens
    assert result["completion_tokens"] == completion_tokens
    assert result["total_tokens"] == prompt_tokens + completion_tokens

    expected_prompt_cost = calculate_expected_cost(prompt_tokens, rates["prompt"])
    expected_completion_cost = calculate_expected_cost(
        completion_tokens, rates["completion"]
    )

    assert result["prompt_cost"] == expected_prompt_cost
    assert result["completion_cost"] == expected_completion_cost
    assert result["total_cost"] == expected_prompt_cost + expected_completion_cost
