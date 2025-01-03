import os
import shutil
from aiogram import types
from config import AUDITS_DIR

def create_store_folder(store_name: str, date_str: str) -> str:
    safe_date_str = date_str.replace(':', '_')
    folder_path = os.path.join(AUDITS_DIR, f"{store_name}_{safe_date_str}")
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

async def save_photo(message: types.Message, folder_path: str, prefix: str) -> str:
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    file_path = os.path.join(folder_path, f"{prefix}_{len(os.listdir(folder_path)) + 1}.jpg")

    await message.bot.download(file, destination=file_path)
    return file_path

async def delete_store_folder(folder_path: str):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)

async def delete_photo(file_path: str) -> bool:
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        print(f"Ошибка при удалении фото: {str(e)}")
        return False

def scan_audits_folder(folder_path: str) -> list:
    audits = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            audits.append(item)
    return audits
