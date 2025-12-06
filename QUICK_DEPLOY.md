# Быстрый деплой на paerser2.ru

## Шаг 1: Подготовка на вашем компьютере

1. Убедитесь, что все изменения закоммичены
2. Скопируйте проект на сервер:

```bash
cd /home/fedor/Desktop/lern_projects/mihail_messager2/full-stack-fastapi-template
rsync -avz --exclude 'node_modules' --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' . root@217.18.61.113:/opt/messager/
```

## Шаг 2: Настройка на сервере

1. Подключитесь к серверу:
```bash
ssh root@217.18.61.113
```

2. Перейдите в директорию проекта:
```bash
cd /opt/messager
```

3. Создайте файл `.env`:
```bash
nano .env
```

Вставьте следующее (замените значения на свои):
```env
DOMAIN=paerser2.ru
ENVIRONMENT=production
DOCKER_IMAGE_BACKEND=messager-backend
DOCKER_IMAGE_FRONTEND=messager-frontend
TAG=latest
BACKEND_CORS_ORIGINS=https://paerser2.ru,http://paerser2.ru

# Сгенерируйте секретный ключ:
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

FIRST_SUPERUSER=admin@paerser2.ru
FIRST_SUPERUSER_PASSWORD=ваш_надежный_пароль
SQLITE_DB_PATH=data/app.db
```

Сохраните файл (Ctrl+O, Enter, Ctrl+X)

4. Сделайте скрипт исполняемым:
```bash
chmod +x deploy.sh
```

## Шаг 3: Деплой

Запустите скрипт деплоя:
```bash
./deploy.sh
```

Это займет несколько минут, так как будут собираться Docker образы.

## Шаг 4: Настройка DNS

Убедитесь, что домен `paerser2.ru` указывает на IP `217.18.61.113`:
- A запись: `paerser2.ru` -> `217.18.61.113`

## Шаг 5: Настройка SSL (опционально, но рекомендуется)

1. Установите Nginx и Certbot:
```bash
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx
```

2. Скопируйте конфигурацию SSL:
```bash
cp nginx-ssl.conf /etc/nginx/sites-available/paerser2.ru
```

3. Активируйте конфигурацию:
```bash
ln -s /etc/nginx/sites-available/paerser2.ru /etc/nginx/sites-enabled/
nginx -t
```

4. Получите SSL сертификат:
```bash
certbot --nginx -d paerser2.ru -d www.paerser2.ru
```

Certbot автоматически обновит конфигурацию Nginx.

## Проверка работы

После деплоя проверьте:
- Frontend: http://paerser2.ru (или https:// если настроили SSL)
- API Docs: http://paerser2.ru/api/v1/docs
- Health check: http://paerser2.ru/api/v1/utils/health-check/

## Полезные команды

Просмотр логов:
```bash
docker compose -f docker-compose.prod.yml logs -f
```

Остановка:
```bash
docker compose -f docker-compose.prod.yml down
```

Перезапуск:
```bash
docker compose -f docker-compose.prod.yml restart
```

Статус контейнеров:
```bash
docker compose -f docker-compose.prod.yml ps
```

## Обновление приложения

### Вариант 1: Быстрое обновление (если используете Git)

```bash
cd /opt/messager
./update.sh
```

Скрипт спросит, нужно ли обновить код из Git, и затем передеплоит приложение.

### Вариант 2: Ручное обновление

1. **Если используете Git:**
```bash
cd /opt/messager
git pull
./deploy.sh
```

2. **Если копируете файлы вручную:**
```bash
# На вашем локальном компьютере:
cd /home/fedor/Desktop/lern_projects/mihail_messager2/full-stack-fastapi-template
rsync -avz --exclude 'node_modules' --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' . root@217.18.61.113:/opt/messager/

# На сервере:
ssh root@217.18.61.113
cd /opt/messager
./deploy.sh
```

### Вариант 3: Обновление только определенного сервиса

Если изменили только бэкенд:
```bash
cd /opt/messager
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

Если изменили только фронтенд:
```bash
cd /opt/messager
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### Пересборка без кэша

Если нужно полностью пересобрать образы (например, после изменения зависимостей):
```bash
cd /opt/messager
./deploy.sh --no-cache
```

