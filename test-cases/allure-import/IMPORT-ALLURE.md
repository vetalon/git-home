# Импорт тест-кейсов в Allure TestOps

Набор файлов для переноса **61 тест-кейса** по функционалу «Смена способа оплаты при недостатке средств» (БТ-1536).

## Файлы

| Файл | Назначение |
|------|------------|
| `retry-pay-change-pmi-allure-steps.csv` | **Рекомендуемый** — одна строка = один шаг сценария |
| `retry-pay-change-pmi-allure-flat.csv` | Альтернатива — одна строка = один тест-кейс, шаги в поле `scenario` |
| `allure-migration-config.example.json` | Пример конфига для [migration tool](https://qameta.github.io/docs-3p-migration-script/) |
| `generate_allure_csv.py` | Скрипт генерации CSV (если нужно пересобрать после правок) |

## Как импортировать

> **Важно:** начиная с Allure TestOps **25.3.4** импорт CSV через UI отключён. Используйте migration tool или обратитесь в поддержку Qameta.

### Вариант 1 — CSV через migration tool (рекомендуется)

1. Скачайте [allure-testops-migration](https://qameta.github.io/docs-3p-migration-script/) (нужна Java 21, пользователь с ROLE_ADMIN).
2. Скопируйте `allure-migration-config.example.json` → `config.json` и укажите endpoint, токен, `projectId`.
3. Укажите путь к `retry-pay-change-pmi-allure-steps.csv`.
4. Запустите:

```bash
java -jar allure-testops-migration-<version>.jar /path/to/config.json
```

### Вариант 2 — импорт CSV через UI (если версия < 25.3.4)

1. **Test cases** → **Import** → выберите `retry-pay-change-pmi-allure-steps.csv`.
2. Сопоставьте колонки:

| Колонка CSV | Поле Allure TestOps |
|-------------|---------------------|
| `name` | Name |
| `precondition` | Precondition |
| `step_action` | Scenario → Step (action) |
| `step_expected_result` | Scenario → Expected result |
| `Epic` | Epic |
| `Feature` | Feature |
| `Story` | Story |
| `Severity` | Severity |
| `tag` | Tags |
| `Layer` | Custom field «Layer» (создайте в проекте, если нет) |
| `external_id` | Custom field «External ID» (опционально) |

3. Для многострочного файла (`-steps.csv`) строки с пустым `name` относятся к предыдущему тест-кейсу — включите группировку по `external_id`, если мастер импорта это поддерживает.

### Вариант 3 — flat CSV

Используйте `retry-pay-change-pmi-allure-flat.csv`, если удобнее один тест = одна строка:

| Колонка CSV | Поле Allure |
|-------------|-------------|
| `scenario` | Scenario (шаги с маркером `[expected]` для ожидаемого результата) |

## Настройка дерева тест-кейсов

После импорта в **Project settings → Trees** добавьте дерево:

- **Epic** → **Feature** → **Story** → **Layer**

Так кейсы сгруппируются: `Оплата` → `Смена способа оплаты…` → `БТ-1536` → `E2E / Backend / Frontend`.

## Приоритеты

| Severity в CSV | Исходный приоритет |
|--------------|-------------------|
| Critical | P1 |
| High | P2 |
| Normal | P3 |
| Minor | P4 |

## Пересборка CSV

```bash
python3 generate_allure_csv.py
```

## Smoke-набор (P1)

Для быстрого прогона отфильтруйте в Allure по тегу или Severity = Critical:

- E2E: TC-RPMI-001 … TC-RPMI-007
- Backend Ordering: TC-RPMI-016 … TC-RPMI-022
- Backend Payments: TC-RPMI-034 … TC-RPMI-037
- Rubilnik: TC-RPMI-040
- Mobile: TC-RPMI-042 … TC-RPMI-045

## Ссылки

- [Импорт CSV в Allure TestOps](https://docs.qameta.io/allure-testops/briefly/test-cases/import/)
- [Migration tool](https://qameta.github.io/docs-3p-migration-script/)
- [Ручной сценарий (шаги + expected results)](https://docs.qameta.io/allure-testops/briefly/test-cases/scenario/)
