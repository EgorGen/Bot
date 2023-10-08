import requests
import io
import os
import asyncio
import logging
import pandas as pd
import sys
import keyboard as kb
from dotenv import load_dotenv
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher, types, F, Router, html
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputFile
from aiogram.filters import CommandStart
from aiogram.methods.send_document import SendDocument

load_dotenv()

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
data = None
form_router = Router()

class Form(StatesGroup):
   name = State()

@form_router.message(CommandStart())
async def send_welcome(message: Message):
   await message.answer("Привет! Задача бота заключается в отображении запроса из базы данных Excel. Отправте свой excel документ, чтоб его обработать",reply_markup=kb.main)

@form_router.message(F.document)
async def take_doc(message: Message, state: FSMContext):
   global data
   try:
      await message.answer('Подождите, загрузка файла может занять некоторое время')
      file_id  = message.document.file_id
      file = await bot.get_file(file_id)
      file_path = file.file_path
      my_object = io.BytesIO()
      MyBinaryIO = await bot.download_file(file_path, my_object)
      data = pd.read_excel(MyBinaryIO)
      await message.answer('Файл успешно загружен!')
   except Exception as e:
      await message.answer(f"Произошла ошибка при загрузке файла. {e}")
   return

@form_router.message(F.text == 'Показать список групп')
async def report(message: Message, state: FSMContext):
   if data is None:
      await message.answer('Вы не отправили документ для обработки!')
   else:
      grup = data['Группа'].unique()
      grup_str = ', '.join(grup)
      await message.answer(f'В  базе данных храниться информации таких групп как: {grup_str}')

@form_router.message(F.text == 'Выбрать группу')
async def report(message: Message, state: FSMContext) -> None:
   await state.set_state(Form.name)
   await message.answer("Введите номер группы: ")

@form_router.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
   if data is None:
      await message.answer('Вы не отправили документ для обработки!')
   else:
      await state.update_data(name=message.text)
      await message.answer(f"Номер вашей группы:  {html.quote(message.text)}")
      skore = data['Группа'].str.contains(str(message.text)).sum()
      if skore == 0:
         await message.answer(f'К сожалению по группе с таким номером нет данных.', reply_markup=kb.main)
      else:
         await message.answer(f'Если хотите получить отчет по группе: {html.quote(message.text)}. Нажмите кнопку отчет', reply_markup=kb.report1)

@dp.callback_query(F.data == 'otchet')
async def cbquantity(callback: CallbackQuery, state: FSMContext):
   if data is None:
      await callback.message.answer('Вы не отправили документ для обработки!')
   else:
      group = await state.get_data()
      last_row = data.shape[0]
      sсore = data['Группа'].str.contains(group['name']).sum()
      stud_PI101 = len(data[data['Группа'] == group['name']]['Личный номер студента'].unique())
      pi101 = data.loc[data['Группа']== group['name'] , 'Личный номер студента'].unique()
      pi101_str = ', '.join(map(str, pi101))
      control = data['Уровень контроля'].unique()
      control_str = ', '.join(map(str, control))
      years = sorted(data['Год'].unique())
      years_str = ', '.join(map(str, years))
      stud_PI101 = len(data[data['Группа'] == 'ПИ101']['Личный номер студента'].unique())
      await callback.message.answer(f'В исходном датасете содержалось {last_row} оценок, из них {sсore} относятся к группе {group["name"]}')
      await callback.message.answer(f'В датасете находятся оценки {stud_PI101} студентов со следующими личными номерами: {pi101_str}')
      await callback.message.answer(f'Используемые формы контроля: {control_str}')
      await callback.message.answer(f'Данные представлены по следующим учебным годам: {years_str}')

async def main():
   dp.include_router(form_router)
   await dp.start_polling(bot)

if __name__ == '__main__':
   logging.basicConfig(level=logging.INFO, stream=sys.stdout)
   asyncio.run(main()) 