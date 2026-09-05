"""Dual persistence engine supporting JSON and CSV file formats."""

import csv
import json
from decimal import Decimal
from pathlib import Path
from typing import Dict
from exceptions import UnsupportedFormatError
from models import BankAccount, SavingsAccount, CheckingAccount


class PersistenceEngine:
    """Manages transactional persistence to and from disk."""

    CSV_HEADERS = ["account_id", "owner", "balance", "type", "interest_rate", "overdraft_limit"]

    @staticmethod
    def save(accounts: Dict[str, BankAccount], file_path: str, format_type: str = "json") -> None:
        fmt = format_type.lower()
        path = Path(file_path)

        if fmt == "json":
            data = {acc_id: acc.to_dict() for acc_id, acc in accounts.items()}
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        elif fmt == "csv":
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=PersistenceEngine.CSV_HEADERS)
                writer.writeheader()
                for acc in accounts.values():
                    writer.writerow(acc.to_dict())
        else:
            raise UnsupportedFormatError(f"Format '{format_type}' is not supported. Use 'json' or 'csv'.")

    @staticmethod
    def load(file_path: str, format_type: str = "json") -> Dict[str, BankAccount]:
        fmt = format_type.lower()
        path = Path(file_path)
        accounts: Dict[str, BankAccount] = {}

        if not path.exists():
            return accounts

        if fmt == "json":
            with path.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)
            for acc_id, item in raw_data.items():
                accounts[acc_id] = PersistenceEngine._deserialize(item)

        elif fmt == "csv":
            with path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    accounts[row["account_id"]] = PersistenceEngine._deserialize(row)
        else:
            raise UnsupportedFormatError(f"Format '{format_type}' is not supported. Use 'json' or 'csv'.")

        return accounts

    @staticmethod
    def _deserialize(record: Dict[str, Any]) -> BankAccount:
        acc_type = record["type"]
        acc_id = record["account_id"]
        owner = record["owner"]
        balance = Decimal(record["balance"])

        if acc_type == "SavingsAccount":
            rate = Decimal(record.get("interest_rate", "0.00"))
            return SavingsAccount(acc_id, owner, balance, rate)
        elif acc_type == "CheckingAccount":
            overdraft = Decimal(record.get("overdraft_limit", "0.00"))
            return CheckingAccount(acc_id, owner, balance, overdraft)
        else:
            raise ValueError(f"Unknown account type: {acc_type}")