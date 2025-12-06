Как начать работать с проектом
1. Склонируй репозиторий
bash

git clone https://github.com/fedorten/Fusion.git
cd Fusion

2. Создай свою ветку
bash

git checkout -b твое-имя/название-задачи

Пример:
bash

git checkout -b anna/login-page
git checkout -b alex/fix-bug-123

3. Сделай изменения в коде

Работай как обычно. Когда готов коммитить:
4. Сохрани изменения
bash

git add .
git commit -m "Описание что сделал"

5. Отправь свою ветку на GitHub
bash

git push -u origin твое-имя/название-задачи
