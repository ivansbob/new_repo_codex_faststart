# Unified Decision Formula — One‑Formula Strategy

Этот документ фиксирует **канонический алгоритм решения**:

**on‑chain event (wallet buy) → ENTER/SKIP → mode → size → execution params → (post‑entry aggressive switch)**

Он предназначен как спецификация для реализации в `strategy.py` (в боевом репо) и для трансформации в код под GMEE (golden mean exit engine).

---

## 1) Состояние, которое стратегия поддерживает

### Wallet‑профиль `W(w)`
- `roi_30d`, `winrate_30d`, `trades_30d`
- `avg_hold_sec` / `median_hold_sec`
- `max_dd_30d`
- `avg_trade_size`
- `dex_pref` (распределение по DEX / preferred)

### Token/market snapshot `M(m,t)`
- `price`
- `ret_1m`, `ret_5m`
- `vol_5m`
- `liquidity_usd`, `volume_24h`
- `spread_bps`
- `slippage_est(size)` (оценка проскальзывания для размера позиции)

### Polymarket snapshot `P(t)` (optional, overlay)
Polymarket используется как **внешний режим рынка** (risk‑on / risk‑off), который **масштабирует** пороги и размер позиции.

Минимальный набор (на каждом `t`):
- `pmkt_p_bull ∈ [0..1]` — агрегированная “bullish” вероятность по выбранным рынкам
- `pmkt_p_change_1h` / `pmkt_p_change_24h` — динамика (дельты вероятностей)
- `pmkt_volume_z` — z‑score всплеска объёма по связанным рынкам
- (опц.) `pmkt_event_risk ∈ [0..1]` — риск “шторма/resolve” (неопределённость)

> Fallback: если Polymarket недоступен или данные “битые” → `pmkt_p_bull=0.5`, `pmkt_volume_z=0`, `pmkt_event_risk=0` ⇒ режим `r≈0`.

---

## 2) Polymarket → режим рынка `r ∈ [-1..+1]`
 Polymarket “светофор” → режим рынка `r ∈ [-1..+1]`

Сводим Polymarket‑фичи в один скаляр режима:

\[
r(t)=\text{clip}\Big(a\cdot(2\cdot pm\_bullish\_score-1) - b\cdot pm\_event\_risk,\; -1,\; +1\Big)
\]

Интуиция:
- bullish ↑ → `r` стремится к `+1` (risk‑on)
- event_risk ↑ → `r` стремится к `-1` (risk‑off)

---

## 3) Единое правило входа: gates → p_model → EV → regime thresholds

**Триггер:** пришло событие: «кошелёк `w` купил токен `m`» в момент `t`.

### 3.1 Hard gates (жёсткие запреты)

`SKIP`, если не выполнено (значения тюнингуются, но логика фиксируется):
- Wallet:
  - `W.trades_30d ≥ 50`
  - `W.winrate_30d ≥ 0.60`
  - `W.roi_30d ≥ 0.25`
- Token:
  - `M.liquidity_usd ≥ 10k…25k`
  - `M.spread_bps ≤ 100…200`
- Safety (optional, но рекомендовано):
  - `honeypot_safe(m) = True`

### 3.2 Вероятность успеха от модели

Строим фичи `x = Φ(W, M, P)` и получаем калиброванную вероятность:

\[
p = p_{model}(x)
\]

### 3.3 Экономика сделки (ожидание)

Оцениваем стоимость входа и грубый ожидаемый outcome:

- `cost = fee + spread + slippage_est(size)`
- `μ_win`, `μ_loss` (ожидаемые профит/лосс в процентах; можно хранить по `mode` и/или `wallet_tier` на основе истории)

\[
EV = p\cdot \mu_{win} - (1-p)\cdot \mu_{loss} - cost
\]

### 3.4 Regime‑регуляция порогов

Пороги зависят от режима `r`:

- `p_min(r) = p0 + k_p·(-r)`  (risk‑off ⇒ выше порог)
- `δ(r) = δ0 + k_δ·(-r)`      (risk‑off ⇒ больше запас по EV)

Финальное правило:

\[
ENTER \iff (p \ge p_{min}(r)) \wedge (EV \ge \delta(r))
\]

Стартовые значения (как дефолты):
- `p0 = 0.58`, `k_p ≈ 0.03`
- `δ0 = 0…0.01`, `k_δ ≈ 0.01…0.02` *(в долях; в YAML удобно хранить в процентах)*

---

## 4) Режим U/S/M/L + post‑entry aggressive switch

### 4.1 Базовый режим по hold‑профилю кошелька

Определяем `mode_base` по `avg_hold_sec` / `median_hold_sec` кошелька:

- `U`: ≤ 35s
- `S`: ≤ 130s
- `M`: ≤ 220s
- `L`: иначе

### 4.2 TP/SL/hold (база)

- **U (15–30s):** TP `+2…4%`, SL `−2…3%`
- **S (60–90s):** TP `+4…6%`, SL `−4…5%`
- **M (120–180s):** TP `+6…10%`, SL `−5…8%`
- **L (240–300s):** TP `+10…15%`, SL `−7…10%`

### 4.3 Агрессия (post‑entry)

Если после входа цена быстро подтверждает импульс, можно включать **Aggressive Layer** (см. `AGGRESSIVE_LAYER_ROCKET_MODE.md`):
- U: `+3% за ≤12s`
- S: `+6% за ≤30s`
- M: `+10% за ≤60s`
- L: `+15% за ≤90s`

Агрессия = **partial take + runner + trailing**:
- продать `30–50%` на раннем TP‑триггере
- остаток вести trailing `10–15%` от пика, с высоким TP

---

## 5) Размер позиции и risk limits (завязаны на `r`)

### 5.1 Sizing (в % от банка)

\[
size_{pct}(r)=\text{clamp}\big(s0\cdot(1+k_s\cdot r),\;0.5\%,\;2\%\big)
\]

Пример: `s0=1%`, `k_s=0.5`  
(risk‑on ⇒ до ~1.5%, risk‑off ⇒ до ~0.5–0.7%)

### 5.2 Max open positions (регим‑зависимый)

\[
max\_open(r)=\text{round}\big(M0\cdot(1+k_m\cdot r)\big)
\]

Пример: `M0=20`, `k_m=0.5`

### 5.3 Kill‑switch (обязателен)

- `max_daily_loss = 5–10%`
- `max_drawdown_total = 20–30%` ⇒ останов/пересмотр/ cooldown

---

## 6) MVP‑критерий “100% free stack” (неделя 1)

MVP = **backtest + sim/paper**, без агрессивного live‑исполнения:
- Discovery: Dune/Flipside/Kolscan (free‑first) → список кошельков
- Free RPC: Helius/Alchemy → история/ивенты (с лимитами)
- Colab + DuckDB/Parquet → симы и бэктест
- Метрики: `ROI`, `winrate`, `maxDD`, `fill_rate` (если симулируем лимиты/TTL)

---

## Связанные артефакты в пакете
- `AGGRESSIVE_LAYER_ROCKET_MODE.md` — правила агрессии (partial/runner/trailing + safety gates)
- `MVP_OFFLINE/` — runnable каркас (Trade → Signal → Sim entry/exit → metrics)
- `REFERENCE/strategy_one_formula.py` — скелет кода, реализующий эту формулу как интерфейсы/алгоритм

