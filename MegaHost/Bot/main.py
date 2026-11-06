print('[START] Version: 1.0')

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict
import random
import os

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder, KeyboardButton, InlineKeyboardButton

from database import *
from settings import *


logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)
router = Router()

last_no_user_bots_time = {}

# Словарь для хранения сообщений
messages_to_edit = {}

last_click_times: Dict[int, float] = {}

class AdminState(StatesGroup):
    waiting_for_user_id_add_stars = State()
    waiting_for_stars_amount_add = State()
    waiting_for_user_id_remove_stars = State()
    waiting_for_stars_amount_remove = State()
    waiting_for_mailing_text = State()
    waiting_for_channel_id_add = State()
    waiting_for_channel_id_delete = State()
    waiting_for_promocode_activation = State()
    waiting_for_promo_details_add = State()
    waiting_for_promocode_delete = State()
    waiting_for_user_blocked = State()





def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🤖Мои юзер-боты")
    builder.button(text="💳 Купить юзер-бота")
    builder.row(
        KeyboardButton(text='👤Профиль')
    )
    builder.row(
        KeyboardButton(text="❓Помощь")
    )
    return builder.as_markup(resize_keyboard=True)



# Интерфейс бота и прочее
@router.message(StateFilter(AdminState.waiting_for_user_id_add_stars))
async def process_add_stars_user_id(message: types.Message, state: FSMContext):
    await state.update_data(user_id_add_stars=message.text)
    await bot.send_message(message.chat.id, "<b>Введите количество звезд для добавления:</b>", parse_mode='HTML')
    await state.set_state(AdminState.waiting_for_stars_amount_add)

@router.message(StateFilter(AdminState.waiting_for_stars_amount_add))
async def process_add_stars_amount(message: types.Message, state: FSMContext):
    try:
        stars = int(message.text)
        data = await state.get_data()
        user_id = int(data.get("user_id_add_stars"))
        increment_stars(user_id, stars)
        await bot.send_message(message.chat.id, f"<b>✅ {stars} звезд успешно добавлено пользователю с ID {user_id}</b>", parse_mode='HTML')
        await bot.send_message(user_id, f"✅ Администратор добавил вам {stars} звезд!", parse_mode='HTML')
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Неверный формат. Пожалуйста, введите число.</b>", parse_mode='HTML')
    except TypeError:
        await bot.send_message(message.chat.id, "<b>❌ Неверный формат ID.</b>", parse_mode='HTML')
    await state.clear()

@router.message(StateFilter(AdminState.waiting_for_user_id_remove_stars))
async def process_remove_stars_user_id(message: types.Message, state: FSMContext):
    await state.update_data(user_id_remove_stars=message.text)
    await bot.send_message(message.chat.id, "<b>Введите количество звезд для удаления:</b>", parse_mode='HTML')
    await state.set_state(AdminState.waiting_for_stars_amount_remove)

@router.message(StateFilter(AdminState.waiting_for_stars_amount_remove))
async def process_remove_stars_amount(message: types.Message, state: FSMContext):
    try:
        stars = int(message.text)
        data = await state.get_data()
        user_id = int(data.get("user_id_add_stars"))
        deincrement_stars(user_id, stars)
        await bot.send_message(message.chat.id, "<b>✅ Звезды успешно удалены!</b>", parse_mode='HTML')
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Неверный формат. Пожалуйста, введите число.</b>", parse_mode='HTML')
    except TypeError:
        await bot.send_message(message.chat.id, "<b>❌ Неверный формат ID.</b>", parse_mode='HTML')
    await state.clear()

@router.message(StateFilter(AdminState.waiting_for_mailing_text))
async def process_mailing_text(message: types.Message, state: FSMContext):
    text = message.text
    users = get_users()
    counter = 0

    for user in users:
        user_id = user[0]
        ref_link = f"\n\nПерешли ссылку всем своим друзьям — https://t.me/{ (await bot.me()).username }?start={user_id}"
        full_text = f"{text}{ref_link}"

        try:
            counter += 1
            await bot.send_message(user_id, f"<b>{full_text}</b>", parse_mode='HTML')
            print(f"[РАССЫЛКА] Отправлено: {user_id}")
        except Exception as e:
            print(f"[РАССЫЛКА] Не отправлено: {user_id}")

    await bot.send_message(message.chat.id, f"<b>✅ Рассылка успешно отправлена!\n\nОтправлено: {counter}/{str(len(users))} пользователю</b>", parse_mode='HTML')
    await state.clear()

