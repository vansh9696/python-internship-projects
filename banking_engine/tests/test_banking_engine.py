
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))



import pytest
from decimal import Decimal
from exceptions import (
    AccountNotFoundError,
    DuplicateAccountError,
    InsufficientFundsError,
    InvalidTransactionAmountError,
    UnsupportedFormatError,
)
from ledger import BankingLedger
from models import SavingsAccount, CheckingAccount


@pytest.fixture
def ledger():
    engine = BankingLedger()
    engine.register_account(SavingsAccount("SAV-01", "Alice", Decimal("1000.00"), Decimal("0.05")))
    engine.register_account(CheckingAccount("CHK-01", "Bob", Decimal("200.00"), Decimal("500.00")))
    return engine


def test_invalid_initialization_amount():
    with pytest.raises(InvalidTransactionAmountError):
        SavingsAccount("SAV-ERR", "Fail", Decimal("-10.00"), Decimal("0.02"))


def test_deposit_validation(ledger):
    acc = ledger.get_account("SAV-01")
    acc.deposit(Decimal("250.00"))
    assert acc.balance == Decimal("1250.00")

    with pytest.raises(InvalidTransactionAmountError):
        acc.deposit(Decimal("-50.00"))


def test_savings_withdrawal_and_overdraft_block(ledger):
    savings = ledger.get_account("SAV-01")
    savings.withdraw(Decimal("500.00"))
    assert savings.balance == Decimal("500.00")

    with pytest.raises(InsufficientFundsError):
        savings.withdraw(Decimal("501.00"))


def test_checking_overdraft_behavior(ledger):
    chk = ledger.get_account("CHK-01")
    # Balance 200, limit 500 -> can withdraw up to 700
    chk.withdraw(Decimal("600.00"))
    assert chk.balance == Decimal("-400.00")

    with pytest.raises(InsufficientFundsError):
        chk.withdraw(Decimal("101.00"))


def test_polymorphic_eom_processing(ledger):
    ledger.run_eom_processing()
    # SAV-01: 1000 + (1000 * 0.05) = 1050
    assert ledger.get_account("SAV-01").balance == Decimal("1050.00")
    # CHK-01: 200 - 12 fee = 188
    assert ledger.get_account("CHK-01").balance == Decimal("188.00")


def test_ledger_transfer_happy_path(ledger):
    ledger.transfer("SAV-01", "CHK-01", Decimal("300.00"))
    assert ledger.get_account("SAV-01").balance == Decimal("700.00")
    assert ledger.get_account("CHK-01").balance == Decimal("500.00")


def test_ledger_transfer_insufficient_funds(ledger):
    with pytest.raises(InsufficientFundsError):
        ledger.transfer("SAV-01", "CHK-01", Decimal("10000.00"))

    # Verify atomic state integrity
    assert ledger.get_account("SAV-01").balance == Decimal("1000.00")
    assert ledger.get_account("CHK-01").balance == Decimal("200.00")


def test_ledger_exceptions(ledger):
    with pytest.raises(DuplicateAccountError):
        ledger.register_account(SavingsAccount("SAV-01", "Duplicate", Decimal("10.00"), Decimal("0.01")))

    with pytest.raises(AccountNotFoundError):
        ledger.get_account("NON-EXISTENT")


def test_json_persistence(ledger, tmp_path):
    target = tmp_path / "ledger.json"
    ledger.export_data(str(target), format_type="json")

    fresh_ledger = BankingLedger()
    fresh_ledger.import_data(str(target), format_type="json")

    assert fresh_ledger.get_account("SAV-01").balance == Decimal("1000.00")
    assert fresh_ledger.get_account("CHK-01").owner == "Bob"


def test_csv_persistence(ledger, tmp_path):
    target = tmp_path / "ledger.csv"
    ledger.export_data(str(target), format_type="csv")

    fresh_ledger = BankingLedger()
    fresh_ledger.import_data(str(target), format_type="csv")

    assert fresh_ledger.get_account("SAV-01").balance == Decimal("1000.00")
    assert fresh_ledger.get_account("CHK-01").balance == Decimal("200.00")


def test_unsupported_persistence_format(ledger, tmp_path):
    target = tmp_path / "ledger.xml"
    with pytest.raises(UnsupportedFormatError):
        ledger.export_data(str(target), format_type="xml")