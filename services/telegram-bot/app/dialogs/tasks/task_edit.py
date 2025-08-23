from aiogram_dialog import Dialog

from .task_form import on_edit_confirm, task_form_windows

dialog = Dialog(*task_form_windows(on_edit_confirm))
