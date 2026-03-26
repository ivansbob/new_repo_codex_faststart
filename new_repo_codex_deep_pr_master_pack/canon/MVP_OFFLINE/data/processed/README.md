# data/processed

Положите сюда ваш датасет `trades.csv` или `trades.parquet`, соответствующий `../INPUT_CONTRACT.md`.

В пакете уже есть пример:

- `trades_stub.csv` — маленькая заглушка (несколько токенов/кошельков), чтобы прогнать пайплайн локально.
- `tools/convert_csv_to_parquet.py` — утилита для конвертации CSV → Parquet (нужен `pyarrow`).
