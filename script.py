import os
import logging
import random
import psycopg2

from dotenv import load_dotenv
from datetime import datetime
from telegram import Update, ForceReply, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from telegram.utils.helpers import escape_markdown


# settings
load_dotenv()
TOKEN = os.getenv("TOKEN")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


# /start
def start(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    username = user.username or user.first_name
    message = f"Привет, {escape_markdown(username)}\! Я могу предложить тебе книгу для чтения\. Напиши /help для начала\!"
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)


# function for get random book from db
def get_random_book() -> tuple:
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = connection.cursor()

    cursor.execute("SELECT id, title, author, genre, description FROM books ORDER BY RANDOM() LIMIT 1;")
    book = cursor.fetchone()

    cursor.close()
    connection.close()

    return book


# save book for historical data
def store_selected_book(book_id: int, selection_time: datetime) -> None:
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = connection.cursor()

    cursor.execute("INSERT INTO books_selected (book_id, selection_time) VALUES (%s, %s);", (book_id, selection_time))

    connection.commit()
    cursor.close()
    connection.close()


# function for read random boook
def recommend(update: Update, _: CallbackContext) -> None:
    book = get_random_book()
    if book:
        user = update.effective_user
        username = user.username or user.first_name
        id, title, author, genre, description = book
        description_with_backslash = description.replace('.', '\.')
        description_with_backslash = description_with_backslash.replace('-', '\.')
        message = f"Вот книга для тебя, {escape_markdown(username)}:\n\nНазвание: {title}\nАвтор: {author}\nЖанр: {genre}\nОписание: {description_with_backslash}"
        update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
        store_selected_book(book_id=book[0], selection_time=datetime.now())
    else:
        update.message.reply_text("К сожалению, не удалось найти подходящую книгу. Попробуйте позже.")


# get book by id
def get_book_by_id(book_id):
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = connection.cursor()

    query = "SELECT title, author, genre, description FROM books WHERE id = %s;"
    cursor.execute(query, (book_id,))
    book = cursor.fetchone()

    cursor.close()
    connection.close()

    return book


# get top 10 books
def get_top_10_books() -> list:
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = connection.cursor()

    cursor.execute("SELECT book_id, COUNT(id) FROM books_selected GROUP BY book_id ORDER BY COUNT(id) DESC LIMIT 10;")
    top_10_books = cursor.fetchall()

    cursor.close()
    connection.close()

    return top_10_books


# /top10
def top_10_books(update: Update, _: CallbackContext) -> None:
    top_books = get_top_10_books()
    if top_books:
        message = "Топ 10 книг, которые часто выбирали:\n\n"
        for i, (book_id, count) in enumerate(top_books, start=1):
            book = get_book_by_id(book_id) 
            if book:
                title = book[0]
                message += f"{i}. {title} - {count} раз\n"
            else:
                message += f"{i}. Книга с id {book_id} не найдена, но она была выбрана ранее {count} раз\n"
        update.message.reply_text(message)
    else:
        update.message.reply_text("К сожалению, пока нет данных для топ 10 книг.")


def help_command(update: Update, _: CallbackContext) -> None:
    help_message = (
        "Доступные команды:\n\n"
        "/start - Начать общение с ботом\n"
        "/help - Показать список доступных команд\n"
        "/recommend - Получить книгу рандомом\n"
        "/top10 - Вывод 10 часто выпадавших книг"
    )
    update.message.reply_text(help_message)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("recommend", recommend))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("top10", top_10_books)) 

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
