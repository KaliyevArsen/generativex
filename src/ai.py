# Program by Kaliyev.A
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Tuple, Optional

from openai import OpenAI

from config import Config
from db import Lead


def _build_prompt(cfg: Config, lead: Lead) -> str:
    lang = "Russian" if cfg.language == "ru" else "English"
    return f"""
You write concise, professional sponsorship outreach emails in {lang}.

Context:
- Project/initiative: {cfg.project_name}
- Description: {cfg.event_desc}
- Target audience: {cfg.audience}
- Benefits for sponsor: {cfg.benefits}
- Ask amount: {cfg.ask_amount}

Lead:
- Company: {lead.company}
- Contact: {lead.contact}
- Contact channel (email/telegram/etc): {lead.channel}
- Notes: {lead.note}

Task:
Generate a single outreach email with:
1) subject (short)
2) body (5-10 short paragraphs max, concrete, respectful, no hype)

Output strictly as JSON:
{{"subject": "...", "body": "..."}}
""".strip()


def generate_email(cfg: Config, lead: Lead) -> Tuple[str, str]:
    if not cfg.openai_api_key:
        subject = f"Sponsorship proposal for {cfg.project_name}"
        body = (
            f"Здравствуйте, {lead.contact}!\n\n"
            f"Меня зовут [Ваше имя]. Я представляю {cfg.project_name}.\n"
            f"{cfg.event_desc}\n\n"
            f"Мы рассматриваем партнёрство со стороны {lead.company}. "
            f"Взамен предлагаем: {cfg.benefits}.\n\n"
            f"Ориентир по бюджету: {cfg.ask_amount}. "
            f"Будет ли удобно обсудить детали коротким созвоном?\n\n"
            f"С уважением,\n[Ваше имя]\n"
        )
        return subject, body

    client = OpenAI(api_key=cfg.openai_api_key)

    prompt = _build_prompt(cfg, lead)
    resp = client.chat.completions.create(
        model=cfg.openai_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )

    content = (resp.choices[0].message.content or "").strip()

    # Try parse JSON
    try:
        data = json.loads(content)
        subject = str(data.get("subject", "")).strip()
        body = str(data.get("body", "")).strip()
        if subject and body:
            return subject, body
    except Exception:
        pass

    # Fallback: heuristic split
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if not lines:
        return "Sponsorship proposal", "Hello!"
    subject = lines[0][:120]
    body = "\n".join(lines[1:]).strip() or content
    return subject, body