@router.message(StateFilter(AdminState.waiting_for_channel_id_add))
async def process_add_channel_id(message: types.Message, state: FSMContext):
    try:
        channel_id_to_add = int(message.text)
        if channel_id_to_add not in channel_ids:
            channel_ids.append(channel_id_to_add)
            await bot.send_message(message.chat.id, "<b>✅ Канал успешно добавлен!</b>", parse_mode='HTML')
        else:
            await bot.send_message(message.chat.id, "<b>⚠️ Этот канал уже есть в списке.</b>", parse_mode='HTML')
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Некорректный ID канала!</b>", parse_mode='HTML')
    await state.clear()

@router.message(StateFilter(AdminState.waiting_for_channel_id_delete))
async def process_delete_channel_id(message: types.Message, state: FSMContext):
    try:
        channel_id_to_delete = int(message.text)
        if channel_id_to_delete in channel_ids:
            channel_ids.remove(channel_id_to_delete)
            await bot.send_message(message.chat.id, "<b>✅ Канал успешно удален!</b>", parse_mode='HTML')
        else:
            await bot.send_message(message.chat.id, "<b>❌ Канал не найден!</b>", parse_mode='HTML')
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Некорректный ID канала!</b>", parse_mode='HTML')
    await state.clear()

@router.message(StateFilter(AdminState.waiting_for_promocode_activation))
async def process_promocode_activation(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    promocode = message.text
    success, result = use_promocode(promocode, user_id)
    if success:
        await bot.send_message(message.chat.id, f"<b>✅ Промокод успешно активирован!\nВам начислено {result} ⭐️</b>", parse_mode='HTML')
    else:
        await bot.send_message(message.chat.id, f"<b>❌ Ошибка: {result}</b>", parse_mode='HTML')
    await state.clear()

@router.message(StateFilter(AdminState.waiting_for_promo_details_add))
async def process_add_promo_details(message: types.Message, state: FSMContext):
    try:
        promocode, stars_str, uses_str = message.text.split(",")
        stars = int(stars_str.strip())
        uses = int(uses_str.strip())
        add_promocode(promocode.strip(), stars, uses)
        await bot.send_message(message.chat.id, "<b>✅ Промокод успешно добавлен!</b>", parse_mode='HTML')
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Некорректный ввод! Введите промокод, количество звезд, количество использований через запятую.</b>", parse_mode='HTML')
    await state.clear()

@router.message(StateFilter(AdminState.waiting_for_promocode_delete))
async def process_delete_promo(message: types.Message, state: FSMContext):
    try:
        promocode = message.text.strip()
        deactivate_promocode(promocode)
        await bot.send_message(message.chat.id, "<b>✅ Промокод успешно удален!</b>", parse_mode='HTML')
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Некорректный ввод!</b>", parse_mode='HTML')
    await state.clear()


@router.message(CommandStart())
async def handle_start(message: types.Message, bot: Bot):
    args = message.text.split()
    user_id = message.from_user.id
    username = message.from_user.username or f"User{user_id}"
    ref_link = f"https://t.me/{ (await bot.me()).username }?start={user_id}"


    builder = InlineKeyboardBuilder()
    builder.button(text="Поделиться ссылкой", url=f"https://t.me/share/url?url={ref_link}")
    markup = builder.as_markup()

    start_command = BotCommand(command='start', description='♻️ Перезапустить бота')
    await bot.set_my_commands([start_command])
    await bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=types.MenuButtonCommands()
    )

    if not user_exists(user_id):
        referral_id = None
        if len(channel_ids) > 0:
            if await check_subscription(user_id, channel_ids, bot):
                return
        if len(args) > 1 and args[1].isdigit():
            referral_id = int(args[1])
            if user_exists(referral_id):
                await bot.send_message(referral_id, f"<b>☑️ Найден пользователь приглашенный вами в бота!\nПри каждой покупке вам будет начисляться 10% от его траты!\n\nПерешли ссылку — {ref_link}</b>", parse_mode='HTML')
                await bot.send_message(admins, text=f"Новый пользователь! рефер: {referral_id}, пользователь: {user_id}", parse_mode='HTML')
                increment_referrals(referral_id)
        add_user(user_id, username, referral_id)
        add_user_creat_ub(user_id)
        await bot.send_message(user_id, "💻", reply_markup=get_main_keyboard())
        await bot.send_message(user_id, f"<b>💻Добро пожаловать в 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™!💻\nЗдесь вы можете приобретать, управлять вашими юзер-ботами 🖥️.\n\nЧто вы получите:\n - ✨Понятное управление вашим юзер-ботом!\n - ✨Поддержку при появлении трудностей\n - ✨Доступные цены</b>", parse_mode='HTML')
    else:
        if len(channel_ids) > 0:
            if await check_subscription(user_id, channel_ids, bot):
                return
        await bot.send_message(user_id, "💻", reply_markup=get_main_keyboard())
        await bot.send_message(user_id, f"<b>💻Добро пожаловать в 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™!💻\nЗдесь вы можете приобретать, управлять вашими юзер-ботами 🖥️.\n\nЧто вы получите:\n - ✨Понятное управление вашим юзер-ботом!\n - ✨Поддержку при появлении трудностей\n - ✨Доступные цены</b>", parse_mode='HTML', reply_markup=markup)

