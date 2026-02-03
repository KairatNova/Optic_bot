from aiogram.fsm.state import State, StatesGroup


# Для регистрации пользователя по номеру
class RegistrationStates(StatesGroup):
    waiting_for_phone = State()



# Для владельца — редактирование контента

class OwnerContentStates(StatesGroup):
    choosing_section = State()      # Выбор раздела для редактирования
    waiting_new_text = State()      # Ожидание нового текста