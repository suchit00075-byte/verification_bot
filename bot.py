import json
import os
from telegram import *
from telegram.ext import *

BOT_TOKEN = "8680097194:AAG_r66Ravn2LKUAWtEr9OuqmY6-SSIFnPU"
PROFESSOR_ID = 7209486623

BACKUP_CHANNEL = "https://t.me/uoscli"
CONTACT_REDIRECT = "https://t.me/Csewala_bot"

# ---------- DATABASE ----------

def load(file):
    if not os.path.exists(file):
        return {}
    with open(file,"r") as f:
        return json.load(f)

def save(file,data):
    with open(file,"w") as f:
        json.dump(data,f,indent=4)

users = load("users.json")
courses = load("courses.json")

# ---------- START ----------

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    uid = str(user.id)

    if uid not in users:
        users[uid] = {
            "name":user.first_name,
            "username":user.username,
            "phone":"",
            "verified":False,
            "backup":False,
            "courses":[]
        }
        save("users.json",users)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Verify Phone",callback_data="verify_phone")]
    ])

    await update.message.reply_text(
        "Welcome to Professor Course System\n\nStep 1: Verify Phone",
        reply_markup=keyboard
    )

# ---------- VERIFY PHONE ----------

async def verify_phone(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    button = KeyboardButton("Share Phone",request_contact=True)

    keyboard = ReplyKeyboardMarkup([[button]],resize_keyboard=True)

    await query.message.reply_text(
        "Share your phone number",
        reply_markup=keyboard
    )

# ---------- PHONE RECEIVED ----------

async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):

    contact = update.message.contact
    user = update.effective_user
    uid = str(user.id)

    # ---- FIX: user exist check ----
    if uid not in users:
        users[uid] = {
            "name": user.first_name,
            "username": user.username,
            "phone": "",
            "verified": False,
            "backup": False,
            "courses": []
        }

    users[uid]["phone"] = contact.phone_number
    users[uid]["verified"] = True

    save("users.json", users)

    await context.bot.send_message(
        PROFESSOR_ID,
        f"NEW VERIFIED USER\n\n"
        f"Name: {user.first_name}\n"
        f"Username: @{user.username}\n"
        f"ID: {user.id}\n"
        f"Phone: {contact.phone_number}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Backup Channel", url=BACKUP_CHANNEL)],
        [InlineKeyboardButton("I Joined", callback_data="backup_done")]
    ])

    await update.message.reply_text(
        "Phone verified successfully.\n\nNow join backup channel.",
        reply_markup=keyboard
    )

# ---------- BACKUP CONFIRM ----------

async def backup_done(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user
    uid = str(user.id)

    users[uid]["backup"] = True
    save("users.json",users)

    await context.bot.send_message(
        PROFESSOR_ID,
        f"User joined backup\n\n{user.first_name}\nID {user.id}"
    )

    await main_menu(query.message)

# ---------- MAIN MENU ----------

async def main_menu(message):

    keyboard = ReplyKeyboardMarkup(
        [
            ["📚 My Courses","📘 Available Courses"],
            ["💳 Payment","👨‍🏫 Contact Professor"]
        ],
        resize_keyboard=True
    )

    inline = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 My Courses",callback_data="my_courses")],
        [InlineKeyboardButton("📘 Available Courses",url=BACKUP_CHANNEL)],
        [InlineKeyboardButton("💳 Payment",callback_data="payment")],
        [InlineKeyboardButton("👨‍🏫 Contact Professor",url=CONTACT_REDIRECT)]
    ])

    await message.reply_text("Main Menu",reply_markup=keyboard)
    await message.reply_text("Quick Access",reply_markup=inline)

# ---------- MENU HANDLER ----------

