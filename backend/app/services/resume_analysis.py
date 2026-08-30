from __future__ import annotations

import asyncio

from app.schemas.ai import ResumeAnalysisResult
from app.services.ai_client import AIClient


RESUME_ANALYSIS_PROMPT_INSTRUCTIONS = """You compare a resume to a job description for ApplyLens.

Rules:
- Use only the resume and job description provided below.
- Do not invent skills, employers, titles, dates, tools, or experience that are not stated in the resume.
- Do not assume qualifications, education, or impact that the resume does not state.
- If the resume does not support a skill or claim, omit it. Use an empty list when nothing is evidenced.
- Do not write unsupported claims about the candidate's fitness for the role.
- Recommendations must be concise and useful, and must follow from gaps between the two texts.
- Return JSON only. No markdown, no prose outside JSON.

Required JSON object:
{
  "match_score": integer from 0 to 100 (how well the resume evidence matches the job description),
  "matching_skills": string array of skills present in both texts,
  "missing_skills": string array of skills required by the job description and not evidenced in the resume,
  "strengths": string array of resume-supported strengths relevant to the job,
  "weaknesses": string array of gaps or weaker evidence relative to the job description,
  "recommendations": string array of concise, actionable suggestions
}
"""


def build_resume_analysis_prompt(resume_text: str, job_description: str) -> str:
    return (
        f"{RESUME_ANALYSIS_PROMPT_INSTRUCTIONS}\n"
        "RESUME\n"
        "------\n"
        f"{resume_text}\n\n"
        "JOB DESCRIPTION\n"
        "---------------\n"
        f"{job_description}\n"
    )


async def analyze_resume(
    resume_text: str,
    job_description: str,
    client: AIClient,
) -> ResumeAnalysisResult:
    prompt = build_resume_analysis_prompt(resume_text, job_description)
    payload = await asyncio.to_thread(
        client.generate_json,
        prompt,
        ResumeAnalysisResult,
    )
    return ResumeAnalysisResult.model_validate(payload)
