from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_services, add_service, delete_service, get_orders, update_order_status
from config import ADMIN_ID

# لوحة التحكم
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 7647281536:
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    kb = [
        [InlineKeyboardButton("➕ إضافة خدمة", callback_data="add_service")],
        [InlineKeyboardButton("📋 قائمة الخدمات", callback_data="list_services")],
        [InlineKeyboardButton("📦 الطلبات", callback_data="list_orders")]
    ]
    await update.message.reply_text("⚙️ لوحة الإدارة:", reply_markup=InlineKeyboardMarkup(kb))

# عرض الخدمات
async def list_services_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    services = get_services()
    if not services:
        await q.edit_message_text("لا توجد خدمات حالياً.")
        return

    text = "📋 الخدمات الحالية:\n\n"
    kb = []
    for sid, name, desc, price in services:
        text += f"• <b>{name}</b>\n{desc}\n💰 السعر: {price} ريال\n\n"
        kb.append([InlineKeyboardButton(f"❌ حذف {name}", callback_data=f"del_service:{sid}")])

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

# حذف خدمة
async def del_service_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    sid = int(q.data.split(":")[1])
    delete_service(sid)
    await q.edit_message_text("✅ تم حذف الخدمة.")

# عرض الطلبات
async def list_orders_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    orders = get_orders()
    if not orders:
        await q.edit_message_text("لا توجد طلبات حالياً.")
        return

    text = "🧾 الطلبات:\n\n"
    kb = []
    for oid, username, sname, status, ts in orders:
        text += f"طلب #{oid} من @{username}\nخدمة: {sname}\n📅 {ts}\nالحالة: {status}\n\n"
        kb.append([
            InlineKeyboardButton("✅ مكتمل", callback_data=f"status:{oid}:مكتمل"),
            InlineKeyboardButton("⚙️ قيد التنفيذ", callback_data=f"status:{oid}:قيد التنفيذ")
        ])

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

# تحديث حالة الطلب
async def update_status_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, oid, new_status = q.data.split(":")
    update_order_status(oid, new_status)
    await q.answer("تم التحديث ✅")
    await q.edit_message_text("✅ تم تغيير حالة الطلب.")