@router.message(Command("admin"))
async def adminpanel_command(message: types.Message, bot: Bot):
    if message.from_user.id in admins:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="⭐️ Выдать рубли", callback_data="add_stars"),
            InlineKeyboardButton(text="⭐️ Снять рубли", callback_data="remove_stars")
        )
        builder.row(
            InlineKeyboardButton(text="📨 Рассылка", callback_data="mailing")
        )
        builder.row(
            InlineKeyboardButton(text="📚 Добавить канал", callback_data="add_channel"),
            InlineKeyboardButton(text="🚫 Удалить канал", callback_data='delete_channel')
        )
        builder.row(
            InlineKeyboardButton(text="📨 Рассылка 0 реф", callback_data='mailing_zero_refs')
        )
        builder.row(
            InlineKeyboardButton(text="🎁 Добавить промокод", callback_data='add_promo_code'),
            InlineKeyboardButton(text="🚫 Удалить промокод", callback_data='remove_promo_code')
        )
        markup = builder.as_markup()
        await bot.send_message(message.chat.id, f"<b>📊 Админ-панель\n\n👥 Пользователей: {get_user_count()}</b>", parse_mode='HTML', reply_markup=markup)

@router.message()
async def handle_reply_buttons(message: types.Message, bot: Bot):
    global kypit_user_bot_message
    user_id = message.from_user.id
    ref_link = f"https://t.me/{ (await bot.me()).username }?start={user_id}"
    username = message.from_user.username or f"User{user_id}"
    if message.text == "🤖Мои юзер-боты":
        user_hikka = get_hikka(user_id)
        user_heroku = get_heroku(user_id)
        if user_hikka:
            hikka = user_hikka[5]
            heroku = user_heroku[6]
            if hikka == 0:
                if heroku == 0:
                    # Получаем текущее время
                    current_time = time.time()
                    if user_id in last_no_user_bots_time:
                        # Вычисляем промежуток времени с последнего нажатия
                        elapsed_time = current_time - last_no_user_bots_time[user_id]
                        if elapsed_time <= 2:
                            await bot.send_message(user_id,
                                                   text="❗️Не спамьте, попробуйте еще раз через несколько секунд❗️")
                            return

                    await bot.send_message(user_id, text= '⚠️У вас не приобретенных юзер-ботов! Приобретите один из юзер-ботов и попробуйте еще раз⚠️')
                elif heroku == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="🪐Heroku", callback_data='heroku')
                    )
                    markup = builder.as_markup()
                    await bot.send_message(user_id, text='📱Ваши юзер-боты:', reply_markup=markup)
            elif hikka == 1:
                if heroku == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="🌘Hikka", callback_data='hikka')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🪐Heroku", callback_data='heroku')
                    )
                    markup = builder.as_markup()
                    await bot.send_message(user_id, text="📱Ваши юзер-боты:", reply_markup=markup)
                elif heroku == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="🌘Hikka", callback_data='hikka')
                    )
                    markup = builder.as_markup()
                    await bot.send_message(user_id, text="Ваши юзер-боты:", reply_markup=markup)
    else:
        if len(channel_ids) > 0:
            if await check_subscription(user_id, channel_ids, bot):
                return
    if message.text == "💳 Купить юзер-бота":
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="⚡️Тарифы", callback_data='tarif'),
            InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
        )
        builder.row(
            InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
        )
        builder.row(
            InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
            InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
        )
        markup = builder.as_markup()
        sent_message = await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
        messages_to_edit['original'] = sent_message.message_id
    else:
        if len(channel_ids) > 0:
            if await check_subscription(user_id, channel_ids, bot):
                return
    if message.text == "👤Профиль":
        user_data = get_user(user_id)
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🎁Бонус", callback_data='bonus_ejed')
        )
        builder.row(
            InlineKeyboardButton(text="💳Пополнить баланс", callback_data='pop_balance')
        )
        markup = builder.as_markup()
        if user_data:
            stars = user_data[2]
            count_refs = user_data[3]
            await bot.send_message(user_id, text=f"Ваш профиль:\n\nID: {user_id}\nUsername: @{username}\n\nБаланс: {stars}\n🔗Приглашено пользователей: {count_refs}\n\n𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™︎", reply_markup=markup)
    else:
        if len(channel_ids) > 0:
            if await check_subscription(user_id, channel_ids, bot):
                return
    if message.text == "❓Помощь":
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🌐Поддержка", url='https://t.me/ABTOSOUND')
        )
        markup = builder.as_markup()
        await bot.send_message(user_id, text="👋Приветствую в разделе помощь👋\n\nЗаметили ошибку❓ Появились трудности❓ Хотите задать вопрос❓ Пишите к нам в поддержку!", reply_markup=markup)
    else:
        if len(channel_ids) > 0:
            if await check_subscription(user_id, channel_ids, bot):
                return
