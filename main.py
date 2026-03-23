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

BACK_LABELS = ["🔙 Back", "🔙 Retour", "🔙 Назад", "🔙 กลับ"]


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
        "💸 โอนเงินผ่านธนาคาร": "bank_transfer",
        "🪙 Crypto": "crypto",
        "🪙 Крипто": "crypto",
        "🪙 คริปโต": "crypto",
        "🌐 PayPal": "paypal",
        "🌐 Skrill": "skrill",
        "➕ Others": "others",
        "➕ Autre": "others",
        "➕ Інше": "others",
        "➕ อื่นๆ": "others",
    }
    return mapping.get(user_text)


def normalize_receive_method(user_text: str):
    mapping = {
        "💸 Bank Transfer": "bank_transfer",
        "💸 Virement": "bank_transfer",
        "💸 Банківський переказ": "bank_transfer",
        "💸 โอนเงินผ่านธนาคาร": "bank_transfer",
        "🪙 Crypto": "crypto",
        "🪙 Крипто": "crypto",
        "🪙 คริปโต": "crypto",
        "🌐 PayPal": "paypal",
        "🌐 Skrill": "skrill",
        "💵 Cash": "cash",
        "💵 Готівка": "cash",
        "💵 เงินสด": "cash",
        "➕ Others": "others",
        "➕ Autre": "others",
        "➕ Інше": "others",
        "➕ อื่นๆ": "others",
    }
    return mapping.get(user_text)


def normalize_amount_mode(user_text: str):
    mapping = {
        "✏️ Amount I send": "send",
        "✏️ Montant que j’envoie": "send",
        "✏️ Сума, яку я надсилаю": "send",
        "✏️ จำนวนที่ฉันส่ง": "send",
        "🎯 Amount I want to receive": "receive",
        "🎯 Montant que je veux recevoir": "receive",
        "🎯 Сума, яку я хочу отримати": "receive",
        "🎯 จำนวนที่ฉันต้องการรับ": "receive",
    }
    return mapping.get(user_text)


def normalize_rates_category(user_text: str):
    mapping = {
        "💸 Bank Transfer": "bank_transfer",
        "💸 Virement": "bank_transfer",
        "💸 Банківський переказ": "bank_transfer",
        "💸 โอนเงินผ่านธนาคาร": "bank_transfer",
        "💵 Cash": "cash",
        "💵 Готівка": "cash",
        "💵 เงินสด": "cash",
        "🌐 PayPal": "paypal",
        "🌐 Skrill": "skrill",
        "➕ Other": "other",
        "➕ Autre": "other",
        "➕ Інше": "other",
        "➕ อื่นๆ": "other",
    }
    return mapping.get(user_text)


