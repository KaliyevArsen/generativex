# Program by Kaliyev.A
from __future__ import annotations

from html import escape
from telebot import types

from db import Lead, Message


def main_menu() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("➕ Лид"), types.KeyboardButton("📋 Лиды"))
    kb.row(types.KeyboardButton("📊 Дашборд"), types.KeyboardButton("ℹ️ Помощь"))
    return kb


def lead_actions_kb(lead_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✨ Сгенерировать", callback_data=f"lead:{lead_id}:gen"),
        types.InlineKeyboardButton("📤 Send (сим.)", callback_data=f"lead:{lead_id}:send"),
    )
    kb.row(types.InlineKeyboardButton("🔄 Обновить", callback_data=f"lead:{lead_id}:open"))
    return kb


def leads_list_kb(leads: list[Lead]) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    for l in leads:
        title = f"#{l.id} · {l.company} · {l.status}"
        kb.row(types.InlineKeyboardButton(title, callback_data=f"lead:{l.id}:open"))
    return kb


def render_lead_card(lead: Lead) -> str:
    return (
        f"<b>Лид #{lead.id}</b>\n"
        f"<b>Компания:</b> {escape(lead.company)}\n"
        f"<b>Контакт:</b> {escape(lead.contact)}\n"
        f"<b>Канал:</b> {escape(lead.channel)}\n"
        f"<b>Статус:</b> {escape(lead.status)}\n"
        f"<b>Заметка:</b> {escape(lead.note) if lead.note else '—'}\n"
        f"<b>Создан:</b> {escape(lead.created_at)} UTC\n"
    )


def render_message_preview(msg: Message) -> str:
    subject = escape(msg.subject)
    body = escape(msg.body)
    if len(body) > 1200:
        body = body[:1200] + "…"
    return (
        f"<b>Последнее письмо</b>\n"
        f"<b>Тема:</b> {subject}\n\n"
        f"{body}"
    )
