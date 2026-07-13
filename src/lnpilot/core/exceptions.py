"""LNPilot-specific exceptions."""


class LNPilotError(Exception):
    """Base error for LNPilot."""


class ValidationError(LNPilotError):
    """Invalid, ambiguous, or physically impossible input."""


class UnitError(LNPilotError):
    """Unit parse or conversion failure."""


class CalibrationError(LNPilotError):
    """Calibration fit or prediction failure."""


class PlateMapError(LNPilotError):
    """Plate map or well assignment problem."""
