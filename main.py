import os
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, PreCheckoutQueryHandler, ConversationHandler
)
from config import *
from database import init_db
from services import add_service, get_all_services, get_service, delete_service
from orders import create_order, get_all_orders

# Initialize database
init_db()

# Conversation states
ADDING_SERVICE_NAME, ADDING_SERVICE_DESC, ADDING_SERVICE_PRICE = range(3)

# ===========================
# User Commands
# ===========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    kb = [[InlineKeyboardButton("🛍️ عرض الخدمات", callback_data="show_services")]]
    await update.message.reply_text(
        f"👋 مرحباً {user.first_name}!\n"
        f"مرحباً بك في بوت الخدمات 💼\n"
        f"يمكنك اختيار الخدمة والدفع بالنجوم ✨",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ===========================
# عرض الخدمات
# ===========================
async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    services = get_all_services()

    if not services:
        await q.answer("🚫 لا توجد خدمات حالياً", show_alert=True)
        return

    kb = []
    for s in services:
        kb.append([InlineKeyboardButton(f"{s[1]} - {s[3]} ريال سعودي", callback_data=f"order_{s[0]}")])
    await q.message.reply_text("اختر الخدمة التي ترغب بها:", reply_markup=InlineKeyboardMarkup(kb))
    await q.answer()

# ===========================
# طلب الخدمة
# ===========================
async def order_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    service_id = int(q.data.split("_")[1])
    context.user_data["service_id"] = service_id
    await q.message.reply_text("📝 أرسل تفاصيل الطلب (يمكنك أيضاً إرفاق ملف أو صورة).")
    await q.answer()

# استقبال تفاصيل الطلب أو الملفات
async def receive_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service_id = context.user_data.get("service_id")
    if not service_id:
        return

    details = context.user_data.get("details", "")
    file_info = None

    if update.message.text:
        details += "\n" + update.message.text
    elif update.message.photo:
        file_info = update.message.photo[-1].file_id
        details += "\n🖼 صورة مرفقة"
    elif update.message.document:
        file_info = update.message.document.file_id
        details += f"\n📎 ملف مرفق: {update.message.document.file_name}"
    elif update.message.voice:
        file_info = update.message.voice.file_id
        details += "\n🎤 ملاحظة صوتية"

    context.user_data["details"] = details
    if file_info:
        context.user_data["file_id"] = file_info

    s = get_service(service_id)
    price = int(float(s[3]))  # convert to smallest unit (e.g. cents)

    await update.message.reply_invoice(
        title=s[1],
        description=s[2],
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=CURRENCY,
        prices=[LabeledPrice(label=s[1], amount=price)],
        payload=f"order_{service_id}"
    )

# ===========================
# الدفع
# ===========================
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    payload = update.message.successful_payment.invoice_payload
    service_id = int(payload.split("_")[1])
    details = context.user_data.get("details", "بدون تفاصيل")

    create_order(user.id, service_id, details)
    await update.message.reply_text("✅ تم الدفع بنجاح! سيتم التواصل معك قريباً.")

    # إشعار الأدمن
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🆕 طلب جديد من {user.mention_html()} لخدمة رقم {service_id}\n💬 التفاصيل:\n{details}",
        parse_mode=ParseMode.HTML
    )

    # إرسال الملف إن وجد
    file_id = context.user_data.get("file_id")
    if file_id:
        try:
            await context.bot.send_document(chat_id=ADMIN_ID, document=file_id)
        except Exception as e:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ لم يتم إرسال المرفق: {e}")

# ===========================
# إدارة الأدمن
# ===========================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    kb = [
        [InlineKeyboardButton("➕ إضافة خدمة", callback_data="add_service")],
        [InlineKeyboardButton("🗑 حذف خدمة", callback_data="delete_service")],
        [InlineKeyboardButton("📦 عرض الطلبات", callback_data="show_orders")]
    ]
    await update.message.reply_text("⚙️ لوحة تحكم الأدمن:", reply_markup=InlineKeyboardMarkup(kb))

# ===========================
# إدارة الخدمات (إضافة / حذف)
# ===========================
async def add_service_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📝 أرسل اسم الخدمة:")
    return ADDING_SERVICE_NAME

async def add_service_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("✏️ أرسل وصف الخدمة:")
    return ADDING_SERVICE_DESC

async def add_service_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("💰 أرسل سعر الخدمة (بالريال):")
    return ADDING_SERVICE_PRICE

async def add_service_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = float(update.message.text)
    add_service(context.user_data["name"], context.user_data["description"], price)
    await update.message.reply_text("✅ تمت إضافة الخدمة بنجاح.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END

async def delete_service_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    services = get_all_services()
    if not services:
        await q.answer("🚫 لا توجد خدمات", show_alert=True)
        return
    kb = [[InlineKeyboardButton(s[1], callback_data=f"confirm_delete_{s[0]}")] for s in services]
    await q.message.reply_text("اختر الخدمة لحذفها:", reply_markup=InlineKeyboardMarkup(kb))
    await q.answer()

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    service_id = int(q.data.split("_")[2])
    delete_service(service_id)
    await q.message.reply_text("🗑 تم حذف الخدمة بنجاح.")
    await q.answer()

# ===========================
# عرض الطلبات
# ===========================
async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    orders = get_all_orders()
    if not orders:
        await q.answer("🚫 لا توجد طلبات حالياً", show_alert=True)
        return
    text = "📦 <b>قائمة الطلبات:</b>\n\n"
    for o in orders:
        text += f"🆔 {o[0]} | 👤 {o[1]} | 🧾 خدمة {o[2]} | 💬 {o[3]} | 🟡 {o[4]}\n\n"
    await q.message.reply_text(text, parse_mode=ParseMode.HTML)
    await q.answer()

# ===========================
# MAIN
# ===========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_service_start, pattern="^add_service$")],
        states={
            ADDING_SERVICE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_name)],
            ADDING_SERVICE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_desc)],
            ADDING_SERVICE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(add_conv)
    app.add_handler(CallbackQueryHandler(show_services, pattern="^show_services$"))
    app.add_handler(CallbackQueryHandler(order_service, pattern="^order_"))
    app.add_handler(CallbackQueryHandler(delete_service_list, pattern="^delete_service$"))
    app.add_handler(CallbackQueryHandler(confirm_delete, pattern="^confirm_delete_"))
    app.add_handler(CallbackQueryHandler(show_orders, pattern="^show_orders$"))

    # ✅ Fixed filters line for PTB 20.6
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO | filters.ATTACHMENT | filters.VOICE) & ~filters.COMMAND,
        receive_order
    ))

    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    print("🚀 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
