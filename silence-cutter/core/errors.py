"""Custom exception hierarchy for Silence Cutter."""


class SilenceCutterError(Exception):
    """Base exception for all Silence Cutter errors."""
    pass


class BinaryNotFoundError(SilenceCutterError):
    """Raised when auto-editor binary is not found."""
    pass


class ProcessingError(SilenceCutterError):
    """Raised when video processing fails."""
    pass


class AnalysisError(SilenceCutterError):
    """Raised when video analysis fails."""
    pass


class InvalidInputError(SilenceCutterError):
    """Raised when input file is invalid."""
    pass
