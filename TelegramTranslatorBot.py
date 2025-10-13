import os
from datetime import datetime, timedelta, timezone
from telegram import (
    Update, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, PreCheckoutQueryHandler, CallbackQueryHandler
)

# ---------- CONFIG ----------
BOT_TOKEN = "8495660220:AAFSiuyEoyd0lagumIHe5Pz-rGjVLDIW4KI"
PREMIUM_CHANNEL_ID = int(os.getenv("PREMIUM_CHANNEL_ID", "-1000000000000"))
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

COURSE_TITLE = "STEP الشاملة الحديثة"
COURSE_DESC = "الدورة الأحدث لتأهيلك لاختبار STEP مع تحديثات مدى الحياة"
COURSE_PRICE_STARS = 1
INVITE_EXP_MINUTES = 10

# ---------- COMMANDS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    kb = [[InlineKeyboardButton("ℹ عن الدورة", callback_data="about")]]
    await update.message.reply_text(
        f"👋 أهلاً {user.first_name}!\n"
        f"مرحبًا بك في <b>{COURSE_TITLE}</b>.\n\n"
        f"📚 {COURSE_DESC}\n\n"
        f"اضغط للدفع داخل تيليجرام بالنجوم ✨",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode=ParseMode.HTML
    )

    # إرسال فاتورة نجوم XTR
    prices = [LabeledPrice(label="اشتراك دورة STEP", amount=COURSE_PRICE_STARS)]
    await update.message.reply_invoice(
        title=COURSE_TITLE,
        description=COURSE_DESC,
        provider_token="",      # فارغ للنجوم XTR
        currency="XTR",         # عملة النجوم
        prices=prices,
        payload="STEP_SUBSCRIPTION",
        start_parameter="stars"
    )

async def about_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "• شروحات مختصرة ومنظمة\n"
        "• تجميعات 2025 محدّثة\n"
        "• اختبارات تجريبية + ملفات PDF\n"
        "• تحديثات مدى الحياة + دعم داخل تيليجرام"
    )

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    expire_at = datetime.now(timezone.utc) + timedelta(minutes=INVITE_EXP_MINUTES)
    invite = await context.bot.create_chat_invite_link(
        chat_id=PREMIUM_CHANNEL_ID,
        name=f"STEP access for {user.id}",
        expire_date=expire_at,
        member_limit=1
    )

    await update.message.reply_text(
        "✅ تم الدفع بنجاح!\n"
        f"هذا رابط دخولك (صالح لدخول واحد ولمدة {INVITE_EXP_MINUTES} دقيقة):\n"
        f"{invite.invite_link}\n\n"
        "لو واجهتك مشكلة، اكتب هنا."
    )

    if ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"💰 اشتراك جديد: {user.mention_html()} (id={user.id})",
            parse_mode=ParseMode.HTML
        )

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("اكتب /start للبدء والدفع عبر النجوم ✨")

# ---------- MAIN ----------
def main():
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN environment variable is missing.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(about_cb, pattern="^about$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.COMMAND, fallback))

    print("🚀 Bot is running…")
    app.run_polling(allowed_updates=["message", "callback_query", "pre_checkout_query"])

if __name__ == "__main__":
    main()
