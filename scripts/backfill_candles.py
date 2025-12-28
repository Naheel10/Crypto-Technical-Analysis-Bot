from __future__ import annotations

import argparse
from datetime import datetime, timedelta

from bot.data.client import ExchangeClient
from bot.data.repository import DataRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill OHLCV candles into the local DB")
    parser.add_argument("--symbol", required=True, help="Trading pair symbol, e.g. BTC/USDT")
    parser.add_argument("--timeframe", required=True, help="Timeframe, e.g. 1h")
    parser.add_argument("--days", type=int, help="Number of recent days to backfill")
    parser.add_argument("--start", help="ISO start datetime, e.g. 2024-01-01T00:00:00")
    parser.add_argument("--end", help="ISO end datetime, defaults to now")
    return parser.parse_args()


def resolve_dates(args: argparse.Namespace) -> tuple[datetime, datetime]:
    if args.days is not None:
        end = datetime.utcnow()
        start = end - timedelta(days=args.days)
        return start, end

    if not args.start:
        raise ValueError("--start is required when --days is not provided")

    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end) if args.end else datetime.utcnow()
    if start >= end:
        raise ValueError("start must be before end")
    return start, end


def main() -> None:
    args = parse_args()
    start, end = resolve_dates(args)

    exchange = ExchangeClient()
    repository = DataRepository()

    print(
        f"Fetching candles for {args.symbol} {args.timeframe} from {start.isoformat()} to {end.isoformat()}"
    )
    candles = exchange.sync_historical_candles(
        symbol=args.symbol,
        timeframe=args.timeframe,
        since=start,
        end=end,
    )
    candles = candles[(candles["timestamp"] >= start) & (candles["timestamp"] <= end)]

    if candles.empty:
        print("No candles returned from exchange")
        return

    repository.save_candles(args.symbol, args.timeframe, candles)
    print(f"Stored {len(candles)} candles into the local database")


if __name__ == "__main__":
    main()
