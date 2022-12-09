import logging

from environs import Env
import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, Filters, Updater

from api import get_access_token, get_products, get_product_by_id, download_photo, add_product_to_cart, get_cart, \
    delete_from_cart, create_customer


_database = None
logger = logging.getLogger('BotLogger')


def start(update, context):
    products_raw = get_products(context.bot_data['shop_access_token'])

    keyboard = [[InlineKeyboardButton(product['attributes']['name'], callback_data=product['id'])]
                for product in products_raw]

    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text='Что хотите закзать?', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def show_menu(update, context):
    context.bot.delete_message(
        chat_id=update.effective_user.id,
        message_id=update.callback_query.message.message_id,
    )

    products_raw = get_products(context.bot_data['shop_access_token'])

    keyboard = [[InlineKeyboardButton(product['attributes']['name'], callback_data=product['id'])
                 ] for product in products_raw]

    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        chat_id=update.effective_user.id,
        text='Что хотите закзать?',
        reply_markup=reply_markup)

    return 'HANDLE_MENU'


def handle_menu(update, context):
    query = update.callback_query

    if query.data == 'cart':
        return show_cart(update, context)
    else:
        context.user_data['product_id'] = query.data

        product = get_product_by_id(context.bot_data['shop_access_token'], query.data)

        context.bot.delete_message(chat_id=query.message.chat_id,
                                   message_id=query.message.message_id)

        product_img_id = product['relationships']['main_image']['data']['id']
        filename = download_photo(context.bot_data['shop_access_token'], product_img_id)

        with open(f'{filename}', 'rb') as image:
            product_price = product['meta']['display_price']['without_tax']['formatted']
            product_text = f'{product["attributes"]["name"]}\n\n'\
                           f'{product_price} за кг\n\n'\
                           f'{product["attributes"]["description"]}'

            keyboard = [[InlineKeyboardButton('1 кг ⚖', callback_data=1),
                         InlineKeyboardButton('5 кг ⚖', callback_data=5),
                         InlineKeyboardButton('10 кг ⚖', callback_data=10)],
                        [InlineKeyboardButton('Корзина🛒', callback_data='cart')],
                        [InlineKeyboardButton('Назад🔙', callback_data='menu')]
                        ]

            markup = InlineKeyboardMarkup(keyboard)

            context.bot.send_photo(chat_id=query.message.chat_id,
                                   photo=image,
                                   caption=product_text,
                                   reply_markup=markup,)
            return 'HANDLE_DESCRIPTION'


def handle_description(update, context):
    query = update.callback_query

    if query.data == 'menu':
        return show_menu(update, context)
    elif query.data == 'cart':
        return show_cart(update, context)
    else:
        add_product_to_cart(
                    context.bot_data['shop_access_token'],
                    update.effective_user.id,
                    context.user_data['product_id'],
                    query.data
                    )

        update.callback_query.answer(
            text=f'В корзину было добавлено {query.data} кг',
        )

        return 'HANDLE_DESCRIPTION'


def show_cart(update, context):
    query = update.callback_query

    context.bot.delete_message(chat_id=query.message.chat_id,
                               message_id=query.message.message_id)

    cart_response, items_response = get_cart(context.bot_data['shop_access_token'], update.effective_user.id)

    cart_text = ''
    keyboard = []
    for item in items_response:
        cart_text += (f'{item["name"]}\n\n'
                      f'{item["meta"]["display_price"]["with_tax"]["unit"]["formatted"]} за кг\n'
                      f'{item["quantity"]} кг в корзине за '
                      f'{item["meta"]["display_price"]["with_tax"]["value"]["formatted"]}\n\n')

        keyboard.append(
            [InlineKeyboardButton(f'Убрать {item["name"]} из корзины',
                                  callback_data=item["id"])]
        )

    cart_text += f'Total: {cart_response["meta"]["display_price"]["with_tax"]["formatted"]}'

    keyboard.append([InlineKeyboardButton('Оплатить💳', callback_data='pay')])
    keyboard.append([InlineKeyboardButton('Назад🔙', callback_data='menu')])

    markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=update.effective_user.id,
                             text=cart_text,
                             reply_markup=markup)

    return 'HANDLE_CART'


def handle_cart(update, context):
    query = update.callback_query
    if query.data == 'menu':
        return show_menu(update, context)
    elif query.data == 'pay':
        context.bot.delete_message(chat_id=query.message.chat_id,
                                   message_id=query.message.message_id)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Пожалуйста, введите свою почту.')
        return 'WAITING_EMAIL'
    else:
        delete_from_cart(context.bot_data['shop_access_token'], update.effective_user.id, query.data)
        update.callback_query.answer(
            text='Продукт был убран из корзины',
        )
        return show_cart(update, context)


def waiting_email(update, context):
    context.user_data['email'] = update.message.text
    update.message.reply_text(text='Мы свяжемся с вами по почте: '+update.message.text)

    create_customer(context.bot_data['shop_access_token'],
                    update.message.from_user.username,
                    context.user_data['email'])


def handle_users_reply(update, context):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': waiting_email,
    }
    state_handler = states_functions[user_state]

    next_state = state_handler(update, context)
    db.set(chat_id, next_state)


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', context.error)


def get_database_connection():
    global _database
    if _database is None:
        database_password = env('DATABASE_PASSWORD')
        database_host = env('DATABASE_HOST')
        database_port = env('DATABASE_PORT')
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


def regenerate_shop_access_token(context):
    shop_access_token = get_access_token(context.bot_data['shop_client_id'])
    context.bot_data['shop_access_token'] = shop_access_token


if __name__ == '__main__':
    env = Env()
    env.read_env()
    
    tg_token = env('TG_TOKEN')
    shop_client_id = env('SHOP_CLIENT_ID')

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    updater = Updater(tg_token)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    dispatcher.add_error_handler(error)

    shop_access_token, token_expires = get_access_token(shop_client_id)

    dispatcher.bot_data['shop_client_id'] = shop_client_id

    dispatcher.bot_data['shop_access_token'] = shop_access_token
    updater.job_queue.run_repeating(regenerate_shop_access_token, interval=token_expires)

    updater.start_polling()
