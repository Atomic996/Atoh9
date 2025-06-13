import json import random import os from aiogram import Bot, Dispatcher, executor, types from aiogram.types import InputFile from aiogram.types.message import ContentType from config import TOKEN, MIN_TASKS_BEFORE_ADD

bot = Bot(token=TOKEN) dp = Dispatcher(bot)

DB_FILE = "database.json" SCREENSHOT_DIR = "screenshots" os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def load_db(): try: with open(DB_FILE, "r") as f: return json.load(f) except: return {}

def save_db(db): with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

@dp.message_handler(commands=['start']) async def start(message: types.Message): user_id = str(message.from_user.id) db = load_db() if user_id not in db: db[user_id] = { "submitted_task": None, "completed_tasks": [], "referrals": 0, "awaiting_screenshot_for": None } save_db(db) await message.answer("👋 مرحبًا بك في بوت تبادل الإحالات بالتحقق عبر Screenshot!\n\nاستخدم /get_task للحصول على مهمة.\nاستخدم /add_task لإضافة رابط إحالتك.\nاستخدم /done بعد تنفيذ المهمة وإرسال صورة.\nاستخدم /referrals لرؤية نتائجك.")

@dp.message_handler(commands=['add_task']) async def add_task(message: types.Message): user_id = str(message.from_user.id) db = load_db()

if len(db[user_id]["completed_tasks"]) < MIN_TASKS_BEFORE_ADD:
    return await message.answer(f"❌ يجب عليك إكمال {MIN_TASKS_BEFORE_ADD} مهمة قبل إضافة رابط إحالتك.")

if db[user_id]["submitted_task"]:
    return await message.answer("📌 لقد أضفت رابطك مسبقًا.")

await message.answer("🔗 أرسل الآن رابط الإحالة الخاص ببوتك (مثل https://t.me/MyBot?start=1234):")
db[user_id]["awaiting_link"] = True
save_db(db)

@dp.message_handler(lambda msg: msg.text.startswith("https://t.me/")) async def receive_task_link(message: types.Message): user_id = str(message.from_user.id) db = load_db()

if db.get(user_id, {}).get("awaiting_link"):
    db[user_id]["submitted_task"] = message.text.strip()
    db[user_id]["awaiting_link"] = False
    save_db(db)
    await message.answer("✅ تم حفظ رابط إحالتك! سيتم مشاركته مع مستخدمين آخرين.")
else:
    await message.answer("❗ هذا الرابط غير مطلوب الآن.")

@dp.message_handler(commands=['get_task']) async def get_task(message: types.Message): user_id = str(message.from_user.id) db = load_db() available = [uid for uid, data in db.items() if data["submitted_task"] and uid != user_id and uid not in db[user_id]["completed_tasks"]]

if not available:
    return await message.answer("😕 لا توجد مهام متاحة حاليًا، حاول لاحقًا.")

chosen_id = random.choice(available)
db[user_id]["current_task"] = chosen_id
db[user_id]["awaiting_screenshot_for"] = chosen_id
save_db(db)

task_link = db[chosen_id]["submitted_task"]
await message.answer(f"🎯 مهمتك:\nانضم إلى البوت التالي عبر الرابط:\n\n{task_link}\n\nثم اضغط /done وأرسل Screenshot بعد إتمام المهمة.")

@dp.message_handler(commands=['done']) async def done(message: types.Message): user_id = str(message.from_user.id) db = load_db()

task_owner = db[user_id].get("awaiting_screenshot_for")
if not task_owner:
    return await message.answer("❗ لا توجد مهمة نشطة حاليًا. استخدم /get_task أولاً.")

await message.answer("📸 أرسل الآن Screenshot من المحادثة مع البوت المُحال إليه.")

@dp.message_handler(content_types=ContentType.PHOTO) async def handle_screenshot(message: types.Message): user_id = str(message.from_user.id) db = load_db() task_owner = db[user_id].get("awaiting_screenshot_for")

if not task_owner:
    return await message.answer("❗ لا يُطلب منك الآن إرسال Screenshot.")

photo = message.photo[-1]  # أعلى جودة
filename = f"{SCREENSHOT_DIR}/{user_id}_{task_owner}.jpg"
await photo.download(destination_file=filename)

db[user_id]["completed_tasks"].append(task_owner)
db[task_owner]["referrals"] += 1
db[user_id]["current_task"] = None
db[user_id]["awaiting_screenshot_for"] = None
save_db(db)

await message.answer("✅ تم تسجيل Screenshot والمهمة كمنجزة بنجاح! استخدم /get_task لمهمة جديدة.")

@dp.message_handler(commands=['referrals']) async def referrals(message: types.Message): user_id = str(message.from_user.id) db = load_db() data = db.get(user_id, {}) await message.answer( f"📊 إحصائياتك:\n" f"🔗 رابطك: {data.get('submitted_task', 'لم يتم الإرسال')}\n" f"✅ مهام مكتملة: {len(data['completed_tasks'])}\n" f"👥 إحالات مستلمة: {data['referrals']}" )

