# Program by Kaliyev.A
from __future__ import annotations

from telebot import TeleBot

from config import load_config
import db
from handlers import register_handlers


def main() -> None:
    cfg = load_config()

    db.init_db(cfg.db_path)

    bot = TeleBot(cfg.telegram_token, parse_mode="HTML")
    register_handlers(bot, cfg)

    bot.infinity_polling(timeout=30, long_polling_timeout=30)


if __name__ == "__main__":
    main()
