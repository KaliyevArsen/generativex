from __future__ import annotations

from typing import Dict, Any, Optional

from telebot import TeleBot, types

import db as dbmod
from config import Config
from ai import generate_email
import ui


def register_handlers(bot: TeleBot, cfg: Config) -> None:
    # Simple in-memory dialog state (MVP)
    user_state: Dict[int, Dict[str, Any]] = {}

    def set_state(chat_id: int, state: str, data: Optional[dict] = None) -> None:
        user_state[chat_id] = {"state": state, "data": data or {}}

    def clear_state(chat_id: int) -> None:
        user_state.pop(chat_id, None)

    def get_state(chat_id: int) -> Optional[Dict[str, Any]]:
        return user_state.get(chat_id)

    @bot.message_handler(commands=["start"])
    def on_start(message: types.Message) -> None:
        bot.send_message(
            message.chat.id,
            "SponsoBot MVP-XS запущен.\nВыберите действие в меню.",
            reply_markup=ui.main_menu(),
            parse_mode="HTML",
        )

    @bot.message_handler(commands=["help"])
    def on_help(message: types.Message) -> None:
        bot.send_message(
            message.chat.id,
            "Команды/кнопки:\n"
            "➕ Лид — добавить лид\n"
            "📋 Лиды — список лидов\n"
            "📊 Дашборд — статистика по статусам\n\n"
            "В MVP отправка email отключена: используется Send (сим.).",
            reply_markup=ui.main_menu(),
        )

    @bot.message_handler(func=lambda m: (m.text or "") == "ℹ️ Помощь")
    def help_btn(message: types.Message) -> None:
        on_help(message)

    # --- Add lead flow ---
    @bot.message_handler(func=lambda m: (m.text or "") == "➕ Лид")
    def add_lead_start(message: types.Message) -> None:
        set_state(message.chat.id, "ADD_COMPANY", {})
        bot.send_message(message.chat.id, "Введите название компании:")

    # ВАЖНО: этот обработчик должен срабатывать ТОЛЬКО когда есть активный state,
    # иначе он перехватывает все сообщения и блокирует 📋 Лиды / 📊 Дашборд и т.д.
    @bot.message_handler(func=lambda m: get_state(m.chat.id) is not None, content_types=["text"])
    def on_text(message: types.Message) -> None:
        st = get_state(message.chat.id)  # здесь st уже точно не None
        text = (message.text or "").strip()

        if not text:
            bot.send_message(message.chat.id, "Пустое значение. Введите текст.")
            return

        state = st["state"]
        data = st["data"]

        if state == "ADD_COMPANY":
            data["company"] = text
            set_state(message.chat.id, "ADD_CONTACT", data)
            bot.send_message(message.chat.id, "Введите имя контакта (или должность/отдел):")
            return

        if state == "ADD_CONTACT":
            data["contact"] = text
            set_state(message.chat.id, "ADD_CHANNEL", data)
            bot.send_message(message.chat.id, "Введите канал (email/telegram/linkedin):")
            return

        if state == "ADD_CHANNEL":
            data["channel"] = text
            set_state(message.chat.id, "ADD_NOTE", data)
            bot.send_message(message.chat.id, "Заметка (можно коротко). Если нет — отправьте '-':")
            return

        if state == "ADD_NOTE":
            data["note"] = "" if text == "-" else text
            lead_id = dbmod.add_lead(
                cfg.db_path,
                company=data["company"],
                contact=data["contact"],
                channel=data["channel"],
                note=data["note"],
            )
            clear_state(message.chat.id)
            lead = dbmod.get_lead(cfg.db_path, lead_id)
            bot.send_message(
                message.chat.id,
                "Лид создан.\n\n" + ui.render_lead_card(lead),
                parse_mode="HTML",
                reply_markup=ui.main_menu(),
            )
            return

    # --- Leads list ---
    @bot.message_handler(func=lambda m: (m.text or "") == "📋 Лиды")
    def list_leads(message: types.Message) -> None:
        leads = dbmod.list_leads(cfg.db_path, limit=20)
        if not leads:
            bot.send_message(message.chat.id, "Лидов пока нет. Нажмите ➕ Лид.")
            return
        bot.send_message(
            message.chat.id,
            "Последние лиды (до 20):",
            reply_markup=ui.leads_list_kb(leads),
        )

    # --- Dashboard ---
    @bot.message_handler(func=lambda m: (m.text or "") == "📊 Дашборд")
    def dashboard(message: types.Message) -> None:
        c = dbmod.count_by_status(cfg.db_path)
        total = sum(c.values())
        bot.send_message(
            message.chat.id,
            f"Статусы (всего {total}):\n"
            f"NEW: {c.get('NEW', 0)}\n"
            f"DRAFTED: {c.get('DRAFTED', 0)}\n"
            f"SENT_SIMULATED: {c.get('SENT_SIMULATED', 0)}\n"
        )

    # --- Callbacks: open/gen/send ---
    @bot.callback_query_handler(func=lambda call: (call.data or "").startswith("lead:"))
    def on_lead_callback(call: types.CallbackQuery) -> None:
        try:
            _, lead_id_str, action = (call.data or "").split(":", 2)
            lead_id = int(lead_id_str)
        except Exception:
            bot.answer_callback_query(call.id, "Некорректные данные.")
            return

        lead = dbmod.get_lead(cfg.db_path, lead_id)
        if not lead:
            bot.answer_callback_query(call.id, "Лид не найден.")
            return

        if action == "open":
            last = dbmod.get_last_message_for_lead(cfg.db_path, lead_id)
            text = ui.render_lead_card(lead)
            if last:
                text += "\n" + ui.render_message_preview(last)
            bot.edit_message_text(
                text=text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=ui.lead_actions_kb(lead_id),
            )
            bot.answer_callback_query(call.id)
            return

        if action == "gen":
            bot.answer_callback_query(call.id, "Генерирую…")
            try:
                subject, body = generate_email(cfg, lead)
            except Exception:
                bot.send_message(call.message.chat.id, "Ошибка AI генерации. Проверьте OPENAI_API_KEY/модель.")
                return

            dbmod.save_message(cfg.db_path, lead_id, subject, body)
            dbmod.update_lead_status(cfg.db_path, lead_id, "DRAFTED")

            updated = dbmod.get_lead(cfg.db_path, lead_id)
            last = dbmod.get_last_message_for_lead(cfg.db_path, lead_id)

            text = ui.render_lead_card(updated) + "\n" + ui.render_message_preview(last)
            bot.edit_message_text(
                text=text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=ui.lead_actions_kb(lead_id),
            )
            return

        if action == "send":
            last = dbmod.get_last_message_for_lead(cfg.db_path, lead_id)
            if not last:
                bot.answer_callback_query(call.id, "Сначала сгенерируйте письмо.")
                return

            dbmod.update_lead_status(cfg.db_path, lead_id, "SENT_SIMULATED")
            updated = dbmod.get_lead(cfg.db_path, lead_id)

            # Send simulated output as separate message for easy copy
            bot.send_message(
                call.message.chat.id,
                "Send (симуляция): письмо НЕ отправлено.\n"
                "Скопируйте ниже и отправьте вручную.\n\n"
                f"Тема: {last.subject}\n\n{last.body}",
            )

            text = ui.render_lead_card(updated) + "\n" + ui.render_message_preview(last)
            bot.edit_message_text(
                text=text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=ui.lead_actions_kb(lead_id),
            )
            bot.answer_callback_query(call.id, "Статус обновлён.")
            return

        bot.answer_callback_query(call.id, "Неизвестное действие.")