@router.callback_query()
async def handle_stars_callback(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username
    user_data = get_user(user_id)
    user_creat_ub = get_creat_ub(user_id)
    if call.data == 'hikka':
        user_server_hikka = get_server_hikka(user_id)
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✨Продлить тариф", callback_data='prodlenie_tarifa_hikka')
        )
        builder.row(
            InlineKeyboardButton(text="⬆️Перенос", callback_data='perenos_hikka')
        )
        builder.row(
            InlineKeyboardButton(text="🛑Удалить юзер-бот с хостинга", callback_data='delete_hikka')
        )
        markup = builder.as_markup()
        if user_server_hikka:
            server = user_server_hikka[7]
            if server == 1:
                await bot.send_message(user_id, text=f"Userbot: 🌘Hikka\nСервер: 🇱🇷USA-1\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™", reply_markup=markup)
            elif server == 2:
                await bot.send_message(user_id, text=f"Userbot: 🌘Hikka\nСервер: 🇱🇷USA-2\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™",
                                       reply_markup=markup)
            elif server == 3:
                await bot.send_message(user_id, text=f"Userbot: 🌘Hikka\nСервер: 🇱🇷USA-3\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™",
                                       reply_markup=markup)
            elif server == 4:
                await bot.send_message(user_id, text=f"Userbot: 🌘Hikka\nСервер: 🇩🇪DE-1\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™",
                                       reply_markup=markup)
            elif server == 5:
                await bot.send_message(user_id, text=f"Userbot: 🌘Hikka\nСервер: 🇩🇪DE-2\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™",
                                       reply_markup=markup)
            elif server == 6:
                await bot.send_message(user_id, text=f"Userbot: 🌘Hikka\nСервер: 🇩🇪DE-3\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™",
                                       reply_markup=markup)
    if call.data == 'delete_hikka':
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅Да", callback_data="yes_delete_hikka"),
            InlineKeyboardButton(text="❌Нет", callback_data="no_delete_hikka")
        )
        markup = builder.as_markup()
        await bot.send_message(user_id, text="Вы уверены что хотите удалить юзер-бот с хостинга?", reply_markup=markup)
    if call.data == 'yes_delete_hikka':
        add_server_hikka(user_id, 0)
        minus_hikka(user_id)
        name_hikka = f'Hikka_{user_id}'
        hikka = search_hikka(name_hikka)

    if call.data == 'heroku':
        user_server_heroku = get_server_heroku(user_id)
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✨Продлить тариф", callback_data='prodlenie_tarifa_heroku')
        )
        builder.row(
            InlineKeyboardButton(text="⬆️Перенос", callback_data='perenos_heroku')
        )
        builder.row(
            InlineKeyboardButton(text="🛑Удалить юзер-бот с хостинга", callback_data='delete_heroku')
        )
        markup = builder.as_markup()
        if user_server_heroku:
            server = user_server_heroku[7]
            if server == 1:
                await bot.send_message(user_id, text=f"Userbot: 🪐Heroku\nСервер: 🇱🇷USA-1\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™", reply_markup=markup)
            elif server == 2:
                await bot.send_message(user_id, text=f"Userbot: 🪐Heroku\nСервер: 🇱🇷USA-2\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™",
                                       reply_markup=markup)
            elif server == 3:
                await bot.send_message(user_id, text=f"Userbot: 🪐Heroku\nСервер: 🇱🇷USA-3\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™",
                                       reply_markup=markup)
            elif server == 4:
                await bot.send_message(user_id, text=f"Userbot: 🪐Heroku\nСервер: 🇩🇪DE-1\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™",
                                       reply_markup=markup)
            elif server == 5:
                await bot.send_message(user_id, text=f"Userbot: 🪐Heroku\nСервер: 🇩🇪DE-2\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™",
                                       reply_markup=markup)
            elif server == 6:
                await bot.send_message(user_id, text=f"Userbot: 🪐Heroku\nСервер: 🇩🇪DE-3\nID владельца: {user_id}\nHosting: 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™",
                                       reply_markup=markup)

    if call.data == 'creat_ub':
        user_creat_ub = get_creat_ub(user_id)
        if user_creat_ub:
            tarif = user_creat_ub[1]
            obraz = user_creat_ub[2]
            server = user_creat_ub[3]
            if tarif == 1:
                if obraz == 1:
                    if server == 1:
                        if user_data:
                            stars = user_data[2]
                            if stars < 40:
                                od = 40 - stars
                                await bot.send_message(user_id, text=f"У вас недостаточно рублей на балансе для покупки юзер-бота. Пополните баланс на {od} рублей чтобы продолжить.")
                            elif stars >= 40:
                                deincrement_stars(user_id, 40)
                                await bot.send_message(user_id, text="✅Подождите ваш юзер-бот создается!✅")
                                hikka_path_name = ['hikka 1', 'hikka 2', 'hikka 3', 'hikka hikka', 'hikka hikka', 'hikka hikka', 'hikka 7', 'hikka 8', 'hikka 9', 'hikka 10', 'hikka 11', 'hikka 12', 'hikka 13', 'hikka 14', 'hikka 15', 'hikka 16', 'hikka 17', 'hikka 18', 'hikka 19', 'hikka 20']
                                hikka = search_hikka(hikka_path_name)
                                if 'hikka 1' in hikka:
                                    name_hikka = 'hikka 1'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    hikka_path = f'{new_path}/hikka'
                                    new_hikka_path = f'{new_path}/Hikka_{user_id}'
                                    os.rename(hikka_path, new_hikka_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 2' in hikka:
                                    name_hikka = 'hikka 2'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 3' in hikka:
                                    name_hikka = 'hikka 3'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka hikka' in hikka:
                                    name_hikka = 'hikka hikka'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka hikka' in hikka:
                                    name_hikka = 'hikka hikka'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka hikka' in hikka:
                                    name_hikka = 'hikka hikka'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 7' in hikka:
                                    name_hikka = 'hikka 7'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 8' in hikka:
                                    name_hikka = 'hikka 8'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 9' in hikka:
                                    name_hikka = 'hikka 9'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 10' in hikka:
                                    name_hikka = 'hikka 10'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 11' in hikka:
                                    name_hikka = 'hikka 11'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 12' in hikka:
                                    name_hikka = 'hikka 12'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 13' in hikka:
                                    name_hikka = 'hikka 13'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 14' in hikka:
                                    name_hikka = 'hikka 14'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 15' in hikka:
                                    name_hikka = 'hikka 15'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 16' in hikka:
                                    name_hikka = 'hikka 16'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 17' in hikka:
                                    name_hikka = 'hikka 17'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 18' in hikka:
                                    name_hikka = 'hikka 18'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 19' in hikka:
                                    name_hikka = 'hikka 19'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                elif 'hikka 20' in hikka:
                                    name_hikka = 'hikka 20'
                                    old_path = f'./Userbots/Hikka/{name_hikka}'
                                    new_path = f'./Userbots/Hikka/Hikka_{user_id}'
                                    # Переименовываем папку
                                    os.rename(old_path, new_path)
                                    add_hikka(user_id)
                                    add_server_hikka(user_id, 1)
                                    # duration = 10  # длительность таймера в секундах
                                    # await main_action(message)
                                    # start_time = time.time()
                                    #
                                    # async def run_timer():
                                    #     nonlocal start_time
                                    #     while True:
                                    #         elapsed_time = time.time() - start_time
                                    #         remaining_time = max(duration - int(elapsed_time), 0)
                                    #
                                    #         if remaining_time > 0:
                                    #             if remaining_time % 2 == 0:
                                    #                 await check_time_remaining(remaining_time, message.chat.id)
                                    #
                                    #             await asyncio.sleep(1)
                                    #         else:
                                    #             break
                                    #
                                    #     await final_action(message.chat.id)
                                    #
                                    # task = asyncio.create_task(run_timer())
                                    # await state.set_data({"timer_task": task})

                                else:
                                    await bot.send_message(admins, text="⚠️Внимание⚠️\nПереключение между серверами!\nВызвано: поиск свободных сессий хикки")


    if call.data == 'tarif':
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽 | 1 месяц - 40 рублей", callback_data="standart_tarif")
        )
        builder.row(
            InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮 | 2 месяца - 75 рублей", callback_data="lite_tarif")
        )
        markup = builder.as_markup()
        if 'original' in messages_to_edit:
            original_message_id = messages_to_edit.get('original')
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=original_message_id,
                text="Выберите тариф:",
                reply_markup=markup
            )
    if call.data == 'standart_tarif':
        add_tarif_ub_add(user_id, 1)
        if user_creat_ub:
            obraz = user_creat_ub[2]
            server = user_creat_ub[3]
            if obraz == 0:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif obraz == 1:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif obraz == 2:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
    if call.data == 'lite_tarif':
        add_tarif_ub_add(user_id, 2)
        if user_creat_ub:
            obraz = user_creat_ub[2]
            server = user_creat_ub[3]
            if obraz == 0:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif obraz == 1:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif obraz == 2:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)

    if call.data == 'user_bot_obraz':
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🌘Hikka", callback_data='obraz_hikka')
        )
        builder.row(
            InlineKeyboardButton(text="🪐Heroku", callback_data='obraz_heroku')
        )
        markup = builder.as_markup()
        if 'original' in messages_to_edit:
            original_message_id = messages_to_edit.get('original')
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=original_message_id,
                text="Выберите образ:",
                reply_markup=markup
            )
        # await bot.send_message(user_id, text="Выберите образ:", reply_markup=markup)
    if call.data == 'obraz_hikka':
        add_ub_obraz(user_id, 1)
        if user_creat_ub:
            tarif = user_creat_ub[1]
            server = user_creat_ub[3]
            if tarif == 0:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 1:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 2:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
    if call.data == 'obraz_heroku':
        add_ub_obraz(user_id, 2)
        if user_creat_ub:
            tarif = user_creat_ub[1]
            server = user_creat_ub[3]
            if tarif == 0:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 1:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 2:
                if server == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️Сервер", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 3:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 4:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 5:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif server == 6:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)

    if call.data == 'server':
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🇱🇷USA-1", callback_data='usa_1')
        )
        builder.row(
            InlineKeyboardButton(text="🇱🇷USA-2", callback_data='usa_2')
        )
        builder.row(
            InlineKeyboardButton(text="🇱🇷USA-3", callback_data='usa_3')
        )
        builder.row(
            InlineKeyboardButton(text="🇩🇪DE-1", callback_data='de_1')
        )
        builder.row(
            InlineKeyboardButton(text="🇩🇪DE-2", callback_data='de_2')
        )
        builder.row(
            InlineKeyboardButton(text="🇩🇪DE-3", callback_data='de_3')
        )
        markup_server = builder.as_markup()
        if 'original' in messages_to_edit:
            original_message_id = messages_to_edit.get('original')
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=original_message_id,
                text="Выберите сервер:",
                reply_markup=markup_server
            )
        # await bot.send_message(user_id, text="Выберите сервер:", reply_markup=markup_server)
    if call.data == 'usa_1':
        add_server_ub_add(user_id, 1)
        if user_creat_ub:
            tarif = user_creat_ub[1]
            obraz = user_creat_ub[2]
            if tarif == 0:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 1:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 2:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
    if call.data == 'usa_2':
        add_server_ub_add(user_id, 2)
        if user_creat_ub:
            tarif = user_creat_ub[1]
            obraz = user_creat_ub[2]
            if tarif == 0:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 1:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 2:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
    if call.data == 'usa_3':
        add_server_ub_add(user_id, 3)
        if user_creat_ub:
            tarif = user_creat_ub[1]
            obraz = user_creat_ub[2]
            if tarif == 0:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 1:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 2:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️USA-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
    if call.data == 'de_1':
        add_server_ub_add(user_id, 4)
        if user_creat_ub:
            tarif = user_creat_ub[1]
            obraz = user_creat_ub[2]
            if tarif == 0:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 1:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 2:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-1", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
    if call.data == 'de_2':
        add_server_ub_add(user_id, 5)
        if user_creat_ub:
            tarif = user_creat_ub[1]
            obraz = user_creat_ub[2]
            if tarif == 0:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 1:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 2:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-2", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
    if call.data == 'de_3':
        add_server_ub_add(user_id, 6)
        if user_creat_ub:
            tarif = user_creat_ub[1]
            obraz = user_creat_ub[2]
            if tarif == 0:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️Тариф", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 1:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓢𝓽𝓪𝓷𝓭𝓪𝓻𝓽", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
            elif tarif == 2:
                if obraz == 0:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🤖Юзер-бот", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 1:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🌘Hikka", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)
                elif obraz == 2:
                    builder = InlineKeyboardBuilder()
                    builder.row(
                        InlineKeyboardButton(text="⚡️𝓛𝓲𝓽𝓮", callback_data='tarif'),
                        InlineKeyboardButton(text="🪐Heroku", callback_data='user_bot_obraz')
                    )
                    builder.row(
                        InlineKeyboardButton(text="🖥️DE-3", callback_data='server')
                    )
                    builder.row(
                        InlineKeyboardButton(text="✅Создать юзер-бот", callback_data='creat_ub'),
                        InlineKeyboardButton(text="❌Отмена", callback_data="otmena_add_ub")
                    )
                    markup = builder.as_markup()
                    if 'original' in messages_to_edit:
                        original_message_id = messages_to_edit.get('original')
                        await bot.edit_message_text(
                            chat_id=user_id,
                            message_id=original_message_id,
                            text="Меню создания:",
                            reply_markup=markup
                        )
                    # await bot.send_message(user_id, text="Меню создания:", reply_markup=markup)

    if call.data == 'otmena_add_ub':
        add_server_ub_add(user_id, 0)
        add_ub_obraz(user_id, 0)
        add_tarif_ub_add(user_id, 0)
        await bot.answer_callback_query(call.id, text="Действие отменено")
        user_data = get_user(user_id)
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🎁Бонус", callback_data='bonus_ejed')
        )
        builder.row(
            InlineKeyboardButton(text="💳Пополнить баланс", callback_data='pop_balance')
        )
        markup = builder.as_markup()
        if user_data:
            stars = user_data[2]
            count_refs = user_data[3]
            if 'original' in messages_to_edit:
                original_message_id = messages_to_edit.get('original')
                await bot.edit_message_text(chat_id=user_id,
                                            message_id=original_message_id,
                                            text=f"Ваш профиль:\n\nID: {user_id}\nUsername: @{username}\n\nБаланс: {stars}\n🔗Приглашено пользователей: {count_refs}\n\n𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™︎",
                                            reply_markup=markup)

    if call.data == 'bonus_ejed':
        # Функция для вывода точного количества часов, минут и секунд
        def format_remaining_time(remaining_seconds: float) -> str:
            hours = int(remaining_seconds // 3600)
            minutes = int((remaining_seconds % 3600) // 60)
            seconds = int(remaining_seconds % 60)
            return f"{hours}часов {minutes}минут {seconds}секунд"
        current_time = datetime.now().timestamp()

        if user_id in last_click_times and current_time - last_click_times[user_id] <= 86400:
            remaining_seconds = round(86400 - (current_time - last_click_times[user_id]))
            formatted_time = format_remaining_time(remaining_seconds)
            await bot.answer_callback_query(call.id, f"Следующий бонус будет доступен через {formatted_time}.", show_alert=True)
        else:
            # Записываем новое время нажатия
            last_click_times[user_id] = current_time
            prize = [1, 0.5, 0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 1, 0.5, 0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 1, 0.5, 0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 1, 0.5, 0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 1, 0.5, 0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9]
            random_prize = random.choice(prize)
            increment_stars(user_id, random_prize)
            await bot.answer_callback_query(call.id, f"Вы получили ежедневный бонус! На ваш баланс начислено {random_prize}")


    if call.data == 'pop_balance':
        await bot.send_message(user_id, text="💢На данный момент пополнение находиться в разработке, но вы можете пополнить баланс через админа.")
    if user_data:
        stars = user_data[2]
        if call.data in ['15', '25', '50', '100', '150', '350', '500']:
            if int(call.data) > stars:
                await bot.answer_callback_query(call.id, "❌ У вас недостаточно звезд для вывода!", show_alert=True)
            else:
                await bot.answer_callback_query(call.id, "✅ Заявка на вывод звезд успешно отправлена!", show_alert=True)
                withdraw_stars(user_id, int(call.data))
                for admin in admins:
                    await bot.send_message(admin, f"<b>✅ Cоздан запрос на вывод\n\n👤 Пользователь @{username} | {user_id} \n💫 Количество: <code>{int(call.data)}</code>⭐️ </b>", parse_mode='HTML')
    if call.data == "add_stars":
        await bot.send_message(user_id, "<b>Введите ID пользователя:</b>", parse_mode='HTML')
        await state.set_state(AdminState.waiting_for_user_id_add_stars)
    if call.data == "remove_stars":
        await bot.send_message(user_id, "<b>Введите ID пользователя:</b>", parse_mode='HTML')
        await state.set_state(AdminState.waiting_for_user_id_remove_stars)
    if call.data == "mailing":
        await bot.send_message(user_id, "<b>Введите текст для рассылки:</b>", parse_mode='HTML')
        await state.set_state(AdminState.waiting_for_mailing_text)
    if call.data == "add_channel":
        await bot.send_message(user_id, "<b>Введите ID канала:</b>", parse_mode='HTML')
        await state.set_state(AdminState.waiting_for_channel_id_add)
    if call.data == 'delete_channel':
        await bot.send_message(user_id, "<b>Введите ID канала:</b>", parse_mode='HTML')
        await state.set_state(AdminState.waiting_for_channel_id_delete)
    if call.data == 'mailing_zero_refs':
        text = "⁉️🤨Мы заметили, что вы не пригласили ни 1 друга!\n\nПерешли ссылку своим друзьям, а также по чатам, 3 ⭐️ за 1 приглашенного⤵️"
        users = get_user_zero_referrals()

        for user in users:
            user_id = user[0]
            ref_link = f"\n\nТвоя персональная ссылка — https://t.me/{ (await bot.me()).username }?start={user_id}"
            full_text = f"{text}{ref_link}"

            try:
                await bot.send_message(user_id, f"<b>{full_text}</b>", parse_mode='HTML')
                print(f"[РАССЫЛКА 1.0] Отправлено: {user_id}")
            except Exception as e:
                print(f"[РАССЫЛКА 1.0] Не отправлено: {user_id}")

        await bot.send_message(call.message.chat.id, "<b>✅ Рассылка успешно отправлена!</b>", parse_mode='HTML')
    if call.data == "check_subs":
        if await check_subscription(user_id, channel_ids, bot):
            await bot.send_message(user_id, "<b>⚠️ Подпишитесь на каналы, чтобы продолжить!</b>", parse_mode='HTML')
        else:
            reff_link = f"https://t.me/{ (await bot.me()).username }?start={user_id}"
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="Поделиться ссылкой", url="https://t.me/share/url?url=" + reff_link)
            )
            markup = builder.as_markup()
            await bot.send_message(user_id, "💻", reply_markup=get_main_keyboard())
            await bot.send_message(user_id, f"<b>✨ Добро пожаловать в 𝓜𝓮𝓰𝓪𝓗𝓸𝓼𝓽™!\n\nРаспространяй свою ссылку и получай 10% от их трат в этом боте!\n\n🔗 Ваша ссылка - {reff_link}</b>", parse_mode='HTML', reply_markup=markup)
    if call.data == "promocode":
        await bot.send_message(user_id, "<b>🎄 Введите промокод:</b>", parse_mode='HTML')
        await state.set_state(AdminState.waiting_for_promocode_activation)
    if call.data == "add_promo_code":
        await bot.send_message(user_id, "<b>Введите промокод, количество звезд, количество использований через запятую:</b>", parse_mode='HTML')
        await state.set_state(AdminState.waiting_for_promo_details_add)
    if call.data == "delete_promo_code":
        await bot.send_message(user_id, "<b>Введите промокод:</b>", parse_mode='HTML')
        await state.set_state(AdminState.waiting_for_promocode_delete)
    await call.answer()

