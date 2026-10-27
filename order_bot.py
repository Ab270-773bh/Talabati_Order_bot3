import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)

# ====== إعدادات المحل (عدّلها لكل زبون) ======
TOKEN = os.environ["BOT_TOKEN"]          8795564106:AAEq_0pYEKkAIbfQZcQJHq_aR6VFqdwSdMI
OWNER_ID = int(os.environ["OWNER_ID"])   8859887860
SHOP_NAME = "مطعم الشام"
CURRENCY = "$"
MENU = {
    "shawarma": ("شاورما دجاج", 3.0),
    "burger": ("برغر لحم", 4.0),
    "falafel": ("ساندويش فلافل", 1.5),
    "fries": ("بطاطا مقلية", 1.5),
    "cola": ("مشروب غازي", 1.0),
}
# ============================================


def cart_text(cart: dict) -> str:
    if not cart:
        return "🛒 السلة فاضية"
    lines, total = [], 0.0
    for key, qty in cart.items():
        name, price = MENU[key]
        lines.append(f"• {name} × {qty} = {price * qty:g}{CURRENCY}")
        total += price * qty
    lines.append(f"\n💰 المجموع: {total:g}{CURRENCY}")
    return "🛒 سلتك:\n" + "\n".join(lines)


def menu_markup() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{name} — {price:g}{CURRENCY}", callback_data=f"add:{key}")]
        for key, (name, price) in MENU.items()
    ]
    rows.append(
        [
            InlineKeyboardButton("✅ إتمام الطلب", callback_data="checkout"),
            InlineKeyboardButton("🗑 تفريغ السلة", callback_data="clear"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def screen(cart: dict) -> str:
    return f"أهلاً فيك في {SHOP_NAME} 🌟\nاختار من القائمة:\n\n{cart_text(cart)}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cart"] = {}
    context.user_data["awaiting"] = False
    await update.message.reply_text(screen({}), reply_markup=menu_markup())


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    cart = context.user_data.setdefault("cart", {})
    data = query.data

    if data.startswith("add:"):
        key = data.split(":", 1)[1]
        if key in MENU:
            cart[key] = cart.get(key, 0) + 1
        await query.answer("انضافت للسلة ✅")
    elif data == "clear":
        cart.clear()
        context.user_data["awaiting"] = False
        await query.answer("تم تفريغ السلة")
    elif data == "checkout":
        if not cart:
            await query.answer("السلة فاضية، اختار شي أول", show_alert=True)
            return
        context.user_data["awaiting"] = True
        await query.answer()
        await query.message.reply_text(
            "تمام 👌 ابعتلي برسالة وحدة:\nاسمك + رقم تلفونك + عنوانك"
        )
        return

    try:
        await query.edit_message_text(screen(cart), reply_markup=menu_markup())
    except BadRequest:
        pass  # ما تغيّر شي بالرسالة


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting"):
        await update.message.reply_text("اكتب /start لتشوف القائمة 📋")
        return

    cart = context.user_data.get("cart", {})
    user = update.effective_user
    order = (
        f"🔔 طلب جديد!\n"
        f"من: {user.full_name} (@{user.username or 'بدون يوزر'})\n\n"
        f"{cart_text(cart)}\n\n"
        f"📞 بيانات الزبون:\n{update.message.text}"
    )
    await context.bot.send_message(chat_id=OWNER_ID, text=order)
    await update.message.reply_text(
        "وصل طلبك ✅ رح نتواصل معك قريب. شكراً لك 🌹\n\nلطلب جديد اكتب /start"
    )
    context.user_data["cart"] = {}
    context.user_data["awaiting"] = False


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling()


if __name__ == "__main__":
    main()
