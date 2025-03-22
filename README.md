Данный бот написан на коленке часа за 4 поэтому ридми соответствующее

Что нужно для запуска?
1. Токен созданного бота. Где его взять? здесь @BotFather
2. Поместить его в созданный файл .env в переменную BOT_TOKEN=<TOKEN> в корень проекта
3. В папку cookies поместить куки от инстаграм instagram_cookies.txt и тикток tiktok_cookies.txt. 
   Где взять? Выкачать из своего браузера, например, расширением Get cookies.txt LOCALLY
4. Выполнить команду docker build -t image name:image tag .
5. Выполнить команду docker run --env-file .env -d image name:image tag