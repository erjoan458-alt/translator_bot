from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import ContextTypes
from database import get_services, get_service_by_id, add_order
from config import ADMIN_ID

# عرض قائمة الخدمات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services = get_services()
    if not services:
        await update.message.reply_text("لا توجد خدمات حالياً.")
        return

    kb = [[InlineKeyboardButton(f"{name} — {price} ريال", callback_data=f"order:{sid}")]
          for sid, name, desc, price in services]
    await update.message.reply_text("📦 اختر الخدمة:", reply_markup=InlineKeyboardMarkup(kb))

# طلب خدمة
async def order_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    sid = int(q.data.split(":")[1])
    service = get_service_by_id(sid)

    if not service:
        await q.edit_message_text("❌ الخدمة غير موجودة.")
        return

    _, name, desc, price = service
    await q.edit_message_text(
        f"🛍 <b>{name}</b>\n\n{desc}\n💰 السعر: {price} ريال سعودي\n\n"
        "📤 أرسل تفاصيل طلبك الآن (يمكنك إرفاق ملف أو كتابة شرح).",
        parse_mode="HTML"
    )
    context.user_data["awaiting_order"] = sid

# استلام تفاصيل الطلب
async def receive_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting_order" not in context.user_data:
        return

    sid = context.user_data.pop("awaiting_order")
    user = update.effective_user
    details = update.message.caption or update.message.text or "بدون تفاصيل"
    file_id = None

    if update.message.document:
        file_id = update.message.document.file_id

    add_order(user.id, user.username, sid, details, file_id)

    await update.message.reply_text("✅ تم استلام طلبك بنجاح وسيتم التواصل معك قريباً.")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📦 طلب جديد من @{user.username}\n\nالتفاصيل:\n{details}"
    )