async def check_subscription(user_id, channel_ids, bot: Bot):
    if not channel_ids:
        return True

    builder = InlineKeyboardBuilder()
    show_join_button = False
    for channel_id in channel_ids:
        try:
            chat_member = await bot.get_chat_member(channel_id, user_id)
            if chat_member.status not in ['member', 'administrator', 'creator', 'restricted']:
                invite_link = (await bot.create_chat_invite_link(channel_id, member_limit=1)).invite_link
                builder.button(text="Подписаться", url=invite_link)
                show_join_button = True
        except Exception as e:
            print(f"Ошибка при проверке подписки: {e}")
            await bot.send_message(user_id, "⚠️Ошибка при проверке подписки⚠️. Пожалуйста, попробуйте позже.")
            return False

    if show_join_button:
        builder.row(
            InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subs")
        )
        markup = builder.as_markup()
        await bot.send_message(user_id, "<b>👋🏻 Добро пожаловать\n\nПодпишитесь на каналы, чтобы продолжить!</b>", parse_mode='HTML', reply_markup=markup)
        return True

    return False

def search_hikka(target_folders):
    # Путь к директории, которую будем сканировать
    path = 'Userbots/Hikka'

    # Список найденных папок
    found_folders = []

    for folder_name in target_folders:
        # Полностью путь к искомой папке
        full_path = os.path.join(path, folder_name)

        if os.path.exists(full_path) and os.path.isdir(full_path):
            found_folders.append(folder_name)

    return found_folders




dp.include_router(router)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    from handlers.ignore_blocked import ignore_blocked_messages
    ignore_blocked_messages(dp)
    executor.start_polling(dp, skip_updates=True)