async def menu_handler(update:Update,context:ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "📚 My Courses":
        await show_courses(update,context)

    elif text == "📘 Available Courses":
        await update.message.reply_text(
            f"Available Courses\n{BACKUP_CHANNEL}"
        )

    elif text == "💳 Payment":

        context.user_data["payment_mode"] = True

        await update.message.reply_text(
            "Send payment screenshot or gift card code."
        )

    elif text == "👨‍🏫 Contact Professor":

        await update.message.reply_text(
            CONTACT_REDIRECT
        )

# ---------- MY COURSES ----------

async def show_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.callback_query:

        query = update.callback_query
        await query.answer()

        uid = str(query.from_user.id)
        msg = query.message

    else:

        uid = str(update.message.from_user.id)
        msg = update.message

    if uid not in users:
        await msg.reply_text("User not found")
        return

    user_courses = users[uid]["courses"]

    if not user_courses:
        await msg.reply_text("No course assigned")
        return

    buttons = []

    for course in user_courses:

        if course in courses:

            link = courses[course]

            buttons.append(
                [InlineKeyboardButton(course, url=link)]
            )

    await msg.reply_text(
        "📚 Your Courses",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------- INLINE PAYMENT ----------

async def payment_inline(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["payment_mode"] = True

    await query.message.reply_text(
        "Send payment screenshot or code."
    )

# ---------- PAYMENT PROOF ----------

async def user_message(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if context.user_data.get("payment_mode"):

        await context.bot.send_message(
            PROFESSOR_ID,
            f"💳 PAYMENT RECEIVED\n\n"
            f"{user.first_name}\n"
            f"ID {user.id}"
        )

        await update.message.copy(PROFESSOR_ID)

        await update.message.reply_text(
            "Payment proof sent to Professor."
        )

        context.user_data["payment_mode"] = False

# ---------- PROFESSOR PANEL ----------

async def panel(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != PROFESSOR_ID:
        return

    await update.message.reply_text(
        "Professor Panel\n\n"
        "/setcourse name link\n"
        "/addcourse userid course\n"
        "/users\n"
        "/stats\n"
        "/broadcast message"
    )

# ---------- SET COURSE ----------

async def setcourse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != PROFESSOR_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Use:\n/setcourse COURSE_NAME LINK"
        )
        return

    name = context.args[0]
    link = context.args[1]

    courses[name] = link
    save("courses.json", courses)

    await update.message.reply_text(
        f"Course saved:\n{name}"
    )

# ---------- ADD COURSE ----------

async def addcourse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != PROFESSOR_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Use:\n/addcourse USERID COURSE_NAME"
        )
        return

    uid = context.args[0]
    course = context.args[1]

    if uid not in users:
        await update.message.reply_text("User not found")
        return

    if course not in courses:
        await update.message.reply_text("Course not set yet")
        return

    if course not in users[uid]["courses"]:
        users[uid]["courses"].append(course)

    save("users.json", users)

    await update.message.reply_text(
        f"Course {course} added to user {uid}"
    )

    await context.bot.send_message(
        uid,
        f"🎓 New Course Assigned\n\n{course}\n\nOpen My Courses."
    )

# ---------- USERS ----------

async def user_list(update:Update,context:ContextTypes.DEFAULT_TYPE):

    text=""

    for uid,data in users.items():
        text+=f"{uid} {data.get('phone','')}\n"

    await update.message.reply_text(text)

# ---------- STATS ----------

async def stats(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"Users:{len(users)}\nCourses:{len(courses)}"
    )

# ---------- BROADCAST ----------

async def broadcast(update:Update,context:ContextTypes.DEFAULT_TYPE):

    msg=" ".join(context.args)

    for uid in users:

        try:
            await context.bot.send_message(uid,msg)
        except:
            pass

# ---------- APP ----------

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("panel",panel))
app.add_handler(CommandHandler("setcourse",setcourse))
app.add_handler(CommandHandler("addcourse",addcourse))
app.add_handler(CommandHandler("users",user_list))
app.add_handler(CommandHandler("stats",stats))
app.add_handler(CommandHandler("broadcast",broadcast))

app.add_handler(CallbackQueryHandler(verify_phone,pattern="verify_phone"))
app.add_handler(CallbackQueryHandler(backup_done,pattern="backup_done"))
app.add_handler(CallbackQueryHandler(show_courses,pattern="my_courses"))
app.add_handler(CallbackQueryHandler(payment_inline,pattern="payment"))

app.add_handler(MessageHandler(filters.CONTACT,phone_received))

app.add_handler(MessageHandler(
    filters.Regex("^(📚 My Courses|📘 Available Courses|💳 Payment|👨‍🏫 Contact Professor)$"),
    menu_handler
))

app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, user_message))

print("BOT RUNNING")

app.run_polling(drop_pending_updates=True, timeout=60)