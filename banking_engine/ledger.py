"""Coordinates high-level domain operations across multiple accounts."""

from decimal import Decimal
from typing import Dict
from exceptions import AccountNotFoundError, DuplicateAccountError
from models import BankAccount
from persistence import PersistenceEngine


class BankingLedger:
    """Central manager handling atomic transfers, persistence, and maintenance."""

    def __init__(self):
        self._accounts: Dict[str, BankAccount] = {}

    def register_account(self, account: BankAccount) -> None:
        if account.account_id in self._accounts:
            raise DuplicateAccountError(f"Account {account.account_id} already exists.")
        self._accounts[account.account_id] = account

    def get_account(self, account_id: str) -> BankAccount:
        if account_id not in self._accounts:
            raise AccountNotFoundError(f"Account {account_id} does not exist.")
        return self._accounts[account_id]

    def transfer(self, from_id: str, to_id: str, amount: Decimal) -> None:
        src = self.get_account(from_id)
        dst = self.get_account(to_id)
        # Attempt withdrawal first; balance remains safe if it raises InsufficientFunds
        src.withdraw(amount)
        dst.deposit(amount)

    def run_eom_processing(self) -> None:
        """Polymorphically executes end-of-month adjustments across all registered types."""
        for account in self._accounts.values():
            account.apply_monthly_maintenance()

    def export_data(self, file_path: str, format_type: str = "json") -> None:
        PersistenceEngine.save(self._accounts, file_path, format_type)

    def import_data(self, file_path: str, format_type: str = "json") -> None:
        self._accounts = PersistenceEngine.load(file_path, format_type)