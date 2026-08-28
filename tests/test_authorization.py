"""Authorization: is_authorized() must fail closed, and the global guard
must actually block every handler, not just /start.

Trovato in revisione (nessun test esisteva prima):
1. is_authorized() restituiva True (accesso consentito) quando
   TELEGRAM_CHAT_ID non era configurato o era il placeholder — un bot che
   riavvia/spegne una macchina reale restava aperto a chiunque se questa
   variabile veniva dimenticata.
2. is_authorized() era controllato solo dentro /start: nessuno degli
   handler dei pulsanti (s_reboot, s_shutdown, d_restart_docker, ecc.)
   lo richiamava, quindi bypassavano l'autorizzazione anche a bot
   configurato correttamente.
"""
import importlib
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from telegram.ext import ApplicationHandlerStop


def _reload_bot(monkeypatch, chat_id):
    """bot_telegram.py legge TELEGRAM_CHAT_ID a import time: ogni test che
    vuole una configurazione diversa deve ricaricare il modulo dopo aver
    impostato l'ambiente, non limitarsi a monkeypatchare l'attributo."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    if chat_id is None:
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    else:
        monkeypatch.setenv("TELEGRAM_CHAT_ID", chat_id)
    sys.modules.pop("bot_telegram", None)
    return importlib.import_module("bot_telegram")


def _fake_update(*, user_id="999", chat_id="999", is_callback=False):
    user = SimpleNamespace(id=user_id)
    chat = SimpleNamespace(id=chat_id)
    if is_callback:
        callback_query = AsyncMock()
        return SimpleNamespace(effective_user=user, effective_chat=chat, callback_query=callback_query, effective_message=None)
    message = AsyncMock()
    return SimpleNamespace(effective_user=user, effective_chat=chat, callback_query=None, effective_message=message)


class TestFailsClosedWhenUnconfigured:
    def test_missing_chat_id_denies_everyone(self, monkeypatch):
        bot = _reload_bot(monkeypatch, chat_id=None)
        assert bot.is_authorized(_fake_update()) is False

    def test_placeholder_chat_id_denies_everyone(self, monkeypatch):
        bot = _reload_bot(monkeypatch, chat_id="IL_TUO_CHAT_ID_QUI")
        assert bot.is_authorized(_fake_update()) is False


class TestConfiguredAuthorization:
    def test_matching_user_is_authorized(self, monkeypatch):
        bot = _reload_bot(monkeypatch, chat_id="12345")
        assert bot.is_authorized(_fake_update(user_id="12345", chat_id="999")) is True

    def test_matching_chat_is_authorized(self, monkeypatch):
        bot = _reload_bot(monkeypatch, chat_id="12345")
        assert bot.is_authorized(_fake_update(user_id="999", chat_id="12345")) is True

    def test_unrelated_user_is_denied(self, monkeypatch):
        bot = _reload_bot(monkeypatch, chat_id="12345")
        assert bot.is_authorized(_fake_update(user_id="000", chat_id="000")) is False


class TestGlobalGuardBlocksEveryHandler:
    """La regressione reale: prima di questo fix, un utente non autorizzato
    poteva attivare direttamente un callback_data come "s_reboot" perche'
    nessuno degli handler dei pulsanti richiamava is_authorized()."""

    @pytest.mark.asyncio
    async def test_unauthorized_callback_query_is_stopped_before_reaching_any_handler(self, monkeypatch):
        bot = _reload_bot(monkeypatch, chat_id="12345")
        update = _fake_update(user_id="attacker", chat_id="attacker", is_callback=True)

        with pytest.raises(ApplicationHandlerStop):
            await bot._reject_unauthorized(update, context=None)

        update.callback_query.answer.assert_awaited_once()
        assert update.callback_query.answer.await_args.kwargs.get("show_alert") is True

    @pytest.mark.asyncio
    async def test_unauthorized_command_is_stopped_and_told_so(self, monkeypatch):
        bot = _reload_bot(monkeypatch, chat_id="12345")
        update = _fake_update(user_id="attacker", chat_id="attacker", is_callback=False)

        with pytest.raises(ApplicationHandlerStop):
            await bot._reject_unauthorized(update, context=None)

        update.effective_message.reply_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_authorized_update_passes_through_without_stopping(self, monkeypatch):
        bot = _reload_bot(monkeypatch, chat_id="12345")
        update = _fake_update(user_id="12345", chat_id="12345", is_callback=True)

        result = await bot._reject_unauthorized(update, context=None)

        assert result is None
        update.callback_query.answer.assert_not_awaited()
