from aiogram.fsm.state import State, StatesGroup

class AuditStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_store_name = State()
    waiting_for_address = State()
    waiting_for_facade_photos = State()  # Состояние для ожидания фото фасада
    waiting_for_delete_facade_photo = State()  # Состояние для ожидания удаления фото фасада
    waiting_for_photos = State()
    waiting_for_defect_type = State()
    waiting_for_defect_description = State()
    waiting_for_work_needed = State()
    waiting_for_electric_panel_photos = State()
    waiting_for_water_meter_photos = State()
    waiting_for_electric_meter_photos = State()
    waiting_for_meter_type = State()
    waiting_for_continue_audit = State()
