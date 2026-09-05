"""Domain models demonstrating encapsulation, inheritance, and polymorphism."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any
from exceptions import InvalidTransactionAmountError, InsufficientFundsError


class BankAccount(ABC):
    """Abstract base class establishing encapsulation and polymorphic behaviors."""

    def __init__(self, account_id: str, owner: str, initial_balance: Decimal = Decimal("0.00")):
        if initial_balance < Decimal("0.00"):
            raise InvalidTransactionAmountError("Initial balance cannot be negative.")
        self._account_id = account_id
        self._owner = owner
        self._balance = initial_balance

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def balance(self) -> Decimal:
        return self._balance

    def deposit(self, amount: Decimal) -> None:
        if amount <= Decimal("0.00"):
            raise InvalidTransactionAmountError("Deposit amount must be strictly positive.")
        self._balance += amount

    @abstractmethod
    def withdraw(self, amount: Decimal) -> None:
        """Subclasses define their own withdrawal constraints."""
        pass

    @abstractmethod
    def apply_monthly_maintenance(self) -> None:
        """Subclasses handle period-end fee/interest adjustments polymorphically."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self._account_id,
            "owner": self._owner,
            "balance": str(self._balance),
            "type": self.__class__.__name__,
        }


class SavingsAccount(BankAccount):
    """Subclass with an interest rate and strict balance floors."""

    def __init__(self, account_id: str, owner: str, initial_balance: Decimal, interest_rate: Decimal):
        super().__init__(account_id, owner, initial_balance)
        self._interest_rate = interest_rate

    def withdraw(self, amount: Decimal) -> None:
        if amount <= Decimal("0.00"):
            raise InvalidTransactionAmountError("Withdrawal amount must be strictly positive.")
        if self._balance - amount < Decimal("0.00"):
            raise InsufficientFundsError("Savings accounts cannot hold negative balances.")
        self._balance -= amount

    def apply_monthly_maintenance(self) -> None:
        interest = self._balance * self._interest_rate
        self._balance += interest

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["interest_rate"] = str(self._interest_rate)
        data["overdraft_limit"] = "0.00"
        return data


class CheckingAccount(BankAccount):
    """Subclass providing an approved overdraft facility and a maintenance fee."""

    def __init__(self, account_id: str, owner: str, initial_balance: Decimal, overdraft_limit: Decimal):
        super().__init__(account_id, owner, initial_balance)
        self._overdraft_limit = overdraft_limit
        self._monthly_fee = Decimal("12.00")

    def withdraw(self, amount: Decimal) -> None:
        if amount <= Decimal("0.00"):
            raise InvalidTransactionAmountError("Withdrawal amount must be strictly positive.")
        if self._balance - amount < -self._overdraft_limit:
            raise InsufficientFundsError(f"Transaction exceeds allowed overdraft of {self._overdraft_limit}.")
        self._balance -= amount

    def apply_monthly_maintenance(self) -> None:
        self._balance -= self._monthly_fee

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["interest_rate"] = "0.00"
        data["overdraft_limit"] = str(self._overdraft_limit)
        return data