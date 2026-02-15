from typing import Protocol, runtime_checkable

import openai
from pydantic import BaseModel


class LLMCitation(BaseModel):
    reference_id: int
    chunk_id: int


class LLMClaim(BaseModel):
    text: str
    citations: list[LLMCitation]


class LLMGenerationResult(BaseModel):
    claims: list[LLMClaim]


@runtime_checkable
class LLMProvider(Protocol):
    def generate_claims(
        self,
        prompt: str,
        evidence_chunks: list[dict],
        system_prompt: str,
    ) -> LLMGenerationResult: ...


class OpenAIProvider:
    def __init__(self, api_key: str, model: str = "gpt-5-mini") -> None:
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def generate_claims(
        self,
        prompt: str,
        evidence_chunks: list[dict],
        system_prompt: str,
    ) -> LLMGenerationResult:
        chunk_listing = "\n".join(
            f"- chunk_id={c['id']} reference_id={c['reference_id']}: {c['content']}"
            for c in evidence_chunks
        )
        user_message = (
            f"{prompt}\n\n"
            f"Available evidence chunks (ONLY cite from these):\n{chunk_listing}"
        )

        completion = self.client.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format=LLMGenerationResult,
        )

        message = completion.choices[0].message
        if message.refusal:
            raise ValueError(f"LLM refused request: {message.refusal}")
        if message.parsed is None:
            raise ValueError("Failed to parse structured response")

        return message.parsed


class MockProvider:
    def __init__(self, fixed_result: LLMGenerationResult) -> None:
        self.fixed_result = fixed_result

    def generate_claims(
        self,
        prompt: str,
        evidence_chunks: list[dict],
        system_prompt: str,
    ) -> LLMGenerationResult:
        return self.fixed_result
