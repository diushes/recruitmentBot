import telebot
from telebot import types

bot = telebot.TeleBot("6846229743:AAEkhJ7o9q_-lgPTO7Dojh2E525-FyKGJ84")
questions = [
    "Имя",
    "Возраст",
    "Последнее место работы",
    "Ник в телеграме",
    "Претендуемая позиция",
    "Резюме",
]

notion_token = "secret_RPZhkqHjgIMcnhwvZ6qVTbxnVdCo8FaVWaM263RiqNw"
notion_page_id = "b12ecd3b08b344f3808481d95388ee46"
notion_database_id = "0d4eff9ba2eb4d5f8fa2d83f433f94cc"


position_options = ["Проектный менеджер", "Офис-менеджер", "Ассистент"]
position_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
position_keyboard.add(*position_options)

user_answers = {}
users_awaiting_review = {}

# Keyboard for reviewing answers
review_keyboard = types.InlineKeyboardMarkup(row_width=2)
review_keyboard.add(
    types.InlineKeyboardButton(text="Отправить тестовое задание", callback_data="Тест"),
    types.InlineKeyboardButton(text="Отклонить", callback_data="Отклонить"),
)


@bot.message_handler(commands=["start"])
def start_recruitment(message):
    bot.send_message(
        message.chat.id,
        "Вас приветствует Макбучная!\nВы можете ознакомиться с доступными вакансиями, а также узнать подробнее о компании по ссылке ниже:\nhttps://www.notion.so/macbookbro/b93138587ea84dad87e9b145ab614110?pvs=4",
    )
    bot.send_message(
        message.chat.id,
        "Теперь, если вы готовы приступить к подаче заявки, просим ответить на несколько наших вопросов!",
    )
    ask_question(message, 0)


def ask_question(message, question_number):
    if question_number < len(questions):
        if questions[question_number] == "Претендуемая позиция":
            bot.send_message(
                message.chat.id,
                questions[question_number],
                reply_markup=position_keyboard,
            )
            bot.register_next_step_handler(message, save_answer, question_number)
        else:
            bot.send_message(message.chat.id, questions[question_number])
            bot.register_next_step_handler(message, save_answer, question_number)
    else:
        send_answers(message.chat.id)


def save_answer(message, question_number):
    user_id = message.from_user.id
    if user_id not in user_answers:
        user_answers[user_id] = {}

    if questions[question_number] == "Претендуемая позиция":
        # Remove the keyboard after the candidate selects an option
        bot.send_message(
            message.chat.id,
            "Спасибо за ответ!",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    # handle position options
    elif questions[question_number] == "Резюме":
        if message.document:
            cv_file_id = message.document.file_id
            user_answers[user_id][questions[question_number]] = cv_file_id
        else:
            bot.send_message(
                message.chat.id, "Пожалуйста, отправьте файл вашего резюме."
            )
            bot.register_next_step_handler(message, save_answer, question_number)
            return
    else:  # If the user entered text
        user_answers[user_id][questions[question_number]] = message.text
    # Ask the next question
    ask_question(message, question_number + 1)


def send_answers(chat_id):
    if chat_id in user_answers:
        review_text = "\n".join(
            [
                f"{key}: {value}"
                for key, value in user_answers[chat_id].items()
                if key != "Резюме"
            ]
        )
        # Check if CV file is uploaded
        if "Резюме" in user_answers[chat_id]:
            cv_file_id = user_answers[chat_id]["Резюме"]
            bot.send_chat_action("-1002002167204", "upload_document")
            sent_review = bot.send_document(
                "-1002002167204",
                cv_file_id,
                caption=review_text,
                reply_markup=review_keyboard,
            )
            bot.send_message(chat_id, "Ваша заявка принята на рассмотрение")
            users_awaiting_review[sent_review.message_id] = chat_id
    else:
        bot.send_message(chat_id, "No answers provided.")


@bot.callback_query_handler(func=lambda call: True)
def review_answers(call):
    if call.message.message_id in users_awaiting_review:
        user_id = users_awaiting_review.pop(call.message.message_id)
        if call.data == "Тест":
            send_task(user_id)
        else:
            bot.send_message(
                user_id,
                "Спасибо за ваше время. К сожалению, на данный момент мы не можем предложить вам сотрудничество.",
            )


def send_task(chat_id):
    task_text = "Поздравляем, вы прошли первичный отбор.\nСледующий этап включает в себя выполнение тестового задания.\nВсе задания вы можете найти по ссылке ниже:\n<a href='https://www.notion.so/macbookbro/1e88dbd00bd9448286caf9b1cac8c1a2'>Тестовое задание</a>"
    bot.send_message(chat_id, task_text, parse_mode="HTML")


bot.polling()


# def write_row(client, database_id, username, position):
#    client.pages.create(
#        **{
#            "parent": {"database_id": database_id},
#            "properties": {
#                "Имя": {"title": [{"text": {"content": username}}]},
#                "Позиция": {"select": {"name": position}},
#            },
#        }
#    )
