from __future__ import annotations

import asyncio

from app.schemas.ai import ResumeAnalysisResult
from app.services.ai_client import AIClient


RESUME_ANALYSIS_PROMPT_INSTRUCTIONS = """You evaluate a single resume for ApplyLens as a standalone ATS and resume-quality review.

This task is NOT job-description matching. Do not compare the resume to a job posting, role, or company. Do not invent a job description. Do not estimate fit for a specific opening.

Rules:
- Use only the resume text provided below.
- Do not invent employers, titles, dates, skills, tools, certifications, education, projects, or achievements that are not supported by the resume.
- Do not claim the candidate is qualified, will pass an ATS, will be shortlisted, or will get an interview.
- Do not pretend to know how any specific company's ATS works.
- The ats_score is an estimated resume-quality score (0-100) based only on observable characteristics in the supplied text.
- You receive extracted PDF text, not a visual layout. Do not claim to inspect fonts, columns, images, headers/footers graphics, or other visual formatting that cannot be determined from this text.
- If something cannot be determined from the extracted text, use an empty list for that field, or state the uncertainty in summary. Do not guess.
- Rewrite suggestions must rewrite wording that actually appears (or is closely paraphrased from) the resume. If no supported rewrite exists, use an empty array.
- Return JSON only. No markdown, no prose outside JSON.

Evaluate observable characteristics such as: section headings, readable structure, contact information, summary/objective, skills clarity, experience and project clarity, education clarity, measurable achievements, action verbs, technical specificity, keyword usefulness, repetition, vague statements, length, missing useful information, and generic descriptions.

Required JSON object:
{
  "ats_score": integer from 0 to 100,
  "score_breakdown": {
    "ats_compatibility": integer from 0 to 100,
    "content_strength": integer from 0 to 100,
    "keyword_optimization": integer from 0 to 100,
    "resume_structure": integer from 0 to 100,
    "achievement_quality": integer from 0 to 100
  },
  "strengths": string array,
  "issues": string array,
  "missing_sections": string array,
  "detected_skills": string array of skills evidenced in the resume,
  "keyword_suggestions": string array of concise, useful terms the writer could add if accurate,
  "improvement_suggestions": string array of actionable recommendations,
  "rewrite_suggestions": array of objects with "original", "suggested", and "reason" strings,
  "summary": string describing resume quality without making hiring claims
}
"""


def build_resume_analysis_prompt(resume_text: str) -> str:
    return (
        f"{RESUME_ANALYSIS_PROMPT_INSTRUCTIONS}\n"
        "RESUME\n"
        "------\n"
        f"{resume_text}\n"
    )


async def analyze_resume(
    resume_text: str,
    client: AIClient,
) -> ResumeAnalysisResult:
    prompt = build_resume_analysis_prompt(resume_text)
    payload = await asyncio.to_thread(
        client.generate_json,
        prompt,
        ResumeAnalysisResult,
    )
    return ResumeAnalysisResult.model_validate(payload)
