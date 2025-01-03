from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import InputFile
from states import AuditStates
from excel_handler import create_excel_file, append_defect_to_excel
from utils import create_store_folder, save_photo, delete_store_folder, delete_photo, scan_audits_folder
from help_text import HELP_TEXT  # Импортируем текст помощи
import os
from config import AUDITS_DIR, BOT_TOKEN
from aiogram import Bot

bot = Bot(token=BOT_TOKEN)

def register_handlers(dp):
    dp.message.register(start_audit, Command("start"))
    dp.message.register(clear_audit, Command("clear"))
    dp.message.register(stop_audit, Command("stop"))
    dp.message.register(stat_audits, Command("stat"))  # Обработчик для команды /stat
    dp.message.register(help_command, Command("help"))  # Обработчик для команды /help
    dp.message.register(process_name, AuditStates.waiting_for_name)
    dp.message.register(process_store_name, AuditStates.waiting_for_store_name)
    dp.message.register(process_address, AuditStates.waiting_for_address)
    dp.message.register(process_facade_photo, AuditStates.waiting_for_facade_photos)  # Обработчик для фото фасада
    dp.message.register(process_delete_facade_photo, AuditStates.waiting_for_delete_facade_photo)  # Обработчик для удаления фото фасада
    dp.message.register(process_defect_photo, AuditStates.waiting_for_photos)  # Обработчик для фото дефектов
    dp.message.register(process_defect_type, AuditStates.waiting_for_defect_type)
    dp.message.register(process_defect_description, AuditStates.waiting_for_defect_description)
    dp.message.register(process_work_needed, AuditStates.waiting_for_work_needed)
    dp.message.register(process_electric_panel_photo, AuditStates.waiting_for_electric_panel_photos)
    dp.message.register(process_electric_meter_photo, AuditStates.waiting_for_electric_meter_photos)
    dp.message.register(process_water_meter_photo, AuditStates.waiting_for_water_meter_photos)
    dp.message.register(process_continue_audit, F.text.in_(["Продолжить аудит", "Закончить аудит", "Счетчики"]))
    dp.message.register(process_meter_type, AuditStates.waiting_for_meter_type)

async def start_audit(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, введите ваше ФИО:")
    await state.set_state(AuditStates.waiting_for_name)

async def clear_audit(message: types.Message, state: FSMContext):
    await delete_store_folder(AUDITS_DIR)
    await message.reply("Все данные удалены. Начните новый аудит с командой /start.")
    await state.clear()

async def stop_audit(message: types.Message, state: FSMContext):
    await message.reply("Аудит прерван.", reply_markup=types.ReplyKeyboardRemove())
    await state.clear()

async def stat_audits(message: types.Message):
    audits = scan_audits_folder(AUDITS_DIR)
    if audits:
        audits_list = "\n".join(f"{idx}. {audit}" for idx, audit in enumerate(audits, start=1))
        await message.reply(f"Список аудитов магазинов:\n{audits_list}")
    else:
        await message.reply("Аудиты магазинов не найдены.")

async def help_command(message: types.Message):
    await message.reply(HELP_TEXT)

async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.reply("Введите название магазина:")
    await state.set_state(AuditStates.waiting_for_store_name)

async def process_store_name(message: types.Message, state: FSMContext):
    await state.update_data(store_name=message.text.strip())
    await message.reply("Введите адрес магазина:")
    await state.set_state(AuditStates.waiting_for_address)

async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    date_str = message.date.strftime("%d_%m_%Y")  # Изменено на подчеркивания
    data = await state.get_data()
    store_name = data['store_name']

    folder_path = create_store_folder(store_name, date_str)
    excel_path = create_excel_file(folder_path, data['name'], store_name, message.text.strip(), date_str)

    await state.update_data(folder_path=folder_path, excel_path=excel_path, date_str=date_str)

    await message.reply("Загрузите фото фасада магазина (мин. 1 фото, макс. 5 фото):")
    await state.set_state(AuditStates.waiting_for_facade_photos)

async def process_facade_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    facade_photos_path = os.path.join(data['folder_path'], "Фасад")

    if message.photo:
        file_path = await save_photo(message, facade_photos_path, "Фасад")
        if file_path:
            facade_photos = os.listdir(facade_photos_path)
            if len(facade_photos) > 5:
                await message.reply("Вы превысили лимит фото фасада. Пожалуйста, удалите одно из фото:", reply_markup=get_delete_facade_photo_keyboard(facade_photos))
                await state.set_state(AuditStates.waiting_for_delete_facade_photo)
            else:
                await message.reply("Фото фасада сохранено. Выберите дальнейшее действие:", reply_markup=get_continue_keyboard())
                await state.set_state(AuditStates.waiting_for_continue_audit)
        else:
            await message.reply("Произошла ошибка при сохранении фото. Попробуйте еще раз.")
    else:
        await message.reply("Пожалуйста, отправьте фото фасада.")

async def process_delete_facade_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    facade_photos_path = os.path.join(data['folder_path'], "Фасад")

    if message.text in os.listdir(facade_photos_path):
        file_path = os.path.join(facade_photos_path, message.text)
        if await delete_photo(file_path):
            await message.reply("Фото фасада удалено. Загрузите новое фото фасада или выберите дальнейшее действие:", reply_markup=get_continue_keyboard())
            await state.set_state(AuditStates.waiting_for_continue_audit)
        else:
            await message.reply("Произошла ошибка при удалении фото. Попробуйте еще раз.")
    else:
        await message.reply("Пожалуйста, выберите фото для удаления.")

def get_delete_facade_photo_keyboard(facade_photos):
    keyboard_buttons = [[types.KeyboardButton(text=photo)] for photo in facade_photos]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True
    )
    return keyboard

