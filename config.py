import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "7781119850:AAHf4xK5q1EM8W-WCdLyR1CZSRs9az4Oqm4")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDITS_DIR = r"D:/Аудиты магазинов"
os.makedirs(AUDITS_DIR, exist_ok=True)
