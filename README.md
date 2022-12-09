# fish-shop
 
Чатбот в мессенджере телеграм для продажи рыбы с помощью сервиса [Elastic Path](https://elasticpath.com)

[@FishShop](https://t.me/dvmn_verbs_game_support_bot)

Пример работы:

![](https://github.com/Ykyki4/fish-shop/blob/main/media/tg-example.gif)

## Установка:

Для начала, скачайте репозиторий в .zip или клонируйте его, изолируйте проект с помощью venv и установите зависимости командой:

```
pip install -r requirements.txt
```

Далее, создайте файл .env и установите следующие переменные окружения в формате ПЕРЕМЕННАЯ=значение:

* TG_BOT_TOKEN - Бот в телеграмме для викторин. Зарегистрировать нового бота можно [тут](https://telegram.me/BotFather).
* SHOP_CLIENT_ID - Айди вашего магазина на [Elastic Path](https://elasticpath.com).
* DB_HOST
* DB_PASSWORD
* DB_PORT

Для получения данных о вашей базе данных, зайдите на [сайт](https://redis.com/), и создайте там новую базу данных.

Для запуска бота, введите в терминал команду:

```
python tg_bot.py
```