async def process_defect_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if message.photo:
        file_path = await save_photo(message, os.path.join(data['folder_path'], "Дефекты"), "Дефект")
        if file_path:
            await message.reply("Выберите тип дефекта:", reply_markup=get_defect_type_keyboard())
            await state.set_state(AuditStates.waiting_for_defect_type)
        else:
            await message.reply("Произошла ошибка при сохранении фото. Попробуйте еще раз.")
    else:
        await message.reply("Пожалуйста, отправьте фото дефекта.")

def get_defect_type_keyboard():
    buttons = ["Механический", "Электрический","Здания и сооружения","Отопление", "Вентиляция","Канализация","ХО","Вспом.оборудование","Охр.сигнализаци","Пож.сигнализация"]
    keyboard_buttons = [[types.KeyboardButton(text=button)] for button in buttons]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True
    )
    return keyboard

async def process_defect_type(message: types.Message, state: FSMContext):
    await state.update_data(defect_type=message.text)
    await message.reply("Опишите выявленный дефект:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AuditStates.waiting_for_defect_description)

async def process_defect_description(message: types.Message, state: FSMContext):
    await state.update_data(defect_description=message.text)
    await message.reply("Какие работы необходимо выполнить, какие материалы затратить?")
    await state.set_state(AuditStates.waiting_for_work_needed)

async def process_work_needed(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if 'excel_path' not in data:
        await message.reply("Ошибка: Путь к файлу Excel не найден. Пожалуйста, начните аудит заново.")
        await state.clear()
        return

    if message.text not in ["Продолжить аудит", "Закончить аудит", "Счетчики"]:
        try:
            append_defect_to_excel(
                data['excel_path'],
                len(os.listdir(os.path.join(data['folder_path'], "Дефекты"))),
                data['defect_type'],
                data['defect_description'],
                message.text
            )
            await message.reply("Дефект записан. Выберите дальнейшее действие:", reply_markup=get_continue_keyboard())
        except Exception as e:
            await message.reply(f"Произошла ошибка при записи данных в Excel: {str(e)}")
    else:
        await process_continue_audit(message, state)

def get_continue_keyboard():
    buttons = ["Продолжить аудит", "Закончить аудит", "Счетчики"]
    keyboard_buttons = [[types.KeyboardButton(text=button)] for button in buttons]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True
    )
    return keyboard

async def process_continue_audit(message: types.Message, state: FSMContext):
    if message.text == "Закончить аудит":
        await message.reply("Аудит завершен.", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
    elif message.text == "Продолжить аудит":
        await message.reply("Загрузите следующее фото дефекта:")
        await state.set_state(AuditStates.waiting_for_photos)
    elif message.text == "Счетчики":
        await message.reply("Выберите тип счетчика:", reply_markup=get_meter_type_keyboard())
        await state.set_state(AuditStates.waiting_for_meter_type)

def get_meter_type_keyboard():
    buttons = ["Фото электрического счетчика", "Фото счетчика воды"]
    keyboard_buttons = [[types.KeyboardButton(text=button)] for button in buttons]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True
    )
    return keyboard

async def process_meter_type(message: types.Message, state: FSMContext):
    if message.text == "Фото электрического счетчика":
        await message.reply("Загрузите фото электрического счетчика:")
        await state.set_state(AuditStates.waiting_for_electric_meter_photos)
    elif message.text == "Фото счетчика воды":
        await message.reply("Загрузите фото счетчика воды:")
        await state.set_state(AuditStates.waiting_for_water_meter_photos)

async def process_electric_panel_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if message.photo:
        folder_name = f"Счетчики_{data['store_name']}_{data['date_str']}"
        file_path = await save_photo(message, os.path.join(data['folder_path'], folder_name), "ЭЩУ")
        if file_path:
            await message.reply("Фото ЭЩУ сохранено. Выберите дальнейшее действие:", reply_markup=get_continue_keyboard())
            await state.set_state(AuditStates.waiting_for_continue_audit)
        else:
            await message.reply("Произошла ошибка при сохранении фото. Попробуйте еще раз.")
    else:
        await message.reply("Пожалуйста, отправьте фото ЭЩУ.")

async def process_electric_meter_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if message.photo:
        folder_name = f"Счетчики_{data['store_name']}_{data['date_str']}"
        file_path = await save_photo(message, os.path.join(data['folder_path'], folder_name), "Электрический_счетчик")
        if file_path:
            await message.reply("Фото электрического счетчика сохранено. Выберите дальнейшее действие:", reply_markup=get_continue_keyboard())
            await state.set_state(AuditStates.waiting_for_continue_audit)
        else:
            await message.reply("Произошла ошибка при сохранении фото. Попробуйте еще раз.")
    else:
        await message.reply("Пожалуйста, отправьте фото электрического счетчика.")

async def process_water_meter_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if message.photo:
        folder_name = f"Счетчики_{data['store_name']}_{data['date_str']}"
        file_path = await save_photo(message, os.path.join(data['folder_path'], folder_name), "Счетчик_воды")
        if file_path:
            await message.reply("Фото счетчика воды сохранено. Выберите дальнейшее действие:", reply_markup=get_continue_keyboard())
            await state.set_state(AuditStates.waiting_for_continue_audit)
        else:
            await message.reply("Произошла ошибка при сохранении фото. Попробуйте еще раз.")
    else:
        await message.reply("Отправьте фото счетчика воды.")
