# Aggressive Layer — “Режим ракеты” поверх U/S/M/L

Этот документ фиксирует **агрессивный слой** стратегии GMEE как **надстройку** над базовыми режимами **U/S/M/L**.

- **Входы не меняются**: те же Tier-кошельки, те же hard-gates (+EV/liq/honeypot/риск-лимиты).
- Меняется **управление позицией после входа**:
  - быстрый **partial take profit** (30–50%),
  - перевод остатка в **runner** (высокий TP),
  - расширенный SL и **trailing stop** от локального пика.
- Агрессия включается **только при выполнении жёстких условий** (wallet/token/regime/risk-state), иначе бот торгует **только base-профилями**.

---

## 1) Base vs Aggressive — логика

### Base (канон)
- Режимы удержания: **U / S / M / L** (15–30 / 60–90 / 120–180 / 240–300 сек)
- У каждого режима: **TP/SL/TTL**
- Hard-gates: wallet tier + winrate/ROI/trades, token liquidity/spread/honeypot, risk regime, cooldown, лимиты.

### Aggressive (надстройка)
1) **После входа** проверяем, был ли быстрый импульс цены от входа.
2) Если импульс удовлетворяет триггеру режима (см. ниже) и проходит safety-filter:
   - фиксируем **часть позиции** по “ранней цели”
   - остаток переводим в **runner-профиль**: высокий TP + trailing
3) Если safety-filter не пройден → **агрессия запрещена**, остаёмся на base.

---

## 2) Профили агрессии по режимам

Все проценты ниже — **изменение цены от входа**.

### U_aggr (15–30s)
**Триггер:** +3–4% за ≤10–15s  
**Действие:**
- partial: 30–50% на +3–4%
- остаток: TP +10–30%, SL −5–8%, trailing 10–15% от пика

### S_aggr (60–90s)
**Триггер:** +6–8% за ≤30s  
**Действие:**
- partial: ~50% на +6–8%
- остаток: TP +30–60%, SL −10–15%, trailing 10–15%

### M_aggr (120–180s)
**Триггер:** +10–15% за ≤60–90s **и** есть follow-on entries smart-кошельков  
**Действие:**
- partial: 30–50% на +10–15%
- остаток: TP +60–120%, SL −15–25%, trailing с “зажатием” (tightening)

### L_aggr (240–300s, редко/элита)
**Триггер:** +15% за ≤90s и wallet median_hold_sec ≥ 200 и исторически ловит x3–x10  
**Действие:**
- partial: 30–50% на +15–20%
- остаток: TP +100–200%+, SL −25–35% или stop-from-peak
- выход не по времени, а по: drawdown от peak (например −30%), leader-exit/hazard, target MC (если используете)

---

## 3) Когда агрессия запрещена (passes_safety_filters)

Агрессивный режим **нельзя включать**, если выполняется что-либо из ниже:

### Wallet слабый
- winrate_30d < 0.60
- ROI_30d < 0.20–0.25
- trades_30d ниже порога tier-гейтов

### Token рискованный
- liquidity_usd < 15–20k
- honeypot flags / sell tax / blacklist признаки
- holders концентрация (top10 > 80–90% или ваш лимит)
- любые признаки “sell may fail” → агрессия OFF

### Regime / risk-state
- risk-off (глобально) или локальный cooldown
- дневной loss близко к лимиту или total drawdown близко к стопу
- слишком большая экспозиция в этом токене

**Результат:** если safety-filter не пройден → **mode = base_only**.

---

## 4) Каноническая интеграция в логику (post-entry)

Агрессия — **пост-входовой переключатель** (один раз до partial), без изменения входной логики:

```python
def maybe_switch_to_aggressive(mode_base, dt_sec, price_change, wallet, token, ctx):
    if not passes_safety_filters(wallet, token, ctx):
        return None, "base_only"

    if mode_base == "U" and price_change >= 0.03 and dt_sec <= 15:
        return "U_aggr", "partial_take_profit"
    if mode_base == "S" and price_change >= 0.06 and dt_sec <= 30:
        return "S_aggr", "partial_take_profit"
    if mode_base == "M" and price_change >= 0.10 and dt_sec <= 90 and ctx.follow_on_smart_money:
        return "M_aggr", "partial_take_profit"
    if mode_base == "L" and price_change >= 0.15 and dt_sec <= 90 and wallet.median_hold_sec >= 200:
        return "L_aggr", "partial_take_profit"

    return None, "no_change"
```

---

## 5) Агрессия и риск-менеджмент (anti-casino)

Фиксируем дополнительные ограничения **только для aggr**:

- `size_multiplier_vs_base = 0.75` (часто лучше меньше размер, но шире хвост)
- `max_aggr_trades_per_day`
- `max_aggr_open_positions`
- `max_aggr_exposure_pct`
- отдельный kill-switch по aggr:
  - если aggr DD ≥ 10–15% или aggr winrate < порога → aggr OFF до конца дня/периода

---

## 6) Канон конфигов

- Канонический YAML для Codex: `config/params_base.yaml` и `config/modes.yaml`
- MVP_OFFLINE использует адаптированный конфиг/нормализацию, но смысл агрессии тот же.

