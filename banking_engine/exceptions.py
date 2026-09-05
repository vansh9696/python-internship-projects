"""Custom domain exceptions for robust banking ledger error handling."""

class BankingEngineError(Exception):
    """Base exception for all domain-specific errors."""
    pass


class AccountNotFoundError(BankingEngineError):
    """Raised when an operation targets a non-existent account ID."""
    pass


class DuplicateAccountError(BankingEngineError):
    """Raised when attempting to register an existing account ID."""
    pass


class InvalidTransactionAmountError(BankingEngineError):
    """Raised when a credit or debit amount is zero or negative."""
    pass


class InsufficientFundsError(BankingEngineError):
    """Raised when an account cannot satisfy a withdrawal/transfer request."""
    pass


class UnsupportedFormatError(BankingEngineError):
    """Raised when an unsupported serialization format is specified."""
    pass