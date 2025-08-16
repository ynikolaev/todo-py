from aiogram.fsm.state import State, StatesGroup


class MenuDlg(StatesGroup):
    main = State()


class CategoryCreateDlg(StatesGroup):
    name = State()
    confirm = State()


class CategoryListDlg(StatesGroup):
    categories = State()
    edit = State()
    confirm_delete = State()


class CreateTaskDlg(StatesGroup):
    title = State()
    description = State()
    due_at = State()
    confirm = State()
