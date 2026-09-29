from aiogram.fsm.state import State, StatesGroup


class LoginState(StatesGroup):
    username = State()
    password = State()

class AddTaskState(StatesGroup):
    title = State()
    description = State()
    priority = State()
    deadline = State()

class AIPlanState(StatesGroup):
    goal = State()
    days = State()
    number_of_tasks = State()
    preview = State()

class EditTaskState(StatesGroup):
    title = State()
    description = State()
    priority = State()
    deadline = State()

class AIReplanState(StatesGroup):
    days = State()
    instruction = State()
    preview = State()