def normalize_cash_rates_location(user_text: str):
    mapping = {
        "🇹🇭 Bangkok THB": "bangkok_thb",
        "🇫🇷 Paris EUR": "paris_eur",
        "🇺🇸 Las Vegas USD": "vegas_usd",
        "🇲🇦 Marrakech MAD": "marrakech_mad",
        "🇹🇭 Бангкок THB": "bangkok_thb",
        "🇫🇷 Париж EUR": "paris_eur",
        "🇺🇸 Лас-Вегас USD": "vegas_usd",
        "🇲🇦 Марракеш MAD": "marrakech_mad",
        "🇹🇭 กรุงเทพ THB": "bangkok_thb",
        "🇫🇷 ปารีส EUR": "paris_eur",
        "🇺🇸 ลาสเวกัส USD": "vegas_usd",
        "🇲🇦 มาร์ราเกช MAD": "marrakech_mad",
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
        "th": {
            "bank_transfer": "โอนเงินผ่านธนาคาร",
            "cash": "เงินสด",
            "paypal": "PayPal",
            "skrill": "Skrill",
            "crypto": "คริปโต",
            "others": "อื่นๆ",
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
        "en": {"send": "Amount I send", "receive": "Amount I want to receive"},
        "fr": {"send": "Montant que j’envoie", "receive": "Montant que je veux recevoir"},
        "ua": {"send": "Сума, яку я надсилаю", "receive": "Сума, яку я хочу отримати"},
        "th": {"send": "จำนวนที่ฉันส่ง", "receive": "จำนวนที่ฉันต้องการรับ"},
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
        "th": {
            "send": f"กรุณาระบุจำนวนที่คุณต้องการส่งเป็น {currency}:",
            "receive": f"กรุณาระบุจำนวนที่คุณต้องการรับเป็น {currency}:",
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
            "Contacter le support" if language == "fr" else (
                "Зверніться до підтримки" if language == "ua" else "ติดต่อฝ่ายซัพพอร์ต"
            )
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
            else ("ринковий курс Bitkub" if language == "ua" else "อัตราตลาด Bitkub")
        )
        if amount < 3000:
            result["fees_text"] = (
                "2.5% (below 3,000 USD: minimum 75 USD fee)" if language == "en"
                else "2.5% (en dessous de 3 000 USD : frais minimum de 75 USD)" if language == "fr"
                else ("2.5% (нижче 3 000 USD: мінімальна комісія 75 USD)" if language == "ua"
                      else "2.5% (ต่ำกว่า 3,000 USD: ค่าธรรมเนียมขั้นต่ำ 75 USD)")
            )
        else:
            result["fees_text"] = (
                "2.5% (minimum trade 3,000 USD)" if language == "en"
                else "2.5% (montant minimum : 3 000 USD)" if language == "fr"
                else ("2.5% (мінімальна сума угоди: 3 000 USD)" if language == "ua"
                      else "2.5% (ยอดขั้นต่ำ 3,000 USD)")
            )
        return result

    if {send_method, receive_method} == {"cash", "crypto"} and ("EUR_PARIS" in [send_cash_code, receive_cash_code]):
        result["rate_reference"] = (
            "XE rate" if language == "en"
            else "taux XE" if language == "fr"
            else ("курс XE" if language == "ua" else "อัตรา XE")
        )
        if amount < 5000:
            result["fees_text"] = (
                "2% (below 5,000 EUR: minimum 100 EUR fee)" if language == "en"
                else "2% (en dessous de 5 000 EUR : frais minimum de 100 EUR)" if language == "fr"
                else ("2% (нижче 5 000 EUR: мінімальна комісія 100 EUR)" if language == "ua"
                      else "2% (ต่ำกว่า 5,000 EUR: ค่าธรรมเนียมขั้นต่ำ 100 EUR)")
            )
        else:
            result["fees_text"] = (
                "2% (minimum trade 5,000 EUR)" if language == "en"
                else "2% (montant minimum : 5 000 EUR)" if language == "fr"
                else ("2% (мінімальна сума угоди: 5 000 EUR)" if language == "ua"
                      else "2% (ยอดขั้นต่ำ 5,000 EUR)")
            )
        return result

    if {send_method, receive_method} == {"cash", "crypto"} and ("USD_VEGAS" in [send_cash_code, receive_cash_code]):
        result["fees_text"] = (
            "2% (minimum trade 10,000 USD)" if language == "en"
            else "2% (montant minimum : 10 000 USD)" if language == "fr"
            else ("2% (мінімальна сума угоди: 10 000 USD)" if language == "ua"
                  else "2% (ยอดขั้นต่ำ 10,000 USD)")
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
        [InlineKeyboardButton("🇹🇭 ไทย", callback_data="lang_th")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["💱 Exchange", "📊 Rates"], ["📞 Support", "🌐 Language"]],
        "fr": [["💱 Échange", "📊 Tarifs"], ["📞 Support", "🌐 Langue"]],
        "ua": [["💱 Обмін", "📊 Тарифи"], ["📞 Підтримка", "🌐 Мова"]],
        "th": [["💱 Exchange", "📊 Rates"], ["📞 Support", "🌐 Language"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_exchange_method_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["💸 Bank Transfer", "🪙 Crypto"], ["🌐 PayPal", "🌐 Skrill"], ["➕ Others"], ["🔙 Back"]],
        "fr": [["💸 Virement", "🪙 Crypto"], ["🌐 PayPal", "🌐 Skrill"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["💸 Банківський переказ", "🪙 Крипто"], ["🌐 PayPal", "🌐 Skrill"], ["➕ Інше"], ["🔙 Назад"]],
        "th": [["💸 โอนเงินผ่านธนาคาร", "🪙 คริปโต"], ["🌐 PayPal", "🌐 Skrill"], ["➕ อื่นๆ"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_receive_method_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["💸 Bank Transfer", "🪙 Crypto"], ["🌐 PayPal", "🌐 Skrill"], ["💵 Cash", "➕ Others"], ["🔙 Back"]],
        "fr": [["💸 Virement", "🪙 Crypto"], ["🌐 PayPal", "🌐 Skrill"], ["💵 Cash", "➕ Autre"], ["🔙 Retour"]],
        "ua": [["💸 Банківський переказ", "🪙 Крипто"], ["🌐 PayPal", "🌐 Skrill"], ["💵 Готівка", "➕ Інше"], ["🔙 Назад"]],
        "th": [["💸 โอนเงินผ่านธนาคาร", "🪙 คริปโต"], ["🌐 PayPal", "🌐 Skrill"], ["💵 เงินสด", "➕ อื่นๆ"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_cash_option_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["🇫🇷 EUR — Paris", "🇺🇸 USD — Las Vegas"], ["🇲🇦 MAD — Marrakech", "🇹🇭 THB — Bangkok"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["🇫🇷 EUR — Paris", "🇺🇸 USD — Las Vegas"], ["🇲🇦 MAD — Marrakech", "🇹🇭 THB — Bangkok"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["🇫🇷 EUR — Париж", "🇺🇸 USD — Лас-Вегас"], ["🇲🇦 MAD — Марракеш", "🇹🇭 THB — Бангкок"], ["➕ Інше"], ["🔙 Назад"]],
        "th": [["🇫🇷 EUR — Paris", "🇺🇸 USD — Las Vegas"], ["🇲🇦 MAD — Marrakech", "🇹🇭 THB — Bangkok"], ["➕ อื่นๆ"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_bank_currency_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["EUR", "USD"], ["THB", "GBP"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["EUR", "USD"], ["THB", "GBP"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["EUR", "USD"], ["THB", "GBP"], ["➕ Інше"], ["🔙 Назад"]],
        "th": [["EUR", "USD"], ["THB", "GBP"], ["➕ อื่นๆ"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_bank_method_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["Wise", "Revolut"], ["SEPA (EUR - Europe)", "SWIFT (International)"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["Wise", "Revolut"], ["SEPA (EUR - Europe)", "SWIFT (International)"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["Wise", "Revolut"], ["SEPA (EUR - Europe)", "SWIFT (International)"], ["➕ Інше"], ["🔙 Назад"]],
        "th": [["Wise", "Revolut"], ["SEPA (EUR - Europe)", "SWIFT (International)"], ["➕ อื่นๆ"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_crypto_asset_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["USDT", "USDC"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["USDT", "USDC"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["USDT", "USDC"], ["➕ Інше"], ["🔙 Назад"]],
        "th": [["USDT", "USDC"], ["➕ อื่นๆ"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_crypto_network_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["TRC20", "ERC20"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["TRC20", "ERC20"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["TRC20", "ERC20"], ["➕ Інше"], ["🔙 Назад"]],
        "th": [["TRC20", "ERC20"], ["➕ อื่นๆ"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_wallet_currency_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["EUR", "USD"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["EUR", "USD"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["EUR", "USD"], ["➕ Інше"], ["🔙 Назад"]],
        "th": [["EUR", "USD"], ["➕ อื่นๆ"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_amount_choice_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["✏️ Amount I send"], ["🎯 Amount I want to receive"], ["🔙 Back"]],
        "fr": [["✏️ Montant que j’envoie"], ["🎯 Montant que je veux recevoir"], ["🔙 Retour"]],
        "ua": [["✏️ Сума, яку я надсилаю"], ["🎯 Сума, яку я хочу отримати"], ["🔙 Назад"]],
        "th": [["✏️ จำนวนที่ฉันส่ง"], ["🎯 จำนวนที่ฉันต้องการรับ"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_rates_category_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["💸 Bank Transfer", "💵 Cash"], ["🌐 PayPal", "🌐 Skrill"], ["➕ Other"], ["🔙 Back"]],
        "fr": [["💸 Virement", "💵 Cash"], ["🌐 PayPal", "🌐 Skrill"], ["➕ Autre"], ["🔙 Retour"]],
        "ua": [["💸 Банківський переказ", "💵 Готівка"], ["🌐 PayPal", "🌐 Skrill"], ["➕ Інше"], ["🔙 Назад"]],
        "th": [["💸 โอนเงินผ่านธนาคาร", "💵 เงินสด"], ["🌐 PayPal", "🌐 Skrill"], ["➕ อื่นๆ"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_cash_rates_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = {
        "en": [["🇹🇭 Bangkok THB", "🇫🇷 Paris EUR"], ["🇺🇸 Las Vegas USD", "🇲🇦 Marrakech MAD"], ["🔙 Back"]],
        "fr": [["🇹🇭 Bangkok THB", "🇫🇷 Paris EUR"], ["🇺🇸 Las Vegas USD", "🇲🇦 Marrakech MAD"], ["🔙 Retour"]],
        "ua": [["🇹🇭 Bangkok THB", "🇫🇷 Париж EUR"], ["🇺🇸 Лас-Вегас USD", "🇲🇦 Марракеш MAD"], ["🔙 Назад"]],
        "th": [["🇹🇭 กรุงเทพ THB", "🇫🇷 ปารีส EUR"], ["🇺🇸 ลาสเวกัส USD", "🇲🇦 มาร์ราเกช MAD"], ["🔙 กลับ"]],
    }
    return ReplyKeyboardMarkup(labels.get(language, labels["en"]), resize_keyboard=True, one_time_keyboard=False)


def get_exchange_result_keyboard(language: str) -> InlineKeyboardMarkup:
    labels = {
        "en": [[InlineKeyboardButton("✅ Send Request", callback_data="exchange_send_request")],
               [InlineKeyboardButton("❌ Cancel", callback_data="exchange_cancel")]],
        "fr": [[InlineKeyboardButton("✅ Envoyer la demande", callback_data="exchange_send_request")],
               [InlineKeyboardButton("❌ Annuler", callback_data="exchange_cancel")]],
        "ua": [[InlineKeyboardButton("✅ Надіслати запит", callback_data="exchange_send_request")],
               [InlineKeyboardButton("❌ Скасувати", callback_data="exchange_cancel")]],
        "th": [[InlineKeyboardButton("✅ ส่งคำขอ", callback_data="exchange_send_request")],
               [InlineKeyboardButton("❌ ยกเลิก", callback_data="exchange_cancel")]],
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
            "choose_rates_category": "Select a category:",
            "choose_cash_rates_location": "Select a cash location:",
            "network_warning": "Please make sure to select the correct network.\n\nSending funds on the wrong network may result in permanent loss.",
            "next_receive_method": "Great. Now select what you want to receive.",
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
            "rates_bank_transfer": "💸 Bank Transfer Rates\n\nBank Transfer ↔ Crypto: 2%\nMinimum fee: 40 USD\n\nFinal quote confirmed by support.",
            "rates_paypal": "🌐 PayPal Rates\n\nCrypto → PayPal: 0%\nPayPal → Crypto: 4%\n\nFinal quote confirmed by support.",
            "rates_skrill": "🌐 Skrill Rates\n\nCrypto → Skrill: 0%\nSkrill → Crypto: 2%\n\nFinal quote confirmed by support.",
            "rates_other": "➕ Other Requests\n\nFor other currencies or custom requests, please contact support.",
            "rates_cash_bangkok": "🇹🇭 Bangkok THB Rates\n\nCash ↔ Crypto: 2.5%\nBased on Bitkub market rate\nBelow 3,000 USD: minimum 75 USD fee\n\nFinal quote confirmed by support.",
            "rates_cash_paris": "🇫🇷 Paris EUR Rates\n\nCash ↔ Crypto: 2%\nBased on XE rate\nBelow 5,000 EUR: minimum 100 EUR fee\n\nFinal quote confirmed by support.",
            "rates_cash_vegas": "🇺🇸 Las Vegas USD Rates\n\nCash ↔ Crypto: 2%\nMinimum trade: 10,000 USD\n\nFinal quote confirmed by support.",
            "rates_cash_marrakech": "🇲🇦 Marrakech MAD Rates\n\nPlease contact support for MAD cash requests.",
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
            "choose_rates_category": "Sélectionnez une catégorie :",
            "choose_cash_rates_location": "Sélectionnez une localisation cash :",
            "network_warning": "Veuillez vous assurer de sélectionner le bon réseau.\n\nUn envoi sur le mauvais réseau peut entraîner une perte définitive des fonds.",
            "next_receive_method": "Parfait. Sélectionnez maintenant ce que vous souhaitez recevoir.",
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
            "rates_bank_transfer": "💸 Tarifs Virement\n\nVirement ↔ Crypto : 2%\nFrais minimum : 40 USD\n\nLe devis final sera confirmé par le support.",
            "rates_paypal": "🌐 Tarifs PayPal\n\nCrypto → PayPal : 0%\nPayPal → Crypto : 4%\n\nLe devis final sera confirmé par le support.",
            "rates_skrill": "🌐 Tarifs Skrill\n\nCrypto → Skrill : 0%\nSkrill → Crypto : 2%\n\nLe devis final sera confirmé par le support.",
            "rates_other": "➕ Autres demandes\n\nPour les autres devises ou demandes personnalisées, veuillez contacter le support.",
            "rates_cash_bangkok": "🇹🇭 Tarifs Bangkok THB\n\nCash ↔ Crypto : 2.5%\nBasé sur le cours du marché Bitkub\nEn dessous de 3 000 USD : frais minimum de 75 USD\n\nLe devis final sera confirmé par le support.",
            "rates_cash_paris": "🇫🇷 Tarifs Paris EUR\n\nCash ↔ Crypto : 2%\nBasé sur le taux XE\nEn dessous de 5 000 EUR : frais minimum de 100 EUR\n\nLe devis final sera confirmé par le support.",
            "rates_cash_vegas": "🇺🇸 Tarifs Las Vegas USD\n\nCash ↔ Crypto : 2%\nMontant minimum : 10 000 USD\n\nLe devis final sera confirmé par le support.",
            "rates_cash_marrakech": "🇲🇦 Tarifs Marrakech MAD\n\nVeuillez contacter le support pour les demandes cash en MAD.",
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
            "choose_rates_category": "Оберіть категорію:",
            "choose_cash_rates_location": "Оберіть локацію для готівки:",
            "network_warning": "Будь ласка, переконайтеся, що ви обрали правильну мережу.\n\nВідправка коштів у неправильній мережі може призвести до їх безповоротної втрати.",
            "next_receive_method": "Чудово. Тепер виберіть, що ви хочете отримати.",
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
            "rates_bank_transfer": "💸 Тарифи банківського переказу\n\nБанківський переказ ↔ Крипто: 2%\nМінімальна комісія: 40 USD\n\nФінальний курс підтверджується підтримкою.",
            "rates_paypal": "🌐 Тарифи PayPal\n\nCrypto → PayPal: 0%\nPayPal → Crypto: 4%\n\nФінальний курс підтверджується підтримкою.",
            "rates_skrill": "🌐 Тарифи Skrill\n\nCrypto → Skrill: 0%\nSkrill → Crypto: 2%\n\nФінальний курс підтверджується підтримкою.",
            "rates_other": "➕ Інші запити\n\nДля інших валют або нестандартних запитів зверніться до підтримки.",
            "rates_cash_bangkok": "🇹🇭 Тарифи Bangkok THB\n\nГотівка ↔ Крипто: 2.5%\nНа основі ринкового курсу Bitkub\nНижче 3 000 USD: мінімальна комісія 75 USD\n\nФінальний курс підтверджується підтримкою.",
            "rates_cash_paris": "🇫🇷 Тарифи Paris EUR\n\nГотівка ↔ Крипто: 2%\nНа основі курсу XE\nНижче 5 000 EUR: мінімальна комісія 100 EUR\n\nФінальний курс підтверджується підтримкою.",
            "rates_cash_vegas": "🇺🇸 Тарифи Las Vegas USD\n\nГотівка ↔ Крипто: 2%\nМінімальна сума угоди: 10 000 USD\n\nФінальний курс підтверджується підтримкою.",
            "rates_cash_marrakech": "🇲🇦 Тарифи Marrakech MAD\n\nДля готівкових запитів у MAD зверніться до підтримки.",
        },
        "th": {
            "welcome": "ยินดีต้อนรับสู่ Dervishaj Bot\n\nบริการแลกเปลี่ยน fiat ↔ crypto ที่รวดเร็วและปลอดภัย\n\nกรุณาเลือกภาษา:",
            "language_set": "ตั้งค่าภาษาเป็นภาษาไทยแล้ว\n\nยินดีต้อนรับสู่ Dervishaj Bot\n\nกรุณาเลือกตัวเลือกด้านล่าง:",
            "support_prompt": "กรุณาส่งข้อความของคุณ แล้วทีมงานจะตอบกลับโดยเร็วที่สุด",
            "support_sent": "ข้อความของคุณถูกส่งแล้ว\n\nทีมงานจะติดต่อกลับโดยเร็วที่สุด",
            "use_menu": "กรุณาใช้ปุ่มเมนูด้านล่าง",
            "choose_language": "กรุณาเลือกภาษา:",
            "exchange_send": "คุณต้องการส่งอะไร?",
            "exchange_receive": "คุณต้องการรับอะไร?",
            "cash_option": "เลือกตัวเลือกเงินสด:",
            "bank_currency": "เลือกสกุลเงินของการโอน:",
            "bank_method": "เลือกวิธีการโอน:",
            "crypto_asset": "เลือกคริปโต:",
            "crypto_network": "เลือกเครือข่าย:",
            "wallet_currency": "เลือกสกุลเงิน:",
            "choose_amount_type": "คุณต้องการกรอกจำนวนแบบไหน?",
            "choose_rates_category": "เลือกหมวดหมู่:",
            "choose_cash_rates_location": "เลือกสถานที่รับเงินสด:",
            "network_warning": "กรุณาเลือกเครือข่ายให้ถูกต้อง\n\nหากส่งเงินไปผิดเครือข่าย อาจทำให้เงินสูญหายถาวร",
            "next_receive_method": "ยอดเยี่ยม ตอนนี้เลือกสิ่งที่คุณต้องการรับ",
            "invalid_amount": "กรุณากรอกจำนวนที่ถูกต้อง",
            "exchange_summary_title": "คำขอของคุณ:",
            "exchange_summary_send": "ส่ง: {value}",
            "exchange_summary_receive": "รับ: {value}",
            "exchange_summary_entered": "ลูกค้ากรอก: {value}",
            "exchange_summary_amount": "จำนวนที่กรอก: {value}",
            "exchange_summary_rate_reference": "อ้างอิงอัตรา: {value}",
            "exchange_summary_fees": "ค่าธรรมเนียม: {value}",
            "exchange_summary_final_note_send": "จำนวนที่จะได้รับจริงจะได้รับการยืนยันโดยซัพพอร์ต",
            "exchange_summary_final_note_receive": "จำนวนที่จะต้องส่งจริงจะได้รับการยืนยันโดยซัพพอร์ต",
            "request_sent": "✅ คำขอของคุณถูกส่งแล้ว\n\nอ้างอิง: {deal_id}\n\nทีมงานจะตรวจสอบและติดต่อกลับโดยเร็วที่สุด",
            "request_cancelled": "❌ ยกเลิกคำขอแล้ว",
            "custom_request_prompt": "กรุณาอธิบายคำขอของคุณ:",
            "custom_request_sent": "✅ คำขอของคุณถูกส่งแล้ว\n\nอ้างอิง: {deal_id}\n\nทีมงานจะตรวจสอบและติดต่อกลับโดยเร็วที่สุด",
            "rates_bank_transfer": "💸 ค่าธรรมเนียมโอนเงินผ่านธนาคาร\n\nโอนเงินผ่านธนาคาร ↔ คริปโต: 2%\nค่าธรรมเนียมขั้นต่ำ: 40 USD\n\nราคาสุดท้ายจะได้รับการยืนยันโดยซัพพอร์ต",
            "rates_paypal": "🌐 ค่าธรรมเนียม PayPal\n\nCrypto → PayPal: 0%\nPayPal → Crypto: 4%\n\nราคาสุดท้ายจะได้รับการยืนยันโดยซัพพอร์ต",
            "rates_skrill": "🌐 ค่าธรรมเนียม Skrill\n\nCrypto → Skrill: 0%\nSkrill → Crypto: 2%\n\nราคาสุดท้ายจะได้รับการยืนยันโดยซัพพอร์ต",
            "rates_other": "➕ คำขออื่นๆ\n\nสำหรับสกุลเงินอื่นหรือคำขอพิเศษ กรุณาติดต่อซัพพอร์ต",
            "rates_cash_bangkok": "🇹🇭 ค่าธรรมเนียม Bangkok THB\n\nเงินสด ↔ คริปโต: 2.5%\nอิงตามอัตราตลาด Bitkub\nต่ำกว่า 3,000 USD: ค่าธรรมเนียมขั้นต่ำ 75 USD\n\nราคาสุดท้ายจะได้รับการยืนยันโดยซัพพอร์ต",
            "rates_cash_paris": "🇫🇷 ค่าธรรมเนียม Paris EUR\n\nเงินสด ↔ คริปโต: 2%\nอิงตามอัตรา XE\nต่ำกว่า 5,000 EUR: ค่าธรรมเนียมขั้นต่ำ 100 EUR\n\nราคาสุดท้ายจะได้รับการยืนยันโดยซัพพอร์ต",
            "rates_cash_vegas": "🇺🇸 ค่าธรรมเนียม Las Vegas USD\n\nเงินสด ↔ คริปโต: 2%\nยอดขั้นต่ำ: 10,000 USD\n\nราคาสุดท้ายจะได้รับการยืนยันโดยซัพพอร์ต",
            "rates_cash_marrakech": "🇲🇦 ค่าธรรมเนียม Marrakech MAD\n\nสำหรับคำขอเงินสด MAD กรุณาติดต่อซัพพอร์ต",
        },
    }
    return texts.get(language, texts["en"])[key]


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        get_text("en", "welcome"),
        reply_markup=get_language_keyboard(),
    )


# =========================
# BACK LOGIC
# =========================

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = get_user_language(context)
    mode = context.user_data.get("mode")
    step = context.user_data.get("exchange_step")
    rates_step = context.user_data.get("rates_step")

    if mode == "rates":
        if rates_step == "cash":
            context.user_data["rates_step"] = "main"
            await update.message.reply_text(
                get_text(language, "choose_rates_category"),
                reply_markup=get_rates_category_keyboard(language),
            )
            return

        context.user_data["mode"] = None
        context.user_data["rates_step"] = None
        await update.message.reply_text(
            get_text(language, "use_menu"),
            reply_markup=get_main_menu_keyboard(language),
        )
        return

    if step == "send_method":
        context.user_data["mode"] = None
        context.user_data["exchange_step"] = None
        await update.message.reply_text(
            get_text(language, "use_menu"),
            reply_markup=get_main_menu_keyboard(language),
        )
        return

    if step == "send_details":
        context.user_data["exchange_step"] = "send_method"
        await update.message.reply_text(
            get_text(language, "exchange_send"),
            reply_markup=get_exchange_method_keyboard(language),
        )
        return

    if step == "receive_method":
        context.user_data["exchange_step"] = "send_details"
        await ask_method_details(update, context, context.user_data.get("exchange_send_method"), "send")
        return

    if step == "receive_details":
        context.user_data["exchange_step"] = "receive_method"
        await update.message.reply_text(
            get_text(language, "exchange_receive"),
            reply_markup=get_receive_method_keyboard(language),
        )
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
# EXCHANGE DETAIL ROUTING
# =========================

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

    if side == "send":
        context.user_data["exchange_step"] = "receive_method"
        await update.message.reply_text(
            get_text(language, "next_receive_method"),
            reply_markup=get_receive_method_keyboard(language),
        )
    else:
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
            context.user_data["exchange_step"] = "receive_method"
            await update.message.reply_text(
                get_text(language, "next_receive_method"),
                reply_markup=get_receive_method_keyboard(language),
            )
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
                context.user_data["exchange_step"] = "receive_method"
                await update.message.reply_text(
                    get_text(language, "next_receive_method"),
                    reply_markup=get_receive_method_keyboard(language),
                )
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
                context.user_data["exchange_step"] = "receive_method"
                await update.message.reply_text(
                    get_text(language, "next_receive_method"),
                    reply_markup=get_receive_method_keyboard(language),
                )
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
                context.user_data["exchange_step"] = "receive_method"
                await update.message.reply_text(
                    get_text(language, "next_receive_method"),
                    reply_markup=get_receive_method_keyboard(language),
                )
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


# =========================
# EXCHANGE FLOW
# =========================

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

    if step == "send_method":
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
        context.user_data["exchange_step"] = "send_details"
        await ask_method_details(update, context, selected_method, "send")
        return

    if step == "send_details":
        await handle_side_details(update, context, "send")
        return

    if step == "receive_method":
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
        context.user_data["exchange_step"] = "receive_details"
        await ask_method_details(update, context, selected_method, "receive")
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


# =========================
# SUPPORT / CUSTOM
# =========================

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


# =========================
# RATES FLOW
# =========================

async def handle_rates_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = get_user_language(context)
    user_text = update.message.text
    step = context.user_data.get("rates_step", "main")

    if is_back(user_text):
        await go_back(update, context)
        return

    if step == "main":
        category = normalize_rates_category(user_text)

        if not category:
            await update.message.reply_text(
                get_text(language, "choose_rates_category"),
                reply_markup=get_rates_category_keyboard(language),
            )
            return

        if category == "bank_transfer":
            await update.message.reply_text(
                get_text(language, "rates_bank_transfer"),
                reply_markup=get_rates_category_keyboard(language),
            )
            return

        if category == "paypal":
            await update.message.reply_text(
                get_text(language, "rates_paypal"),
                reply_markup=get_rates_category_keyboard(language),
            )
            return

        if category == "skrill":
            await update.message.reply_text(
                get_text(language, "rates_skrill"),
                reply_markup=get_rates_category_keyboard(language),
            )
            return

        if category == "other":
            await update.message.reply_text(
                get_text(language, "rates_other"),
                reply_markup=get_rates_category_keyboard(language),
            )
            return

        if category == "cash":
            context.user_data["rates_step"] = "cash"
            await update.message.reply_text(
                get_text(language, "choose_cash_rates_location"),
                reply_markup=get_cash_rates_keyboard(language),
            )
            return

    if step == "cash":
        location = normalize_cash_rates_location(user_text)

        if not location:
            await update.message.reply_text(
                get_text(language, "choose_cash_rates_location"),
                reply_markup=get_cash_rates_keyboard(language),
            )
            return

        if location == "bangkok_thb":
            await update.message.reply_text(
                get_text(language, "rates_cash_bangkok"),
                reply_markup=get_cash_rates_keyboard(language),
            )
            return

        if location == "paris_eur":
            await update.message.reply_text(
                get_text(language, "rates_cash_paris"),
                reply_markup=get_cash_rates_keyboard(language),
            )
            return

        if location == "vegas_usd":
            await update.message.reply_text(
                get_text(language, "rates_cash_vegas"),
                reply_markup=get_cash_rates_keyboard(language),
            )
            return

        if location == "marrakech_mad":
            await update.message.reply_text(
                get_text(language, "rates_cash_marrakech"),
                reply_markup=get_cash_rates_keyboard(language),
            )
            return


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

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

    if query.data == "lang_th":
        context.user_data["language"] = "th"
        context.user_data["mode"] = None
        await query.message.reply_text(
            get_text("th", "language_set"),
            reply_markup=get_main_menu_keyboard("th"),
        )
        return

    language = get_user_language(context)

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


# =========================
# TEXT HANDLER
# =========================

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

    if mode == "rates":
        await handle_rates_flow(update, context)
        return

    if user_text in ["💱 Exchange", "💱 Échange", "💱 Обмін"]:
        context.user_data["mode"] = "exchange"
        context.user_data["exchange_step"] = "send_method"
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
        context.user_data["mode"] = "rates"
        context.user_data["rates_step"] = "main"
        await update.message.reply_text(
            get_text(language, "choose_rates_category"),
            reply_markup=get_rates_category_keyboard(language),
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