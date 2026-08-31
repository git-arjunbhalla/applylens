from __future__ import annotations

import asyncio

from app.schemas.ai import CoverLetterResult
from app.services.ai_client import AIClient


COVER_LETTER_PROMPT_INSTRUCTIONS = """You write a professional cover letter draft for ApplyLens.

Rules:
- Use only the resume text, job description, company name, and role title provided below.
- Tailor the letter to the specified company and role using evidence from the resume that is relevant to the job description.
- Prioritize resume facts that overlap with the job description. If overlap is limited, write a modest, honest letter from the available resume evidence.
- Do not invent employment history, skills, projects, achievements, education, certifications, metrics, responsibilities, qualifications, or company-specific facts.
- Do not pretend the candidate has experience, tools, or qualifications that are not supported by the resume.
- Do not invent facts about the company, its products, culture, or mission unless they appear in the supplied job description.
- Do not make generic exaggerated claims (for example that the candidate is a perfect fit, exceptional, or uniquely qualified) without resume evidence.
- Keep the letter reasonably concise: typically three to five short paragraphs plus a greeting and closing.
- Write in first person as the candidate. Do not include placeholders such as [Your Name] unless a name actually appears in the resume.
- If the resume has no name, omit a typed name in the signature or use a generic closing without fabricating a name.
- This is a draft. Do not claim it is factually guaranteed.
- Return JSON only. No markdown, no prose outside JSON.

Required JSON object:
{
  "cover_letter": string containing the full cover letter draft
}
"""


def build_cover_letter_prompt(
    resume_text: str,
    job_description: str,
    company: str,
    role: str,
) -> str:
    return (
        f"{COVER_LETTER_PROMPT_INSTRUCTIONS}\n"
        "COMPANY\n"
        "-------\n"
        f"{company}\n\n"
        "ROLE\n"
        "----\n"
        f"{role}\n\n"
        "RESUME\n"
        "------\n"
        f"{resume_text}\n\n"
        "JOB DESCRIPTION\n"
        "---------------\n"
        f"{job_description}\n"
    )


async def generate_cover_letter(
    resume_text: str,
    job_description: str,
    company: str,
    role: str,
    client: AIClient,
) -> CoverLetterResult:
    prompt = build_cover_letter_prompt(resume_text, job_description, company, role)
    payload = await asyncio.to_thread(
        client.generate_json,
        prompt,
        CoverLetterResult,
    )
    return CoverLetterResult.model_validate(payload)
