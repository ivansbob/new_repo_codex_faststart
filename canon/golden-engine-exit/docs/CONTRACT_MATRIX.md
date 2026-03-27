# CONTRACT_MATRIX — GMEE P0 (v0.4, Variant A)

Цель: зафиксировать **1:1 соответствие** между:
- `configs/*` (единственные числа/пороги),
- `queries/*` (единственный read API),
- `schemas/*` (DDL),
- `docs/*` (контракты).

CI обязан ловить любой drift.

---

## 1) Sources of truth (P0)

### 1.1 Numeric truth
- `configs/golden_exit_engine.yaml` — единственный источник порогов/чисел.

### 1.2 Read API truth
- `configs/queries.yaml` — реестр SQL файлов и их параметров (**1:1** с placeholders).
- `queries/*.sql` — только эти SQL разрешены для чтения.

### 1.3 Storage truth
- `schemas/clickhouse.sql` — таблицы + TTL + (ровно) MV+VIEW
- `schemas/postgres.sql` — config_store/experiment_registry/promotions_audit

### 1.4 Contract truth
- `docs/SPEC.md` — writer ordering, attempt/confirm/forensics, gates
- `docs/DATA_MODEL.md` — must-log поля, ключи, TTL

---

## 2) Variant A (обязательное правило)

**Variant A:** `queries/04_glue_select.sql` **должен быть полностью параметризован**.

Запрещено в SQL04:
- захардкоженные значения порогов/epsilon/aggr/clamp (секунды/миллисекунды/проценты/окна)

Разрешено:
- строковые литералы `'U'|'S'|'M'|'L'`
- `CASE/multiIf` логика
- числа, не являющиеся порогами (например 0/1 для булевских выражений)

CI (`scripts/assert_no_drift.py`) проверяет: ни одно число из YAML-порогов не встречается как literal в SQL04.

---

## 3) YAML → SQL placeholder mapping (P0)

Источник: `configs/golden_exit_engine.yaml: chain_defaults.solana`

| YAML path | Meaning | SQL placeholder (queries/04_glue_select.sql) |
|---|---|---|
| `mode_thresholds_sec.U_max` | верхняя граница U | `{mode_u_max_sec:UInt32}` |
| `mode_thresholds_sec.S_max` | верхняя граница S | `{mode_s_max_sec:UInt32}` |
| `mode_thresholds_sec.M_max` | верхняя граница M | `{mode_m_max_sec:UInt32}` |
| `planned_hold.margin_mult_default` | множитель hold | `{margin_mult:Float32}` |
| `planned_hold.clamp_sec.min` | min hold | `{min_hold_sec:UInt32}` |
| `planned_hold.clamp_sec.max` | max hold | `{max_hold_sec:UInt32}` |
| `epsilon.pad_ms_default` | epsilon pad | `{epsilon_pad_ms:UInt32}` |
| `epsilon.hard_bounds_ms.min` | epsilon min | `{epsilon_min_ms:UInt32}` |
| `epsilon.hard_bounds_ms.max` | epsilon max | `{epsilon_max_ms:UInt32}` |
| `aggr_triggers.U.up_pct` | U runaway pct | `{aggr_u_up_pct:Float32}` |
| `aggr_triggers.U.window_sec` | U runaway window | `{aggr_u_window_s:UInt16}` |
| `aggr_triggers.S.up_pct` | S runaway pct | `{aggr_s_up_pct:Float32}` |
| `aggr_triggers.S.window_sec` | S runaway window | `{aggr_s_window_s:UInt16}` |
| `aggr_triggers.M.up_pct` | M runaway pct | `{aggr_m_up_pct:Float32}` |
| `aggr_triggers.M.window_sec` | M runaway window | `{aggr_m_window_s:UInt16}` |
| `aggr_triggers.L.up_pct` | L runaway pct | `{aggr_l_up_pct:Float32}` |
| `aggr_triggers.L.window_sec` | L runaway window | `{aggr_l_window_s:UInt16}` |
| `microticks.window_sec` | microticks window | `{microticks_window_s:UInt16}` |

---

## 4) Quantile mapping contract (Mode → Base quantile) (P0 hard)

Контракт:
- `U -> q10_hold_sec`
- `S -> q25_hold_sec`
- `M -> q40_hold_sec`
- `L -> median_hold_sec`

Где реализовано:
- декларативно: `configs/golden_exit_engine.yaml` (`base_quantile_by_mode`)
- вычислительно: `queries/04_glue_select.sql` (выбор `base_hold_sec`)
- контролируется: `scripts/assert_no_drift.py` (regex-проверка)

---

## 5) DDL ↔ YAML (TTL / retention)

DDL в `schemas/clickhouse.sql` обязан соответствовать YAML:

- `signals_raw TTL` == `retention.signals_raw_ttl_days`
- `rpc_events TTL` == `retention.rpc_events_ttl_days`
- `microticks_1s TTL` == `chain_defaults.solana.microticks.ttl_days`
- `trades_ttl_days=0` → TTL отсутствует в DDL для `trades`

CI сравнивает YAML ↔ DDL.

---

## 6) CI gates (must pass before “business-code”)

Workflow: `.github/workflows/ch_compile_smoke.yml`

Gates:
1) DDL apply: `schemas/clickhouse.sql` применился на пустой БД
2) Query compile: `EXPLAIN SYNTAX` для `queries/01..04.sql`
3) Anti-drift: `python3 scripts/assert_no_drift.py`
4) Canary: seed + checks (throwIf)
5) Oracle: tiny dataset → `04_glue_select.sql` → TSV == expected

Если любой gate падает — запрещено двигаться к P1/P2.
