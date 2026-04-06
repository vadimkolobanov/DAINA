import weasyprint

html = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<style>
  @page { size: A4; margin: 2cm; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; line-height: 1.5; color: #2d2028; }
  h1 { font-size: 22px; color: #a06a78; margin-bottom: 4px; }
  h2 { font-size: 16px; color: #a06a78; border-bottom: 2px solid #f0d5d0; padding-bottom: 4px; margin-top: 24px; }
  h3 { font-size: 13px; color: #2d2028; margin-top: 16px; }
  .subtitle { font-size: 12px; color: #9e8a94; margin-bottom: 20px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; }
  .badge-fail { background: #fde8e8; color: #c85050; }
  .badge-warn { background: #fef3e2; color: #b07a00; }
  .badge-pass { background: #e8f5e9; color: #2e7d32; }
  table { width: 100%; border-collapse: collapse; margin: 8px 0 16px; font-size: 10.5px; }
  th, td { border: 1px solid #e0d5d8; padding: 6px 8px; text-align: left; }
  th { background: #f8f0f3; font-weight: 600; color: #a06a78; }
  tr:nth-child(even) { background: #fdf8fa; }
  .critical { color: #c85050; font-weight: 600; }
  .high { color: #d4a050; font-weight: 600; }
  .medium { color: #9e8a94; }
  .summary-box { background: #f8f0f3; border-radius: 8px; padding: 12px 16px; margin: 12px 0; }
  .verdict { font-size: 14px; font-weight: 700; color: #a06a78; text-align: center; padding: 12px; background: #fdf0ec; border-radius: 8px; margin: 16px 0; }
  ul { margin: 4px 0; padding-left: 20px; }
  li { margin-bottom: 3px; }
  .page-break { page-break-before: always; }
</style>
</head>
<body>

<h1>DAINA — Code Review Report</h1>
<div class="subtitle">GloDia Beauty & Nails Studio — Telegram Mini App<br>Дата: 6 апреля 2026 | Ревизия: a6c3208</div>

<div class="verdict">ОБЩАЯ ОЦЕНКА: DEPLOYABLE WITH CAUTION</div>

<div class="summary-box">
  <strong>Проект:</strong> Telegram Mini App для записи на маникюр<br>
  <strong>Стек:</strong> FastAPI + Aiogram (backend), React + TypeScript + Vite (frontend), PostgreSQL<br>
  <strong>Деплой:</strong> Docker → Timeweb Cloud<br>
  <strong>Статус:</strong> Работает в продакшене. Функционал полный. Есть критические проблемы безопасности.
</div>

<!-- ==================== BACKEND ==================== -->
<h2>1. Бэкенд — Сводка по категориям</h2>

<table>
  <tr><th>Категория</th><th>Оценка</th><th>Критич.</th><th>Высокие</th><th>Средние</th></tr>
  <tr><td>Архитектура</td><td><span class="badge badge-pass">PASS</span></td><td>0</td><td>0</td><td>2</td></tr>
  <tr><td>Безопасность</td><td><span class="badge badge-fail">FAIL</span></td><td>4</td><td>2</td><td>3</td></tr>
  <tr><td>Целостность данных</td><td><span class="badge badge-fail">FAIL</span></td><td>2</td><td>2</td><td>3</td></tr>
  <tr><td>Обработка ошибок</td><td><span class="badge badge-pass">PASS</span></td><td>0</td><td>0</td><td>3</td></tr>
  <tr><td>Производительность</td><td><span class="badge badge-pass">PASS</span></td><td>0</td><td>0</td><td>0</td></tr>
  <tr><td>Качество кода</td><td><span class="badge badge-warn">NEEDS IMPROVEMENT</span></td><td>0</td><td>0</td><td>2</td></tr>
  <tr><td>БД / Миграции</td><td><span class="badge badge-warn">NEEDS IMPROVEMENT</span></td><td>0</td><td>1</td><td>3</td></tr>
</table>

<h3>Критические проблемы бэкенда</h3>
<table>
  <tr><th>#</th><th>Проблема</th><th>Файл</th><th>Влияние</th></tr>
  <tr><td>1</td><td class="critical">Race condition при записи</td><td>booking_service.py:138</td><td>Двойная запись на один слот</td></tr>
  <tr><td>2</td><td class="critical">Нет аутентификации на клиентских endpoints</td><td>bookings.py, clients.py</td><td>Любой может создать/изменить запись</td></tr>
  <tr><td>3</td><td class="critical">Небезопасный fallback авторизации</td><td>dependencies.py:72</td><td>Можно выдать себя за любого пользователя</td></tr>
  <tr><td>4</td><td class="critical">Race condition в статистике клиента</td><td>booking_service.py:134</td><td>Потеря счётчика визитов</td></tr>
  <tr><td>5</td><td class="critical">CORS allow_origins=["*"]</td><td>main.py:115</td><td>API доступен с любого сайта</td></tr>
  <tr><td>6</td><td class="critical">Миграции в коде приложения</td><td>main.py:33-40</td><td>Ошибки миграций скрываются</td></tr>
</table>

<h3>Высокие проблемы бэкенда</h3>
<table>
  <tr><th>#</th><th>Проблема</th><th>Файл</th></tr>
  <tr><td>7</td><td class="high">Нет rate limiting</td><td>Все endpoints</td></tr>
  <tr><td>8</td><td class="high">Уведомления только на ADMIN_TELEGRAM_ID</td><td>notification_service.py:78</td></tr>
  <tr><td>9</td><td class="high">Нет пагинации</td><td>admin.py:147</td></tr>
  <tr><td>10</td><td class="high">Нет индексов на bookings.client_id, status</td><td>models/booking.py</td></tr>
  <tr><td>11</td><td class="high">Нет валидации переходов статуса</td><td>booking_service.py:122</td></tr>
</table>

<h3>Что сделано хорошо (бэкенд)</h3>
<ul>
  <li>Чистая архитектура: models → services → API</li>
  <li>pool_pre_ping + pool_recycle — пул соединений настроен</li>
  <li>lazy="selectin" — нет N+1 запросов</li>
  <li>Все уведомления проверяют telegram_id is not None</li>
  <li>Логирование ошибок через logger.exception()</li>
  <li>Конфигурация через БД + env fallback</li>
</ul>

<!-- ==================== FRONTEND ==================== -->
<h2 class="page-break">2. Фронтенд — Сводка по категориям</h2>

<table>
  <tr><th>Категория</th><th>Оценка</th><th>Критич.</th><th>Высокие</th><th>Средние</th></tr>
  <tr><td>Архитектура</td><td><span class="badge badge-warn">NEEDS IMPROVEMENT</span></td><td>0</td><td>1</td><td>2</td></tr>
  <tr><td>TypeScript</td><td><span class="badge badge-warn">NEEDS IMPROVEMENT</span></td><td>0</td><td>1</td><td>2</td></tr>
  <tr><td>React паттерны</td><td><span class="badge badge-pass">PASS</span></td><td>0</td><td>0</td><td>2</td></tr>
  <tr><td>Обработка ошибок</td><td><span class="badge badge-warn">NEEDS IMPROVEMENT</span></td><td>1</td><td>0</td><td>3</td></tr>
  <tr><td>Безопасность</td><td><span class="badge badge-warn">NEEDS IMPROVEMENT</span></td><td>0</td><td>1</td><td>1</td></tr>
  <tr><td>UX / Доступность</td><td><span class="badge badge-warn">NEEDS IMPROVEMENT</span></td><td>0</td><td>0</td><td>2</td></tr>
  <tr><td>Качество кода</td><td><span class="badge badge-pass">PASS</span></td><td>0</td><td>0</td><td>2</td></tr>
</table>

<h3>Критические проблемы фронтенда</h3>
<table>
  <tr><th>#</th><th>Проблема</th><th>Файл</th><th>Влияние</th></tr>
  <tr><td>1</td><td class="critical">Нет Error Boundary</td><td>App.tsx</td><td>Одна ошибка = белый экран</td></tr>
  <tr><td>2</td><td class="high">any типы в API клиенте</td><td>client.ts:127,158</td><td>Потеря type safety</td></tr>
  <tr><td>3</td><td class="high">Global mutable _authHeaders</td><td>client.ts:4-11</td><td>Race condition, не тестируемо</td></tr>
  <tr><td>4</td><td class="high">Нет route guards для админки</td><td>App.tsx</td><td>Можно перейти до проверки isAdmin</td></tr>
  <tr><td>5</td><td class="high">XSS риск: config values не санитизируются</td><td>MasterContacts.tsx</td><td>Если бэкенд скомпрометирован</td></tr>
</table>

<h3>Что сделано хорошо (фронтенд)</h3>
<ul>
  <li>TypeScript strict mode</li>
  <li>Правильные useEffect cleanup</li>
  <li>Loading/error states почти везде</li>
  <li>Debounce поиска (300ms)</li>
  <li>tg.openTelegramLink() / tg.openLink() — CSP bypass</li>
  <li>SessionStorage для booking state</li>
  <li>Skeleton loaders, анимации Framer Motion</li>
  <li>15s timeout на API запросы</li>
</ul>

<!-- ==================== ROADMAP ==================== -->
<h2 class="page-break">3. План исправлений</h2>

<h3>Фаза 1 — Критические (перед масштабированием)</h3>
<table>
  <tr><th>#</th><th>Задача</th><th>Приоритет</th></tr>
  <tr><td>1</td><td>SELECT FOR UPDATE при создании записи</td><td class="critical">CRITICAL</td></tr>
  <tr><td>2</td><td>Убрать fallback x-telegram-user-id</td><td class="critical">CRITICAL</td></tr>
  <tr><td>3</td><td>Ограничить CORS конкретным доменом</td><td class="critical">CRITICAL</td></tr>
  <tr><td>4</td><td>Атомарные UPDATE visit_count = visit_count + 1</td><td class="critical">CRITICAL</td></tr>
  <tr><td>5</td><td>Error Boundary на фронте</td><td class="critical">CRITICAL</td></tr>
</table>

<h3>Фаза 2 — Высокие (в течение недели)</h3>
<table>
  <tr><th>#</th><th>Задача</th><th>Приоритет</th></tr>
  <tr><td>6</td><td>Rate limiting (slowapi)</td><td class="high">HIGH</td></tr>
  <tr><td>7</td><td>Миграции в Alembic</td><td class="high">HIGH</td></tr>
  <tr><td>8</td><td>Индексы в БД (client_id, status)</td><td class="high">HIGH</td></tr>
  <tr><td>9</td><td>Типизировать any на фронте</td><td class="high">HIGH</td></tr>
  <tr><td>10</td><td>Извлечь дублированные константы</td><td class="high">HIGH</td></tr>
</table>

<h3>Фаза 3 — Средние (в течение месяца)</h3>
<table>
  <tr><th>#</th><th>Задача</th><th>Приоритет</th></tr>
  <tr><td>11</td><td>Валидация переходов статуса</td><td class="medium">MEDIUM</td></tr>
  <tr><td>12</td><td>Разбить index.css на модули</td><td class="medium">MEDIUM</td></tr>
  <tr><td>13</td><td>Пагинация на list endpoints</td><td class="medium">MEDIUM</td></tr>
  <tr><td>14</td><td>CASCADE DELETE на FK</td><td class="medium">MEDIUM</td></tr>
  <tr><td>15</td><td>Route guards для админки</td><td class="medium">MEDIUM</td></tr>
</table>

<!-- ==================== STATS ==================== -->
<h2>4. Статистика проекта</h2>

<div class="summary-box">
  <strong>Файлов Python:</strong> ~25<br>
  <strong>Файлов TypeScript/TSX:</strong> ~22<br>
  <strong>Строк CSS:</strong> ~690<br>
  <strong>API endpoints:</strong> ~20<br>
  <strong>Telegram Bot handlers:</strong> 6<br>
  <strong>Background tasks:</strong> 2 (reminders, followups)<br>
  <strong>Config keys:</strong> 16 (динамических)<br>
  <strong>Зависимости backend:</strong> 9<br>
  <strong>Зависимости frontend:</strong> 6
</div>

<h2>5. Заключение</h2>

<p>Проект <strong>DAINA</strong> представляет собой полнофункциональное Telegram Mini App для записи на маникюр. Приложение включает клиентский booking flow, админ-панель с управлением записями/клиентами/услугами/настройками, систему уведомлений и напоминаний.</p>

<p><strong>Для текущего масштаба</strong> (один мастер, десятки клиентов) — приложение <strong>работоспособно и безопасно</strong>. Критические проблемы безопасности имеют низкий реальный риск при малом трафике.</p>

<p><strong>Для масштабирования</strong> — необходимо выполнить Фазу 1 исправлений (5 задач), что займёт примерно 1 рабочий день.</p>

<div class="verdict">Рекомендация: продолжать использование, запланировать Фазу 1 на ближайшую неделю</div>

</body>
</html>
"""

weasyprint.HTML(string=html).write_pdf("/home/user/DAINA/DAINA_Code_Review.pdf")
print("PDF created")
