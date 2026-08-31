from __future__ import annotations

import asyncio

from app.schemas.ai import JDMatchResult
from app.services.ai_client import AIClient


JD_MATCH_PROMPT_INSTRUCTIONS = """You compare a resume to a job description for ApplyLens keyword matching.

Rules:
- Use only the resume and job description provided below.
- Identify keywords that are explicitly present or strongly implied by the supplied text.
- Do not invent experience, skills, certifications, education, projects, employment history, or qualifications that are not supported by the resume.
- Do not claim that the candidate is qualified for the role.
- Missing keywords are job-description terms without resume evidence. That is not proof the person lacks the skill.
- If something cannot be determined from the provided text, use an empty list for that field rather than guessing.
- Keep list items concise strings.
- Return JSON only. No markdown, no prose outside JSON.

Required JSON object:
{
  "matched_keywords": string array of keywords evidenced in both texts,
  "missing_keywords": string array of important job keywords not evidenced in the resume,
  "relevant_skills": string array of resume-supported skills relevant to the job,
  "important_requirements": string array of concise job requirements extracted from the job description,
  "match_score": integer from 0 to 100 (keyword and requirement overlap based only on the provided texts)
}
"""


def build_jd_match_prompt(resume_text: str, job_description: str) -> str:
    return (
        f"{JD_MATCH_PROMPT_INSTRUCTIONS}\n"
        "RESUME\n"
        "------\n"
        f"{resume_text}\n\n"
        "JOB DESCRIPTION\n"
        "---------------\n"
        f"{job_description}\n"
    )


async def match_job_description(
    resume_text: str,
    job_description: str,
    client: AIClient,
) -> JDMatchResult:
    prompt = build_jd_match_prompt(resume_text, job_description)
    payload = await asyncio.to_thread(
        client.generate_json,
        prompt,
        JDMatchResult,
    )
    return JDMatchResult.model_validate(payload)
