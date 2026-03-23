import os
from datetime import datetime
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))


# =========================
# HELPERS
# =========================

BACK_LABELS = ["🔙 Back", "🔙 Retour", "🔙 Назад"]


def is_back(text: str) -> bool:
    return text in BACK_LABELS


def generate_deal_id() -> str:
    return f"DX-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_number(amount: float) -> str:
    if float(amount).is_integer():
        return f"{int(amount):,}"
    return f"{amount:,.2f}"


def format_amount_with_currency(amount: float, currency: str) -> str:
    currency = currency.strip() if currency else ""
    if currency:
        return f"{format_number(amount)} {currency}"
    return format_number(amount)


def get_user_language(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("language", "en")


def normalize_send_method(user_text: str):
    mapping = {
        "💸 Bank Transfer": "bank_transfer",
        "💸 Virement": "bank_transfer",
        "💸 Банківський переказ": "bank_transfer",
        "🪙 Crypto": "crypto",
        "🪙 Крипто": "crypto",
        "🌐 PayPal": "paypal",
        "🌐 Skrill": "skrill",
        "➕ Others": "others",
        "➕ Autre": "others",
        "➕ Інше": "others",
    }
    return mapping.get(user_text)


def normalize_receive_method(user_text: str):
    mapping = {
        "💸 Bank Transfer": "bank_transfer",
        "💸 Virement": "bank_transfer",
        "💸 Банківський переказ": "bank_transfer",
        "🪙 Crypto": "crypto",
        "🪙 Крипто": "crypto",
        "🌐 PayPal": "paypal",
        "🌐 Skrill": "skrill",
        "💵 Cash": "cash",
        "💵 Готівка": "cash",
        "➕ Others": "others",
        "➕ Autre": "others",
        "➕ Інше": "others",
    }
    return mapping.get(user_text)


def normalize_amount_mode(user_text: str):
    mapping = {
        "✏️ Amount I send": "send",
        "✏️ Montant que j’envoie": "send",
        "✏️ Сума, яку я надсилаю": "send",
        "🎯 Amount I want to receive": "receive",
        "🎯 Montant que je veux recevoir": "receive",
        "🎯 Сума, яку я хочу отримати": "receive",
    }
    return mapping.get(user_text)


def format_method(method: str, language: str) -> str:
    labels = {
        "en": {
            "bank_transfer": "Bank Transfer",
            "cash": "Cash",
            "paypal": "PayPal",
            "skrill": "Skrill",
            "crypto": "Crypto",
            "others": "Others",
        },
        "fr": {
            "bank_transfer": "Virement",
            "cash": "Cash",
            "paypal": "PayPal",
            "skrill": "Skrill",
            "crypto": "Crypto",
            "others": "Autre",
        },
        "ua": {
            "bank_transfer": "Банківський переказ",
            "cash": "Готівка",
            "paypal": "PayPal",
            "skrill": "Skrill",
            "crypto": "Крипто",
            "others": "Інше",
        },
    }
    return labels.get(language, labels["en"]).get(method, method)


def get_cash_code(details: str) -> str:
    if not details:
        return ""
    if "THB" in details:
        return "THB_BANGKOK"
    if "EUR" in details:
        return "EUR_PARIS"
    if "USD" in details:
        return "USD_VEGAS"
    if "MAD" in details:
        return "MAD_MARRAKECH"
    return ""


def extract_cash_currency(details: str) -> str:
    if not details:
        return ""
    if "THB" in details:
        return "THB"
    if "EUR" in details:
        return "EUR"
    if "USD" in details:
        return "USD"
    if "MAD" in details:
        return "MAD"
    return ""


def get_side_currency(context: ContextTypes.DEFAULT_TYPE, side: str) -> str:
    method = context.user_data.get(f"exchange_{side}_method")

    if method == "bank_transfer":
        return context.user_data.get(f"exchange_{side}_bank_currency", "")

    if method == "crypto":
        return context.user_data.get(f"exchange_{side}_crypto_asset", "")

    if method in ["paypal", "skrill"]:
        return context.user_data.get(f"exchange_{side}_wallet_currency", "")

    if method == "cash":
        details = context.user_data.get(f"exchange_{side}_details", "")
        return extract_cash_currency(details)

    return ""


def get_amount_mode_label(language: str, mode: str) -> str:
    labels = {
        "en": {
            "send": "Amount I send",
            "receive": "Amount I want to receive",
        },
        "fr": {
            "send": "Montant que j’envoie",
            "receive": "Montant que je veux recevoir",
        },
        "ua": {
            "send": "Сума, яку я надсилаю",
            "receive": "Сума, яку я хочу отримати",
        },
    }
    return labels.get(language, labels["en"]).get(mode, mode)


def build_amount_prompt(language: str, amount_mode: str, currency: str) -> str:
    currency = currency or "selected currency"

    prompts = {
        "en": {
            "send": f"Please enter the amount you want to send in {currency}:",
            "receive": f"Please enter the amount you want to receive in {currency}:",
        },
        "fr": {
            "send": f"Veuillez saisir le montant que vous souhaitez envoyer en {currency} :",
            "receive": f"Veuillez saisir le montant que vous souhaitez recevoir en {currency} :",
        },
        "ua": {
            "send": f"Будь ласка, введіть суму, яку ви хочете надіслати в {currency}:",
            "receive": f"Будь ласка, введіть суму, яку ви хочете отримати в {currency}:",
        },
    }

    return prompts.get(language, prompts["en"])[amount_mode]


def get_amount_currency(context: ContextTypes.DEFAULT_TYPE) -> str:
    amount_mode = context.user_data.get("exchange_amount_mode", "send")
    if amount_mode == "receive":
        return get_side_currency(context, "receive")
    return get_side_currency(context, "send")


def build_side_summary(context: ContextTypes.DEFAULT_TYPE, side: str, language: str) -> str:
    method = context.user_data.get(f"exchange_{side}_method")

    if method == "bank_transfer":
        currency = context.user_data.get(f"exchange_{side}_bank_currency", "")
        transfer_method = context.user_data.get(f"exchange_{side}_bank_method", "")
        return f"{format_method(method, language)} ({currency} — {transfer_method})"

    if method == "crypto":
        asset = context.user_data.get(f"exchange_{side}_crypto_asset", "")
        network = context.user_data.get(f"exchange_{side}_crypto_network", "")
        return f"{format_method(method, language)} ({asset} — {network})"

    if method in ["paypal", "skrill"]:
        currency = context.user_data.get(f"exchange_{side}_wallet_currency", "")
        return f"{format_method(method, language)} ({currency})"

    if method == "cash":
        details = context.user_data.get(f"exchange_{side}_details", "")
        return f"{format_method(method, language)} ({details})"

    if method == "others":
        return format_method(method, language)

    return format_method(method or "", language)


def calculate_exchange_fees(context: ContextTypes.DEFAULT_TYPE, language: str):
    send_method = context.user_data.get("exchange_send_method")
    receive_method = context.user_data.get("exchange_receive_method")
    amount = context.user_data.get("exchange_amount", 0.0)

    send_cash_code = get_cash_code(context.user_data.get("exchange_send_details", ""))
    receive_cash_code = get_cash_code(context.user_data.get("exchange_receive_details", ""))

    result = {
        "fees_text": "Contact support" if language == "en" else (
            "Contacter le support" if language == "fr" else "Зверніться до підтримки"
        ),
        "rate_reference": None,
    }

    if {send_method, receive_method} == {"bank_transfer", "crypto"}:
        result["fees_text"] = "2% (minimum 40 USD)"
        return result

    if send_method == "crypto" and receive_method == "paypal":
        result["fees_text"] = "0%"
        return result

    if send_method == "crypto" and receive_method == "skrill":
        result["fees_text"] = "0%"
        return result

    if send_method == "paypal" and receive_method == "crypto":
        result["fees_text"] = "4%"
        return result

    if send_method == "skrill" and receive_method == "crypto":
        result["fees_text"] = "2%"
        return result

    if {send_method, receive_method} == {"cash", "crypto"} and ("THB_BANGKOK" in [send_cash_code, receive_cash_code]):
        result["rate_reference"] = (
            "Bitkub market rate" if language == "en"
            else "cours du marché Bitkub" if language == "fr"
            else "ринковий курс Bitkub"
        )
        if amount < 3000:
            result["fees_text"] = (
                "2.5% (below 3,000 USD: minimum 75 USD fee)" if language == "en"
                else "2.5% (en dessous de 3 000 USD : frais minimum de 75 USD)" if language == "fr"
                else "2.5% (нижче 3 000 USD: мінімальна комісія 75 USD)"
            )
        else:
            result["fees_text"] = (
                "2.5% (minimum trade 3,000 USD)" if language == "en"
                else "2.5% (montant minimum : 3 000 USD)" if language == "fr"
                else "2.5% (мінімальна сума угоди: 3 000 USD)"
            )
        return result

    if {send_method, receive_method} == {"cash", "crypto"} and ("EUR_PARIS" in [send_cash_code, receive_cash_code]):
        result["rate_reference"] = (
            "XE rate" if language == "en"
            else "taux XE" if language == "fr"
            else "курс XE"
        )
        if amount < 5000:
            result["fees_text"] = (
                "2% (below 5,000 EUR: minimum 100 EUR fee)" if language == "en"
                else "2% (en dessous de 5 000 EUR : frais minimum de 100 EUR)" if language == "fr"
                else "2% (нижче 5 000 EUR: мінімальна комісія 100 EUR)"
            )
        else:
            result["fees_text"] = (
                "2% (minimum trade 5,000 EUR)" if language == "en"
                else "2% (montant minimum : 5 000 EUR)" if language == "fr"
                else "2% (мінімальна сума угоди: 5 000 EUR)"
            )
        return result

    if {send_method, receive_method} == {"cash", "crypto"} and ("USD_VEGAS" in [send_cash_code, receive_cash_code]):
        result["fees_text"] = (
            "2% (minimum trade 10,000 USD)" if language == "en"
            else "2% (montant minimum : 10 000 USD)" if language == "fr"
            else "2% (мінімальна сума угоди: 10 000 USD)"
        )
        return result

    return result


# =========================
# KEYBOARDS
# =========================

def get_language_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["💱 Exchange", "📊 Rates"], ["📞 Support", "🌐 Language"]],
        "fr": [["💱 Échange", "📊 Tarifs"], ["📞 Support", "🌐 Langue"]],
        "ua": [["💱 Обмін", "📊 Тарифи"], ["📞 Підтримка", "🌐 Мова"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_exchange_method_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [
            ["💸 Bank Transfer", "🪙 Crypto"],
            ["🌐 PayPal", "🌐 Skrill"],
            ["➕ Others"],
            ["🔙 Back"],
        ],
        "fr": [
            ["💸 Virement", "🪙 Crypto"],
            ["🌐 PayPal", "🌐 Skrill"],
            ["➕ Autre"],
            ["🔙 Retour"],
        ],
        "ua": [
            ["💸 Банківський переказ", "🪙 Крипто"],
            ["🌐 PayPal", "🌐 Skrill"],
            ["➕ Інше"],
            ["🔙 Назад"],
        ],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_receive_method_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [
            ["💸 Bank Transfer", "🪙 Crypto"],
            ["🌐 PayPal", "🌐 Skrill"],
            ["💵 Cash", "➕ Others"],
            ["🔙 Back"],
        ],
        "fr": [
            ["💸 Virement", "🪙 Crypto"],
            ["🌐 PayPal", "🌐 Skrill"],
            ["💵 Cash", "➕ Autre"],
            ["🔙 Retour"],
        ],
        "ua": [
            ["💸 Банківський переказ", "🪙 Крипто"],
            ["🌐 PayPal", "🌐 Skrill"],
            ["💵 Готівка", "➕ Інше"],
            ["🔙 Назад"],
        ],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_cash_option_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [
            ["🇫🇷 EUR — Paris", "🇺🇸 USD — Las Vegas"],
            ["🇲🇦 MAD — Marrakech", "🇹🇭 THB — Bangkok"],
            ["➕ Other"],
            ["🔙 Back"],
        ],
        "fr": [
            ["🇫🇷 EUR — Paris", "🇺🇸 USD — Las Vegas"],
            ["🇲🇦 MAD — Marrakech", "🇹🇭 THB — Bangkok"],
            ["➕ Autre"],
            ["🔙 Retour"],
        ],
        "ua": [
            ["🇫🇷 EUR — Париж", "🇺🇸 USD — Лас-Вегас"],
            ["🇲🇦 MAD — Марракеш", "🇹🇭 THB — Бангкок"],
            ["➕ Інше"],
            ["🔙 Назад"],
        ],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_bank_currency_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["EUR", "USD"], ["THB", "GBP"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["EUR", "USD"], ["THB", "GBP"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["EUR", "USD"], ["THB", "GBP"], ["➕ Інше"], ["🔙 Назад"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_bank_method_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["Wise", "Revolut"], ["SEPA (EUR - Europe)", "SWIFT (International)"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["Wise", "Revolut"], ["SEPA (EUR - Europe)", "SWIFT (International)"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["Wise", "Revolut"], ["SEPA (EUR - Europe)", "SWIFT (International)"], ["➕ Інше"], ["🔙 Назад"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_crypto_asset_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["USDT", "USDC"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["USDT", "USDC"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["USDT", "USDC"], ["➕ Інше"], ["🔙 Назад"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_crypto_network_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["TRC20", "ERC20"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["TRC20", "ERC20"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["TRC20", "ERC20"], ["➕ Інше"], ["🔙 Назад"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_wallet_currency_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["EUR", "USD"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["EUR", "USD"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["EUR", "USD"], ["➕ Інше"], ["🔙 Назад"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_amount_choice_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [
            ["✏️ Amount I send"],
            ["🎯 Amount I want to receive"],
            ["🔙 Back"],
        ],
        "fr": [
            ["✏️ Montant que j’envoie"],
            ["🎯 Montant que je veux recevoir"],
            ["🔙 Retour"],
        ],
        "ua": [
            ["✏️ Сума, яку я надсилаю"],
            ["🎯 Сума, яку я хочу отримати"],
            ["🔙 Назад"],
        ],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_exchange_result_keyboard(language: str) -> InlineKeyboardMarkup:
    labels = {
        "en": [
            [InlineKeyboardButton("✅ Send Request", callback_data="exchange_send_request")],
            [InlineKeyboardButton("❌ Cancel", callback_data="exchange_cancel")],
        ],
        "fr": [
            [InlineKeyboardButton("✅ Envoyer la demande", callback_data="exchange_send_request")],
            [InlineKeyboardButton("❌ Annuler", callback_data="exchange_cancel")],
        ],
        "ua": [
            [InlineKeyboardButton("✅ Надіслати запит", callback_data="exchange_send_request")],
            [InlineKeyboardButton("❌ Скасувати", callback_data="exchange_cancel")],
        ],
    }
    return InlineKeyboardMarkup(labels.get(language, labels["en"]))


# =========================
# TEXTS
# =========================

def get_text(language: str, key: str) -> str:
    texts = {
        "en": {
            "welcome": "Welcome to Dervishaj Bot.\n\nSecure and fast fiat ↔ crypto exchange service.\n\nPlease select your language:",
            "language_set": "Language set to English.\n\nWelcome to Dervishaj Bot.\n\nPlease choose an option below:",
            "support_prompt": "Please send your message and our team will reply as soon as possible.",
            "support_sent": "Your message has been sent.\n\nOur team will get back to you shortly.",
            "use_menu": "Please use the menu buttons below.",
            "choose_language": "Please select your language:",
            "exchange_send": "What do you want to send?",
            "exchange_receive": "What do you want to receive?",
            "cash_option": "Select cash option:",
            "bank_currency": "Select transfer currency:",
            "bank_method": "Select transfer method:",
            "crypto_asset": "Select cryptocurrency:",
            "crypto_network": "Select network:",
            "wallet_currency": "Select currency:",
            "choose_amount_type": "Which amount do you want to enter?",
            "network_warning": "Please make sure to select the correct network.\n\nSending funds on the wrong network may result in permanent loss.",
            "next_receive_details": "Great. Now let's set the receive details.",
            "invalid_amount": "Please enter a valid amount.",
            "exchange_summary_title": "Your request:",
            "exchange_summary_send": "Send: {value}",
            "exchange_summary_receive": "Receive: {value}",
            "exchange_summary_entered": "Client entered: {value}",
            "exchange_summary_amount": "Entered amount: {value}",
            "exchange_summary_rate_reference": "Rate reference: {value}",
            "exchange_summary_fees": "Fees: {value}",
            "exchange_summary_final_note_send": "Final amount to receive will be confirmed by support.",
            "exchange_summary_final_note_receive": "Final amount to send will be confirmed by support.",
            "request_sent": "✅ Your request has been sent.\n\nReference: {deal_id}\n\nOur team will review it and get back to you shortly.",
            "request_cancelled": "❌ Request cancelled.",
            "custom_request_prompt": "Please describe your request:",
            "custom_request_sent": "✅ Your request has been sent.\n\nReference: {deal_id}\n\nOur team will review it and get back to you shortly.",
            "rates_text": (
                "Our Fees:\n\n"
                "Bank Transfer ↔ Crypto: 2% (minimum 40 USD)\n\n"
                "Cash Bangkok (THB): 2.5% based on Bitkub market rate\n"
                "- Below 3,000 USD: minimum 75 USD fee\n\n"
                "Cash Paris (EUR): 2% based on XE rate\n"
                "- Below 5,000 EUR: minimum 100 EUR fee\n\n"
                "Cash Las Vegas (USD): 2%\n"
                "- Minimum trade: 10,000 USD\n\n"
                "Crypto → PayPal: 0%\n"
                "PayPal → Crypto: 4%\n\n"
                "Crypto → Skrill: 0%\n"
                "Skrill → Crypto: 2%\n\n"
                "For other requests, please contact support."
            ),
        },
        "fr": {
            "welcome": "Welcome to Dervishaj Bot.\n\nSecure and fast fiat ↔ crypto exchange service.\n\nPlease select your language:",
            "language_set": "Langue définie sur le français.\n\nBienvenue sur Dervishaj Bot.\n\nVeuillez choisir une option ci-dessous :",
            "support_prompt": "Veuillez envoyer votre message et notre équipe vous répondra dès que possible.",
            "support_sent": "Votre message a bien été envoyé.\n\nNotre équipe vous répondra rapidement.",
            "use_menu": "Veuillez utiliser les boutons du menu ci-dessous.",
            "choose_language": "Veuillez sélectionner votre langue :",
            "exchange_send": "Que souhaitez-vous envoyer ?",
            "exchange_receive": "Que souhaitez-vous recevoir ?",
            "cash_option": "Sélectionnez une option cash :",
            "bank_currency": "Sélectionnez la devise du virement :",
            "bank_method": "Sélectionnez le type de virement :",
            "crypto_asset": "Sélectionnez la cryptomonnaie :",
            "crypto_network": "Sélectionnez le réseau :",
            "wallet_currency": "Sélectionnez la devise :",
            "choose_amount_type": "Quel montant souhaitez-vous renseigner ?",
            "network_warning": "Veuillez vous assurer de sélectionner le bon réseau.\n\nUn envoi sur le mauvais réseau peut entraîner une perte définitive des fonds.",
            "next_receive_details": "Parfait. Passons maintenant aux détails de réception.",
            "invalid_amount": "Veuillez saisir un montant valide.",
            "exchange_summary_title": "Votre demande :",
            "exchange_summary_send": "Envoyer : {value}",
            "exchange_summary_receive": "Recevoir : {value}",
            "exchange_summary_entered": "Montant saisi par le client : {value}",
            "exchange_summary_amount": "Montant saisi : {value}",
            "exchange_summary_rate_reference": "Référence du taux : {value}",
            "exchange_summary_fees": "Frais : {value}",
            "exchange_summary_final_note_send": "Le montant final reçu sera confirmé par le support.",
            "exchange_summary_final_note_receive": "Le montant final à envoyer sera confirmé par le support.",
            "request_sent": "✅ Votre demande a bien été envoyée.\n\nRéférence : {deal_id}\n\nNotre équipe va l’examiner et revenir vers vous rapidement.",
            "request_cancelled": "❌ Demande annulée.",
            "custom_request_prompt": "Veuillez décrire votre demande :",
            "custom_request_sent": "✅ Votre demande a bien été envoyée.\n\nRéférence : {deal_id}\n\nNotre équipe va l’examiner et revenir vers vous rapidement.",
            "rates_text": (
                "Nos frais :\n\n"
                "Virement ↔ Crypto : 2% (minimum 40 USD)\n\n"
                "Cash Bangkok (THB) : 2.5% basé sur le cours du marché Bitkub\n"
                "- En dessous de 3 000 USD : frais minimum de 75 USD\n\n"
                "Cash Paris (EUR) : 2% basé sur le taux XE\n"
                "- En dessous de 5 000 EUR : frais minimum de 100 EUR\n\n"
                "Cash Las Vegas (USD) : 2%\n"
                "- Montant minimum : 10 000 USD\n\n"
                "Crypto → PayPal : 0%\n"
                "PayPal → Crypto : 4%\n\n"
                "Crypto → Skrill : 0%\n"
                "Skrill → Crypto : 2%\n\n"
                "Pour toute autre demande, veuillez contacter le support."
            ),
        },
        "ua": {
            "welcome": "Welcome to Dervishaj Bot.\n\nSecure and fast fiat ↔ crypto exchange service.\n\nPlease select your language:",
            "language_set": "Мову встановлено: українська.\n\nЛаскаво просимо до Dervishaj Bot.\n\nБудь ласка, оберіть опцію нижче:",
            "support_prompt": "Будь ласка, надішліть ваше повідомлення, і наша команда відповість вам якомога швидше.",
            "support_sent": "Ваше повідомлення надіслано.\n\nНаша команда відповість вам найближчим часом.",
            "use_menu": "Будь ласка, використовуйте кнопки меню нижче.",
            "choose_language": "Будь ласка, оберіть мову:",
            "exchange_send": "Що ви хочете надіслати?",
            "exchange_receive": "Що ви хочете отримати?",
            "cash_option": "Оберіть варіант готівки:",
            "bank_currency": "Оберіть валюту переказу:",
            "bank_method": "Оберіть тип переказу:",
            "crypto_asset": "Оберіть криптовалюту:",
            "crypto_network": "Оберіть мережу:",
            "wallet_currency": "Оберіть валюту:",
            "choose_amount_type": "Яку суму ви хочете вказати?",
            "network_warning": "Будь ласка, переконайтеся, що ви обрали правильну мережу.\n\nВідправка коштів у неправильній мережі може призвести до їх безповоротної втрати.",
            "next_receive_details": "Чудово. Тепер переходимо до деталей отримання.",
            "invalid_amount": "Будь ласка, введіть коректну суму.",
            "exchange_summary_title": "Ваш запит:",
            "exchange_summary_send": "Відправити: {value}",
            "exchange_summary_receive": "Отримати: {value}",
            "exchange_summary_entered": "Клієнт ввів: {value}",
            "exchange_summary_amount": "Введена сума: {value}",
            "exchange_summary_rate_reference": "Базовий курс: {value}",
            "exchange_summary_fees": "Комісія: {value}",
            "exchange_summary_final_note_send": "Фінальна сума до отримання буде підтверджена підтримкою.",
            "exchange_summary_final_note_receive": "Фінальна сума до відправки буде підтверджена підтримкою.",
            "request_sent": "✅ Ваш запит надіслано.\n\nРеференс: {deal_id}\n\nНаша команда перегляне його та зв’яжеться з вами найближчим часом.",
            "request_cancelled": "❌ Запит скасовано.",
            "custom_request_prompt": "Будь ласка, опишіть ваш запит:",
            "custom_request_sent": "✅ Ваш запит надіслано.\n\nРеференс: {deal_id}\n\nНаша команда перегляне його та зв’яжеться з вами найближчим часом.",
            "rates_text": (
                "Наші комісії:\n\n"
                "Банківський переказ ↔ Крипто: 2% (мінімум 40 USD)\n\n"
                "Готівка Бангкок (THB): 2.5% на основі ринкового курсу Bitkub\n"
                "- Нижче 3 000 USD: мінімальна комісія 75 USD\n\n"
                "Готівка Париж (EUR): 2% на основі курсу XE\n"
                "- Нижче 5 000 EUR: мінімальна комісія 100 EUR\n\n"
                "Готівка Лас-Вегас (USD): 2%\n"
                "- Мінімальна сума: 10 000 USD\n\n"
                "Crypto → PayPal: 0%\n"
                "PayPal → Crypto: 4%\n\n"
                "Crypto → Skrill: 0%\n"
                "Skrill → Crypto: 2%\n\n"
                "Для інших запитів зверніться до підтримки."
            ),
        },
    }
    return texts.get(language, texts["en"])[key]


# =========================
# BACK LOGIC
# =========================

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = get_user_language(context)
    step = context.user_data.get("exchange_step")

    if step == "send":
        context.user_data["mode"] = None
        context.user_data["exchange_step"] = None
        await update.message.reply_text(
            get_text(language, "use_menu"),
            reply_markup=get_main_menu_keyboard(language),
        )
        return

    if step == "receive":
        context.user_data["exchange_step"] = "send"
        await update.message.reply_text(
            get_text(language, "exchange_send"),
            reply_markup=get_exchange_method_keyboard(language),
        )
        return

    if step == "send_details":
        method = context.user_data.get("exchange_send_method")
        detail_step = context.user_data.get("exchange_send_detail_step")

        if method == "bank_transfer":
            if detail_step == "bank_method":
                context.user_data["exchange_send_detail_step"] = "bank_currency"
                await update.message.reply_text(
                    get_text(language, "bank_currency"),
                    reply_markup=get_bank_currency_keyboard(language),
                )
                return
            context.user_data["exchange_step"] = "receive"
            await update.message.reply_text(
                get_text(language, "exchange_receive"),
                reply_markup=get_receive_method_keyboard(language),
            )
            return

        if method == "crypto":
            if detail_step == "crypto_network":
                context.user_data["exchange_send_detail_step"] = "crypto_asset"
                await update.message.reply_text(
                    get_text(language, "crypto_asset"),
                    reply_markup=get_crypto_asset_keyboard(language),
                )
                return
            context.user_data["exchange_step"] = "receive"
            await update.message.reply_text(
                get_text(language, "exchange_receive"),
                reply_markup=get_receive_method_keyboard(language),
            )
            return

        if method in ["paypal", "skrill", "cash"]:
            context.user_data["exchange_step"] = "receive"
            await update.message.reply_text(
                get_text(language, "exchange_receive"),
                reply_markup=get_receive_method_keyboard(language),
            )
            return

    if step == "receive_details":
        method = context.user_data.get("exchange_receive_method")
        detail_step = context.user_data.get("exchange_receive_detail_step")

        if method == "bank_transfer":
            if detail_step == "bank_method":
                context.user_data["exchange_receive_detail_step"] = "bank_currency"
                await update.message.reply_text(
                    get_text(language, "bank_currency"),
                    reply_markup=get_bank_currency_keyboard(language),
                )
                return
            context.user_data["exchange_step"] = "send_details"
            await ask_method_details(update, context, context.user_data.get("exchange_send_method"), "send")
            return

        if method == "crypto":
            if detail_step == "crypto_network":
                context.user_data["exchange_receive_detail_step"] = "crypto_asset"
                await update.message.reply_text(
                    get_text(language, "crypto_asset"),
                    reply_markup=get_crypto_asset_keyboard(language),
                )
                return
            context.user_data["exchange_step"] = "send_details"
            await ask_method_details(update, context, context.user_data.get("exchange_send_method"), "send")
            return

        if method in ["paypal", "skrill", "cash"]:
            context.user_data["exchange_step"] = "send_details"
            await ask_method_details(update, context, context.user_data.get("exchange_send_method"), "send")
            return

    if step == "amount_mode":
        context.user_data["exchange_step"] = "receive_details"
        await ask_method_details(update, context, context.user_data.get("exchange_receive_method"), "receive")
        return

    if step == "amount":
        context.user_data["exchange_step"] = "amount_mode"
        await update.message.reply_text(
            get_text(language, "choose_amount_type"),
            reply_markup=get_amount_choice_keyboard(language),
        )
        return

    context.user_data["mode"] = None
    context.user_data["exchange_step"] = None
    await update.message.reply_text(
        get_text(language, "use_menu"),
        reply_markup=get_main_menu_keyboard(language),
    )


# =========================
# MAIN FLOW HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        get_text("en", "welcome"),
        reply_markup=get_language_keyboard(),
    )


async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = get_user_language(context)
    user = update.effective_user
    message_text = update.message.text
    username = f"@{user.username}" if user.username else "No username"
    deal_id = generate_deal_id()
    timestamp = get_timestamp()

    admin_message = (
        "📞 New Support Message\n\n"
        f"🆔 Deal ID: {deal_id}\n"
        f"📌 Status: Pending\n"
        f"👤 User: {username}\n"
        f"🆔 Telegram ID: {user.id}\n"
        f"🌐 Language: {language.upper()}\n"
        f"🕒 Time: {timestamp}\n\n"
        f"📝 Message:\n{message_text}"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
    context.user_data["mode"] = None

    await update.message.reply_text(
        get_text(language, "support_sent"),
        reply_markup=get_main_menu_keyboard(language),
    )


async def handle_custom_request_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = get_user_language(context)
    user = update.effective_user
    message_text = update.message.text
    username = f"@{user.username}" if user.username else "No username"
    deal_id = generate_deal_id()
    timestamp = get_timestamp()

    admin_message = (
        "🧾 New Custom Request\n\n"
        f"🆔 Deal ID: {deal_id}\n"
        f"📌 Status: Pending\n"
        f"👤 User: {username}\n"
        f"🆔 Telegram ID: {user.id}\n"
        f"🌐 Language: {language.upper()}\n"
        f"🕒 Time: {timestamp}\n\n"
        f"📝 Message:\n{message_text}"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
    context.user_data.clear()

    await update.message.reply_text(
        get_text(language, "custom_request_sent").format(deal_id=deal_id),
        reply_markup=get_main_menu_keyboard(language),
    )


async def ask_method_details(update: Update, context: ContextTypes.DEFAULT_TYPE, method: str, side: str):
    language = get_user_language(context)
    context.user_data[f"exchange_{side}_detail_step"] = None

    if method == "cash":
        await update.message.reply_text(
            get_text(language, "cash_option"),
            reply_markup=get_cash_option_keyboard(language),
        )
        return

    if method == "bank_transfer":
        context.user_data[f"exchange_{side}_detail_step"] = "bank_currency"
        await update.message.reply_text(
            get_text(language, "bank_currency"),
            reply_markup=get_bank_currency_keyboard(language),
        )
        return

    if method == "crypto":
        context.user_data[f"exchange_{side}_detail_step"] = "crypto_asset"
        await update.message.reply_text(
            get_text(language, "crypto_asset"),
            reply_markup=get_crypto_asset_keyboard(language),
        )
        return

    if method in ["paypal", "skrill"]:
        context.user_data[f"exchange_{side}_detail_step"] = "wallet_currency"
        await update.message.reply_text(
            get_text(language, "wallet_currency"),
            reply_markup=get_wallet_currency_keyboard(language),
        )
        return

    context.user_data["exchange_step"] = "amount_mode"
    await update.message.reply_text(
        get_text(language, "choose_amount_type"),
        reply_markup=get_amount_choice_keyboard(language),
    )


async def handle_side_details(update: Update, context: ContextTypes.DEFAULT_TYPE, side: str):
    language = get_user_language(context)
    user_text = update.message.text
    method = context.user_data.get(f"exchange_{side}_method")
    detail_step = context.user_data.get(f"exchange_{side}_detail_step")

    if method == "cash":
        context.user_data[f"exchange_{side}_details"] = user_text
        if side == "send":
            context.user_data["exchange_step"] = "receive_details"
            await update.message.reply_text(get_text(language, "next_receive_details"))
            await ask_method_details(update, context, context.user_data.get("exchange_receive_method"), "receive")
        else:
            context.user_data["exchange_step"] = "amount_mode"
            await update.message.reply_text(
                get_text(language, "choose_amount_type"),
                reply_markup=get_amount_choice_keyboard(language),
            )
        return

    if method == "bank_transfer":
        if detail_step == "bank_currency":
            context.user_data[f"exchange_{side}_bank_currency"] = user_text
            context.user_data[f"exchange_{side}_detail_step"] = "bank_method"
            await update.message.reply_text(
                get_text(language, "bank_method"),
                reply_markup=get_bank_method_keyboard(language),
            )
            return

        if detail_step == "bank_method":
            context.user_data[f"exchange_{side}_bank_method"] = user_text
            if side == "send":
                context.user_data["exchange_step"] = "receive_details"
                await update.message.reply_text(get_text(language, "next_receive_details"))
                await ask_method_details(update, context, context.user_data.get("exchange_receive_method"), "receive")
            else:
                context.user_data["exchange_step"] = "amount_mode"
                await update.message.reply_text(
                    get_text(language, "choose_amount_type"),
                    reply_markup=get_amount_choice_keyboard(language),
                )
            return

    if method == "crypto":
        if detail_step == "crypto_asset":
            context.user_data[f"exchange_{side}_crypto_asset"] = user_text
            context.user_data[f"exchange_{side}_detail_step"] = "crypto_network"
            await update.message.reply_text(
                get_text(language, "crypto_network"),
                reply_markup=get_crypto_network_keyboard(language),
            )
            return

        if detail_step == "crypto_network":
            context.user_data[f"exchange_{side}_crypto_network"] = user_text
            await update.message.reply_text(get_text(language, "network_warning"))

            if side == "send":
                context.user_data["exchange_step"] = "receive_details"
                await update.message.reply_text(get_text(language, "next_receive_details"))
                await ask_method_details(update, context, context.user_data.get("exchange_receive_method"), "receive")
            else:
                context.user_data["exchange_step"] = "amount_mode"
                await update.message.reply_text(
                    get_text(language, "choose_amount_type"),
                    reply_markup=get_amount_choice_keyboard(language),
                )
            return

    if method in ["paypal", "skrill"]:
        if detail_step == "wallet_currency":
            context.user_data[f"exchange_{side}_wallet_currency"] = user_text
            if side == "send":
                context.user_data["exchange_step"] = "receive_details"
                await update.message.reply_text(get_text(language, "next_receive_details"))
                await ask_method_details(update, context, context.user_data.get("exchange_receive_method"), "receive")
            else:
                context.user_data["exchange_step"] = "amount_mode"
                await update.message.reply_text(
                    get_text(language, "choose_amount_type"),
                    reply_markup=get_amount_choice_keyboard(language),
                )
            return

    if method == "others":
        context.user_data["mode"] = "custom_request"
        context.user_data["exchange_step"] = None
        await update.message.reply_text(get_text(language, "custom_request_prompt"))


async def handle_exchange_amount_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = get_user_language(context)
    mode = normalize_amount_mode(update.message.text)

    if not mode:
        await update.message.reply_text(
            get_text(language, "choose_amount_type"),
            reply_markup=get_amount_choice_keyboard(language),
        )
        return

    context.user_data["exchange_amount_mode"] = mode
    context.user_data["exchange_step"] = "amount"

    amount_currency = get_amount_currency(context)

    await update.message.reply_text(
        build_amount_prompt(language, mode, amount_currency),
        reply_markup=get_main_menu_keyboard(language),
    )


async def handle_exchange_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = get_user_language(context)
    user_text = update.message.text.strip().replace(",", "")

    try:
        amount = float(user_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        amount_mode = context.user_data.get("exchange_amount_mode", "send")
        amount_currency = get_amount_currency(context)
        await update.message.reply_text(get_text(language, "invalid_amount"))
        await update.message.reply_text(
            build_amount_prompt(language, amount_mode, amount_currency),
            reply_markup=get_main_menu_keyboard(language),
        )
        return

    context.user_data["exchange_amount"] = amount
    context.user_data["exchange_step"] = None
    context.user_data["mode"] = None

    send_summary = build_side_summary(context, "send", language)
    receive_summary = build_side_summary(context, "receive", language)
    fees_info = calculate_exchange_fees(context, language)

    amount_mode = context.user_data.get("exchange_amount_mode", "send")
    amount_mode_label = get_amount_mode_label(language, amount_mode)
    amount_currency = get_amount_currency(context)
    amount_display = format_amount_with_currency(amount, amount_currency)

    summary_parts = [
        f"{get_text(language, 'exchange_summary_title')}\n",
        get_text(language, "exchange_summary_send").format(value=send_summary),
        get_text(language, "exchange_summary_receive").format(value=receive_summary),
        get_text(language, "exchange_summary_entered").format(value=amount_mode_label),
        get_text(language, "exchange_summary_amount").format(value=amount_display),
        "",
    ]

    if fees_info.get("rate_reference"):
        summary_parts.append(
            get_text(language, "exchange_summary_rate_reference").format(value=fees_info["rate_reference"])
        )

    summary_parts.append(
        get_text(language, "exchange_summary_fees").format(value=fees_info["fees_text"])
    )
    summary_parts.append("")

    if amount_mode == "receive":
        summary_parts.append(get_text(language, "exchange_summary_final_note_receive"))
    else:
        summary_parts.append(get_text(language, "exchange_summary_final_note_send"))

    summary = "\n".join(summary_parts)

    await update.message.reply_text(
        summary,
        reply_markup=get_exchange_result_keyboard(language),
    )


async def handle_exchange_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = get_user_language(context)
    user_text = update.message.text
    step = context.user_data.get("exchange_step")

    if is_back(user_text):
        await go_back(update, context)
        return

    if step == "send":
        selected_method = normalize_send_method(user_text)
        if not selected_method:
            await update.message.reply_text(
                get_text(language, "exchange_send"),
                reply_markup=get_exchange_method_keyboard(language),
            )
            return

        if selected_method == "others":
            context.user_data["mode"] = "custom_request"
            context.user_data["exchange_step"] = None
            await update.message.reply_text(get_text(language, "custom_request_prompt"))
            return

        context.user_data["exchange_send_method"] = selected_method
        context.user_data["exchange_step"] = "receive"

        await update.message.reply_text(
            get_text(language, "exchange_receive"),
            reply_markup=get_receive_method_keyboard(language),
        )
        return

    if step == "receive":
        selected_method = normalize_receive_method(user_text)
        if not selected_method:
            await update.message.reply_text(
                get_text(language, "exchange_receive"),
                reply_markup=get_receive_method_keyboard(language),
            )
            return

        if selected_method == "others":
            context.user_data["mode"] = "custom_request"
            context.user_data["exchange_step"] = None
            await update.message.reply_text(get_text(language, "custom_request_prompt"))
            return

        context.user_data["exchange_receive_method"] = selected_method
        context.user_data["exchange_step"] = "send_details"

        await ask_method_details(update, context, context.user_data.get("exchange_send_method"), "send")
        return

    if step == "send_details":
        await handle_side_details(update, context, "send")
        return

    if step == "receive_details":
        await handle_side_details(update, context, "receive")
        return

    if step == "amount_mode":
        await handle_exchange_amount_mode(update, context)
        return

    if step == "amount":
        await handle_exchange_amount(update, context)
        return


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    language = get_user_language(context)

    if query.data == "lang_en":
        context.user_data["language"] = "en"
        context.user_data["mode"] = None
        await query.message.reply_text(
            get_text("en", "language_set"),
            reply_markup=get_main_menu_keyboard("en"),
        )
        return

    if query.data == "lang_fr":
        context.user_data["language"] = "fr"
        context.user_data["mode"] = None
        await query.message.reply_text(
            get_text("fr", "language_set"),
            reply_markup=get_main_menu_keyboard("fr"),
        )
        return

    if query.data == "lang_ua":
        context.user_data["language"] = "ua"
        context.user_data["mode"] = None
        await query.message.reply_text(
            get_text("ua", "language_set"),
            reply_markup=get_main_menu_keyboard("ua"),
        )
        return

    if query.data == "exchange_send_request":
        user = query.from_user
        deal_id = generate_deal_id()
        timestamp = get_timestamp()

        send_summary = build_side_summary(context, "send", language)
        receive_summary = build_side_summary(context, "receive", language)
        amount = context.user_data.get("exchange_amount", 0)
        fees_info = calculate_exchange_fees(context, language)

        amount_mode = context.user_data.get("exchange_amount_mode", "send")
        amount_mode_label = get_amount_mode_label(language, amount_mode)
        amount_currency = get_amount_currency(context)
        amount_display = format_amount_with_currency(amount, amount_currency)

        admin_message_parts = [
            "💱 New Exchange Request\n",
            f"🆔 Deal ID: {deal_id}",
            f"📌 Status: Pending",
            f"👤 User: @{user.username if user.username else 'No username'}",
            f"🆔 Telegram ID: {user.id}",
            f"🌐 Language: {language.upper()}",
            f"🕒 Time: {timestamp}",
            "",
            f"Send: {send_summary}",
            f"Receive: {receive_summary}",
            f"Client entered: {amount_mode_label}",
            f"Entered amount: {amount_display}",
        ]

        if fees_info.get("rate_reference"):
            admin_message_parts.append(f"Rate reference: {fees_info['rate_reference']}")

        admin_message_parts.append(f"Fees: {fees_info['fees_text']}")

        if amount_mode == "receive":
            admin_message_parts.append("Final amount to send: to be confirmed by support")
        else:
            admin_message_parts.append("Final amount to receive: to be confirmed by support")

        admin_message = "\n".join(admin_message_parts)

        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)

        await query.message.reply_text(
            get_text(language, "request_sent").format(deal_id=deal_id),
            reply_markup=get_main_menu_keyboard(language),
        )

        context.user_data.clear()
        return

    if query.data == "exchange_cancel":
        await query.message.reply_text(
            get_text(language, "request_cancelled"),
            reply_markup=get_main_menu_keyboard(language),
        )
        context.user_data.clear()


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    language = get_user_language(context)
    mode = context.user_data.get("mode")

    if mode == "support":
        await handle_support_message(update, context)
        return

    if mode == "custom_request":
        await handle_custom_request_message(update, context)
        return

    if mode == "exchange":
        await handle_exchange_flow(update, context)
        return

    if user_text in ["💱 Exchange", "💱 Échange", "💱 Обмін"]:
        context.user_data["mode"] = "exchange"
        context.user_data["exchange_step"] = "send"
        context.user_data["exchange_send_method"] = None
        context.user_data["exchange_receive_method"] = None
        context.user_data["exchange_send_detail_step"] = None
        context.user_data["exchange_receive_detail_step"] = None
        context.user_data["exchange_amount_mode"] = None
        context.user_data["exchange_amount"] = None

        await update.message.reply_text(
            get_text(language, "exchange_send"),
            reply_markup=get_exchange_method_keyboard(language),
        )
        return

    if user_text in ["📊 Rates", "📊 Tarifs", "📊 Тарифи"]:
        await update.message.reply_text(
            get_text(language, "rates_text"),
            reply_markup=get_main_menu_keyboard(language),
        )
        return

    if user_text in ["📞 Support", "📞 Підтримка"]:
        context.user_data["mode"] = "support"
        await update.message.reply_text(
            get_text(language, "support_prompt"),
            reply_markup=get_main_menu_keyboard(language),
        )
        return

    if user_text in ["🌐 Language", "🌐 Langue", "🌐 Мова"]:
        context.user_data["mode"] = None
        await update.message.reply_text(
            get_text(language, "choose_language"),
            reply_markup=get_language_keyboard(),
        )
        return

    await update.message.reply_text(
        get_text(language, "use_menu"),
        reply_markup=get_main_menu_keyboard(language),
    )


# =========================
# MAIN
# =========================

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing")

    if ADMIN_CHAT_ID == 0:
        raise ValueError("ADMIN_CHAT_ID is missing or invalid")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()