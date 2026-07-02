#!/usr/bin/env python3
"""Generate Allure TestOps import CSV files for retry-pay / change-pmi test cases."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent

PRIORITY_MAP = {
    "P1": "Critical",
    "P2": "High",
    "P3": "Normal",
    "P4": "Minor",
}

EPIC = "Оплата"
FEATURE = "Смена способа оплаты при недостатке средств"
STORY_BT = "БТ-1536"


@dataclass
class TestCase:
    external_id: str
    priority: str
    layer: str
    name: str
    precondition: str
    steps: list[tuple[str, str]]
    tags: list[str]
    description: str = ""


TEST_CASES: list[TestCase] = [
    TestCase(
        "TC-RPMI-001", "P1", "E2E",
        "Успешная смена способа оплаты на привязанную карту (BANKCARD)",
        "Заказ в WAIT_RETRY_PAY; retry_pay.available_function = change_pmi; дедлайн не истёк; тогл RETRY_PAY_CHANGE_PMI включён; на карте достаточно средств.",
        [("Открыть деталку заказа.", "Деталка открыта, отображается сценарий смены способа оплаты."),
         ("Нажать «Изменить».", "Открыт bottom sheet выбора способа оплаты."),
         ("Выбрать привязанную карту BANKCARD.", "Способ выбран, кнопка «Готово» активна."),
         ("Нажать «Готово».", "Вызван POST /retry-pay-by-linked-pmi; холд/extrahold успешен; деталка обновляется (~10 сек); оплата проходит; заказ продолжает обработку.")],
        ["e2e", "change-pmi", "bankcard", "happy-path"],
    ),
    TestCase(
        "TC-RPMI-002", "P1", "E2E",
        "Успешная смена на привязанный SberPay (SBERPAY)",
        "Заказ в WAIT_RETRY_PAY с change_pmi; есть активная связка SberPay; дедлайн не истёк.",
        [("Открыть деталку → «Изменить».", "Открыт bottom sheet."),
         ("Выбрать SBERPAY → «Готово».", "POST /retry-pay-by-linked-pmi; успешный холд; деталка обновлена; оплата проходит.")],
        ["e2e", "change-pmi", "sberpay", "happy-path"],
    ),
    TestCase(
        "TC-RPMI-003", "P1", "E2E",
        "Успешная смена на Orange Pay (ORANGE_PAY)",
        "Есть связка Orange Pay; KAF доступен; change_pmi; дедлайн не истёк.",
        [("Выбрать Orange Pay → «Готово».", "POST /retry-pay-by-linked-pmi + fingerprint из KAF; успешная оплата; деталка обновлена.")],
        ["e2e", "change-pmi", "orange-pay", "happy-path"],
    ),
    TestCase(
        "TC-RPMI-004", "P1", "E2E",
        "Смена через добавление новой карты (ADD_CARD)",
        "Нет подходящей привязанной карты с достаточным балансом; change_pmi.",
        [("Выбрать «Добавить карту» → «Готово».", "POST /retry-pay-by-unlinked-card; открывается вебвью Сбербанка."),
         ("Пройти привязку карты в вебвью и закрыть его.", "Возврат на деталку с обновлением (~10 сек); связка создана; оплата успешна.")],
        ["e2e", "change-pmi", "add-card", "happy-path"],
    ),
    TestCase(
        "TC-RPMI-005", "P1", "E2E",
        "Смена через добавление SberPay (ADD_SBERPAY)",
        "Диплинк SberPay доступен (iOS — хотя бы одна схема; Android — диплинк отвечает).",
        [("Выбрать ADD_SBERPAY → «Готово».", "POST /retry-pay-by-unlinked-sberpay; открыто приложение Сбера."),
         ("Вернуться по обратному диплинку.", "Деталка обновлена (~10 сек); связка и оплата успешны.")],
        ["e2e", "change-pmi", "add-sberpay", "happy-path"],
    ),
    TestCase(
        "TC-RPMI-006", "P1", "E2E",
        "Недостаточно средств при смене — повторный change_pmi",
        "Первая смена завершилась HOLD_FAILED / WITHDRAW_FAILED; available_function остаётся change_pmi.",
        [("Повторить смену способа оплаты на другой метод.", "Доступен повторный выбор; attempt_count увеличен; UI показывает сценарий смены (не «Списать сейчас»).")],
        ["e2e", "change-pmi", "negative", "retry"],
    ),
    TestCase(
        "TC-RPMI-007", "P1", "E2E",
        "Истечение дедлайна retry_pay_deadline — смена недоступна",
        "Заказ в WAIT_RETRY_PAY; retry_pay_deadline < текущего времени.",
        [("Открыть деталку заказа.", "Блок «Изменить» скрыт или неактивен."),
         ("Попытаться открыть bottom sheet смены способа (если UI позволяет).", "Кнопка «Готово» неактивна; смена способа невозможна.")],
        ["e2e", "change-pmi", "deadline", "negative"],
    ),
    TestCase(
        "TC-RPMI-008", "P2", "E2E",
        "Сценарий retry_pay (без смены способа) — регрессия",
        "available_function = retry_pay; is_retry_pay = true; дедлайн не истёк.",
        [("Открыть деталку / главную / историю.", "Отображается UI «Недостаточно средств, Списать сейчас»; кнопки «Изменить» нет.")],
        ["e2e", "retry-pay", "regression"],
    ),
    TestCase(
        "TC-RPMI-009", "P2", "E2E",
        "Смена способа с главной (активный заказ)",
        "Активный заказ с change_pmi на главной; дедлайн не истёк.",
        [("Нажать «Изменить» на виджете активного заказа.", "Открывается деталка + bottom sheet выбора способа оплаты.")],
        ["e2e", "change-pmi", "main-screen"],
    ),
    TestCase(
        "TC-RPMI-010", "P2", "E2E",
        "Смена способа из истории заказов",
        "Заказ в истории с change_pmi; дедлайн не истёк.",
        [("Нажать «Изменить» в списке истории.", "Открывается деталка + bottom sheet.")],
        ["e2e", "change-pmi", "order-history"],
    ),
    TestCase(
        "TC-RPMI-011", "P2", "E2E",
        "Открытие смены способа по пушу",
        "Получен пуш об изменении способа оплаты.",
        [("Тапнуть по пушу.", "Открывается деталка заказа с bottom sheet выбора способа оплаты.")],
        ["e2e", "change-pmi", "push"],
    ),
    TestCase(
        "TC-RPMI-012", "P2", "E2E",
        "Тогл RETRY_PAY_CHANGE_PMI выключен",
        "Тогл в Rubilnik = OFF; ошибка оплаты (недостаток средств).",
        [("Получить заказ после ошибки оплаты.", "available_function ≠ change_pmi или смена недоступна."),
         ("Проверить UI.", "Отображается «Списать сейчас» / старое поведение без смены способа.")],
        ["e2e", "rubilnik", "toggle-off"],
    ),
    TestCase(
        "TC-RPMI-013", "P2", "E2E",
        "Старая версия приложения + change_pmi",
        "Установлена старая версия мобильного приложения; бэкенд вернул change_pmi.",
        [("Вызвать POST /retry-pay (старый флоу «Списать сейчас»).", "Ответ 424: «Изменить способ оплаты можно только в новой версии приложения».")],
        ["e2e", "change-pmi", "backward-compatibility"],
    ),
    TestCase(
        "TC-RPMI-014", "P3", "E2E",
        "Пуш при истечении дедлайна без смены (СБП-сценарий)",
        "Оплата СБП; дедлайн истёк; способ не сменён.",
        [("Дождаться срабатывания джобы отмены партиции.", "В ОМС paid = false; payment_status = WITHDRAW_FAILED; пуш: «Не хватает на оплату» / «Пополните счёт, повторим списание через Х минут».")],
        ["e2e", "push", "deadline", "sbp"],
    ),
    TestCase(
        "TC-RPMI-015", "P3", "E2E",
        "Отложенный пуш ER025 (15 мин)",
        "Сценарий смены способа; WITHDRAW_FAILED; error_code = ER025.",
        [("Дождаться ~15 мин (или уменьшенный конфиг на стенде).", "Отправлен отложенный пуш по тексту [СА] «Нерабочая связка для СБП».")],
        ["e2e", "push", "er025"],
    ),
    TestCase(
        "TC-RPMI-016", "P1", "Backend (Ordering)",
        "GET /orders/{id}/payment-methods — корректный список для RETRY_PAY",
        "Заказ WAIT_RETRY_PAY; available_function = change_pmi.",
        [("Вызвать GET /api/ordering/public/v1/orders/{order_id}/payment-methods.", "200; список содержит BANKCARD, SBERPAY, ORANGE_PAY, ADD_CARD, ADD_SBERPAY; нет SBP, ADD_SBP, INSTANT_SBP, PODELI; порядок как в Payments.")],
        ["backend", "ordering", "payment-methods"],
    ),
    TestCase(
        "TC-RPMI-017", "P1", "Backend (Ordering)",
        "POST /retry-pay-by-linked-pmi — успешный холд",
        "Валидный pmi_id; заказ в корректном статусе.",
        [("Вызвать POST /retry-pay-by-linked-pmi.", "200; attempt_count +1; инициирован extrahold/hold; статус переходит корректно.")],
        ["backend", "ordering", "retry-pay-by-linked-pmi"],
    ),
    TestCase(
        "TC-RPMI-018", "P1", "Backend (Ordering)",
        "POST /retry-pay-by-unlinked-card — успех",
        "Валидные данные карты; заказ WAIT_RETRY_PAY.",
        [("Вызвать POST /retry-pay-by-unlinked-card.", "200; создана связка + холд; attempt_count +1.")],
        ["backend", "ordering", "retry-pay-by-unlinked-card"],
    ),
    TestCase(
        "TC-RPMI-019", "P1", "Backend (Ordering)",
        "POST /retry-pay-by-unlinked-sberpay — успех",
        "Валидный SberPay-флоу; заказ WAIT_RETRY_PAY.",
        [("Вызвать POST /retry-pay-by-unlinked-sberpay.", "200; связка SberPay + холд.")],
        ["backend", "ordering", "retry-pay-by-unlinked-sberpay"],
    ),
    TestCase(
        "TC-RPMI-020", "P1", "Backend (Ordering)",
        "Обработка /extrahold — HOLD_SUCCESS при смене способа",
        "Extrahold в процессе смены PMI.",
        [("Получить callback HOLD_SUCCESS.", "Партиция/заказ обновлены; джоба отмены партиции удалена.")],
        ["backend", "ordering", "extrahold"],
    ),
    TestCase(
        "TC-RPMI-021", "P1", "Backend (Ordering)",
        "Обработка /extrahold — HOLD_FAILED при смене способа",
        "Extrahold после смены PMI.",
        [("Получить HOLD_FAILED.", "available_function остаётся change_pmi; заказ в WAIT_RETRY_PAY; возможна повторная смена.")],
        ["backend", "ordering", "extrahold", "negative"],
    ),
    TestCase(
        "TC-RPMI-022", "P1", "Backend (Ordering)",
        "Kafka: маппинг статусов при смене способа оплаты",
        "Настроен consumer статусов оплаты.",
        [("Отправить HOLD_SUCCESS / HOLD_FAILED / WITHDRAW_FAILED в Kafka.", "Статусы payments и заказа соответствуют матрице «Смена способов оплаты».")],
        ["backend", "ordering", "kafka"],
    ),
    TestCase(
        "TC-RPMI-023", "P2", "Backend (Ordering)",
        "Поле attempt_count при создании payment",
        "Создаётся новый payment.",
        [("Создать payment.", "attempt_count = 0.")],
        ["backend", "ordering", "attempt-count"],
    ),
    TestCase(
        "TC-RPMI-024", "P2", "Backend (Ordering)",
        "attempt_count инкремент при каждой попытке",
        "У payment уже есть попытки оплаты.",
        [("Выполнить retry или смену PMI.", "attempt_count увеличивается на 1.")],
        ["backend", "ordering", "attempt-count"],
    ),
    TestCase(
        "TC-RPMI-025", "P2", "Backend (Ordering)",
        "available_function в ответах GET order / orders / active",
        "Payment в WAIT_RETRY_PAY.",
        [("Вызвать GET /orders/{id}, GET /orders, GET /orders/active.", "В каждом ответе retry_pay.available_function = change_pmi или retry_pay из payments.available_function.")],
        ["backend", "ordering", "api"],
    ),
    TestCase(
        "TC-RPMI-026", "P2", "Backend (Ordering)",
        "POST /retry-pay при available_function = change_pmi",
        "payments.available_function = change_pmi.",
        [("Вызвать POST /retry-pay.", "424 с текстом про новую версию приложения.")],
        ["backend", "ordering", "retry-pay", "negative"],
    ),
    TestCase(
        "TC-RPMI-027", "P2", "Backend (Ordering)",
        "POST /retry-pay при available_function = retry_pay",
        "payments.available_function = retry_pay.",
        [("Вызвать POST /retry-pay.", "Стандартное поведение retry (не 424).")],
        ["backend", "ordering", "retry-pay", "regression"],
    ),
    TestCase(
        "TC-RPMI-028", "P2", "Backend (Ordering)",
        "Джоба отмены партиции при смене PMI",
        "Задан orders_parts.retry_pay_deadline.",
        [("Дождаться таймера без успешной оплаты.", "Запрос в ОМС /update-payment-status paid=false; пуш об ошибке; payment_status = WITHDRAW_FAILED.")],
        ["backend", "ordering", "job"],
    ),
    TestCase(
        "TC-RPMI-029", "P2", "Backend (Ordering)",
        "Удаление джобы при HOLD_SUCCESS / HOLD_FAILED",
        "Джоба отмены партиции запланирована.",
        [("Получить HOLD_SUCCESS или HOLD_FAILED.", "Джоба удалена; повторная отмена не срабатывает.")],
        ["backend", "ordering", "job"],
    ),
    TestCase(
        "TC-RPMI-030", "P3", "Backend (Ordering)",
        "Кэш способов оплаты в Ordering",
        "Заказ с change_pmi.",
        [("Дважды вызвать GET payment-methods подряд.", "Второй запрос отдаётся из кэша; данные консистентны.")],
        ["backend", "ordering", "cache"],
    ),
    TestCase(
        "TC-RPMI-031", "P3", "Backend (Ordering)",
        "Негатив: смена PMI после истечения дедлайна",
        "retry_pay_deadline < now.",
        [("Вызвать retry-pay-by-*.", "Ошибка; смена отклонена.")],
        ["backend", "ordering", "negative", "deadline"],
    ),
    TestCase(
        "TC-RPMI-032", "P3", "Backend (Ordering)",
        "Негатив: смена PMI для чужого заказа",
        "Авторизован другой cip_id.",
        [("Вызвать retry-pay-by-* для чужого order_id.", "403 или 404.")],
        ["backend", "ordering", "negative", "security"],
    ),
    TestCase(
        "TC-RPMI-033", "P4", "Backend (Ordering)",
        "available_function = null",
        "Payment без значения available_function.",
        [("GET order и POST /retry-pay.", "Поведение как retry_pay.")],
        ["backend", "ordering", "edge-case"],
    ),
    TestCase(
        "TC-RPMI-034", "P1", "Backend (Payments)",
        "Фильтрация target=RETRY_PAY — только ADD_CARD и ADD_SBERPAY в primary",
        "Есть несколько способов оплаты у пользователя.",
        [("GET /api/payments/Internal/v1/payment-methods/{cip_id}?target=RETRY_PAY.", "В filter для RETRY_PAY только ADD_CARD, ADD_SBERPAY; остальные отфильтрованы по правилам.")],
        ["backend", "payments", "filter"],
    ),
    TestCase(
        "TC-RPMI-035", "P1", "Backend (Payments)",
        "Сортировка способов для RETRY_PAY",
        "Несколько способов у пользователя.",
        [("Запросить payment-methods с target=RETRY_PAY.", "Порядок соответствует настроенной сортировке RETRY_PAY.")],
        ["backend", "payments", "sort"],
    ),
    TestCase(
        "TC-RPMI-036", "P1", "Backend (Payments)",
        "/extrahold на статусе HOLD_FAILED",
        "Payment в статусе HOLD_FAILED.",
        [("Вызвать extrahold.", "Разрешён переход HOLD_FAILED → EXTRA_HOLD_WAITING.")],
        ["backend", "payments", "extrahold"],
    ),
    TestCase(
        "TC-RPMI-037", "P1", "Backend (Payments)",
        "/confirm после extrahold без успешного HOLD",
        "Только успешный extrahold; HOLD неуспешен.",
        [("Вызвать confirm.", "Confirm проходит: сначала ищется успешный HOLD, если нет — успешный extrahold.")],
        ["backend", "payments", "confirm"],
    ),
    TestCase(
        "TC-RPMI-038", "P2", "Backend (Payments)",
        "Регрессия: confirm при успешном HOLD",
        "Классический HOLD SUCCESS.",
        [("Вызвать confirm.", "Работает по старой логике (приоритет HOLD).")],
        ["backend", "payments", "confirm", "regression"],
    ),
    TestCase(
        "TC-RPMI-039", "P3", "Backend (Payments)",
        "Негатив: extrahold не из HOLD_FAILED",
        "Payment в некорректном статусе.",
        [("Вызвать extrahold.", "Ошибка валидации.")],
        ["backend", "payments", "extrahold", "negative"],
    ),
    TestCase(
        "TC-RPMI-040", "P1", "Backend (Rubilnik)",
        "Тогл RETRY_PAY_CHANGE_PMI ON",
        "Тогл включён; ошибка недостатка средств.",
        [("Создать/получить заказ с retry.", "available_function = change_pmi.")],
        ["backend", "rubilnik", "toggle-on"],
    ),
    TestCase(
        "TC-RPMI-041", "P2", "Backend (Rubilnik)",
        "Тогл RETRY_PAY_CHANGE_PMI OFF",
        "Тогл выключен; ошибка недостатка средств.",
        [("Создать/получить заказ с retry.", "available_function = retry_pay или смена недоступна.")],
        ["backend", "rubilnik", "toggle-off"],
    ),
    TestCase(
        "TC-RPMI-042", "P1", "Frontend (Mobile)",
        "Деталка: UI при change_pmi",
        "is_retry_pay=true; дедлайн не истёк; available_function=change_pmi.",
        [("Открыть деталку заказа.", "Отображается блок с кнопкой «Изменить» (не «Списать сейчас»).")],
        ["frontend", "mobile", "order-detail"],
    ),
    TestCase(
        "TC-RPMI-043", "P1", "Frontend (Mobile)",
        "Bottom sheet: загрузка способов оплаты",
        "Деталка с change_pmi.",
        [("Нажать «Изменить».", "Вызван GET /orders/{id}/payment-methods; открыт bottom sheet «Выберите способ оплаты».")],
        ["frontend", "mobile", "bottom-sheet"],
    ),
    TestCase(
        "TC-RPMI-044", "P1", "Frontend (Mobile)",
        "Кнопка «Готово» — активность при выборе и дедлайне",
        "Bottom sheet открыт.",
        [("Не выбирать способ оплаты.", "Кнопка «Готово» неактивна."),
         ("Выбрать способ при валидном дедлайне.", "Кнопка «Готово» активна."),
         ("Дождаться истечения дедлайна.", "Кнопка «Готово» неактивна.")],
        ["frontend", "mobile", "bottom-sheet", "deadline"],
    ),
    TestCase(
        "TC-RPMI-045", "P1", "Frontend (Mobile)",
        "Таймер на bottom sheet",
        "retry_pay.retry_pay_deadline в ответе деталки.",
        [("Открыть bottom sheet.", "Таймер соответствует retry_pay_deadline с бэкенда.")],
        ["frontend", "mobile", "timer"],
    ),
    TestCase(
        "TC-RPMI-046", "P2", "Frontend (Mobile)",
        "Иконки платёжных систем по BIN",
        "В списке BANKCARD с разными payment_name.",
        [("Открыть bottom sheet.", "2* → MIR; 5* → MC/Maestro; 4* → Visa; иначе — общая иконка.")],
        ["frontend", "mobile", "ui", "bankcard"],
    ),
    TestCase(
        "TC-RPMI-047", "P2", "Frontend (Mobile)",
        "Кнопка «ЕЩЕ» скрыта",
        "Bottom sheet открыт.",
        [("Просмотреть список способов.", "Кнопки «ЕЩЕ» нет.")],
        ["frontend", "mobile", "ui"],
    ),
    TestCase(
        "TC-RPMI-048", "P2", "Frontend (Mobile)",
        "ADD_SBERPAY скрыт при недоступном диплинке",
        "SberPay не установлен / схемы не отвечают.",
        [("Открыть bottom sheet.", "ADD_SBERPAY не отображается.")],
        ["frontend", "mobile", "sberpay", "negative"],
    ),
    TestCase(
        "TC-RPMI-049", "P2", "Frontend (Mobile)",
        "ADD_SBERPAY виден при отвечающем диплинке",
        "SberPay доступен (iOS/Android).",
        [("Открыть bottom sheet.", "ADD_SBERPAY в списке; на iOS — опрос схем по GET /api/payments/v1/deeplink-ios-schemes.")],
        ["frontend", "mobile", "sberpay", "ios", "android"],
    ),
    TestCase(
        "TC-RPMI-050", "P2", "Frontend (Mobile)",
        "Недоступные типы оплаты не показываются",
        "API не возвращает SBP/PODELI и т.д.",
        [("Открыть bottom sheet.", "Нет SBP, ADD_SBP, INSTANT_SBP, PODELI.")],
        ["frontend", "mobile", "payment-types"],
    ),
    TestCase(
        "TC-RPMI-051", "P2", "Frontend (Mobile)",
        "Порядок способов в списке",
        "Несколько способов в ответе API.",
        [("Сравнить UI с JSON.", "Порядок = порядку массива payments.")],
        ["frontend", "mobile", "ui"],
    ),
    TestCase(
        "TC-RPMI-052", "P2", "Frontend (Mobile)",
        "Главная: виджет активного заказа change_pmi",
        "Активный заказ с change_pmi.",
        [("Открыть главную.", "UI с «Изменить», не «Списать сейчас».")],
        ["frontend", "mobile", "main-screen"],
    ),
    TestCase(
        "TC-RPMI-053", "P2", "Frontend (Mobile)",
        "История: карточка заказа change_pmi",
        "Заказ в списке истории с change_pmi.",
        [("Открыть историю заказов.", "Корректный блок и кнопка «Изменить».")],
        ["frontend", "mobile", "order-history"],
    ),
    TestCase(
        "TC-RPMI-054", "P2", "Frontend (Mobile)",
        "Обновление деталки после успешной смены (linked PMI)",
        "Успешный ответ retry-pay-by-linked-pmi.",
        [("Нажать «Готово» и дождаться обновления.", "Остаёмся/переходим на деталку; обновление с задержкой ~10 сек.")],
        ["frontend", "mobile", "refresh"],
    ),
    TestCase(
        "TC-RPMI-055", "P2", "Frontend (Mobile)",
        "Флоу ADD_CARD: вебвью и возврат",
        "Выбран ADD_CARD.",
        [("Пройти вебвью → закрыть.", "После закрытия — деталка с обновлением ~10 сек.")],
        ["frontend", "mobile", "add-card"],
    ),
    TestCase(
        "TC-RPMI-056", "P2", "Frontend (Mobile)",
        "Флоу ADD_SBERPAY: диплинк туда-обратно",
        "Выбран ADD_SBERPAY.",
        [("Уйти в SberPay → вернуться по диплинку.", "Деталка с обновлением ~10 сек.")],
        ["frontend", "mobile", "add-sberpay"],
    ),
    TestCase(
        "TC-RPMI-057", "P3", "Frontend (Mobile)",
        "is_active=false у способа оплаты",
        "В ответе есть неактивный способ.",
        [("Открыть bottom sheet.", "Неактивный способ недоступен для выбора / визуально отключён.")],
        ["frontend", "mobile", "negative"],
    ),
    TestCase(
        "TC-RPMI-058", "P3", "Frontend (Mobile)",
        "Ошибка API payment-methods",
        "Мок/стенд возвращает 5xx или timeout.",
        [("Нажать «Изменить».", "Понятная ошибка; повтор возможен; приложение не падает.")],
        ["frontend", "mobile", "error-handling"],
    ),
    TestCase(
        "TC-RPMI-059", "P3", "Frontend (Mobile)",
        "Ошибка retry-pay-by-*",
        "API возвращает ошибку.",
        [("Нажать «Готово».", "Ошибка пользователю; bottom sheet/деталка в консистентном состоянии.")],
        ["frontend", "mobile", "error-handling"],
    ),
    TestCase(
        "TC-RPMI-060", "P4", "Frontend (Mobile)",
        "UI при истёкшем дедлайне на деталке",
        "retry_pay_deadline < now.",
        [("Открыть деталку.", "Нет активного сценария смены/retry.")],
        ["frontend", "mobile", "deadline"],
    ),
    TestCase(
        "TC-RPMI-061", "P4", "Frontend (Mobile)",
        "Bottom sheet аналогичен чекауту",
        "Есть эталонный чекаут.",
        [("Сравнить UI bottom sheet с чекаутом.", "Стили и состояния выбора как на чекауте; кнопки «ЕЩЕ» нет.")],
        ["frontend", "mobile", "ui", "regression"],
    ),
]


def write_steps_csv(path: Path) -> None:
    """One row per step — best for Allure CSV import mapping."""
    fieldnames = [
        "external_id",
        "name",
        "Epic",
        "Feature",
        "Story",
        "Layer",
        "Severity",
        "tag",
        "precondition",
        "step_index",
        "step_action",
        "step_expected_result",
        "description",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for tc in TEST_CASES:
            for idx, (action, expected) in enumerate(tc.steps, start=1):
                writer.writerow({
                    "external_id": tc.external_id if idx == 1 else "",
                    "name": tc.name if idx == 1 else "",
                    "Epic": EPIC if idx == 1 else "",
                    "Feature": FEATURE if idx == 1 else "",
                    "Story": STORY_BT if idx == 1 else "",
                    "Layer": tc.layer if idx == 1 else "",
                    "Severity": PRIORITY_MAP[tc.priority] if idx == 1 else "",
                    "tag": ",".join(tc.tags) if idx == 1 else "",
                    "precondition": tc.precondition if idx == 1 else "",
                    "step_index": idx,
                    "step_action": action,
                    "step_expected_result": expected,
                    "description": tc.description if idx == 1 else "",
                })


def write_flat_csv(path: Path) -> None:
    """One row per test case — alternative import format."""
    fieldnames = [
        "external_id",
        "name",
        "Epic",
        "Feature",
        "Story",
        "Layer",
        "Severity",
        "tag",
        "precondition",
        "description",
        "scenario",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for tc in TEST_CASES:
            scenario_lines: list[str] = []
            for idx, (action, expected) in enumerate(tc.steps, start=1):
                scenario_lines.append(f"{idx}. {action}")
                scenario_lines.append(f"   [expected] {expected}")
            writer.writerow({
                "external_id": tc.external_id,
                "name": tc.name,
                "Epic": EPIC,
                "Feature": FEATURE,
                "Story": STORY_BT,
                "Layer": tc.layer,
                "Severity": PRIORITY_MAP[tc.priority],
                "tag": ",".join(tc.tags),
                "precondition": tc.precondition,
                "description": tc.description,
                "scenario": "\n".join(scenario_lines),
            })


def main() -> None:
    write_steps_csv(OUTPUT_DIR / "retry-pay-change-pmi-allure-steps.csv")
    write_flat_csv(OUTPUT_DIR / "retry-pay-change-pmi-allure-flat.csv")
    print(f"Generated {len(TEST_CASES)} test cases into {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
