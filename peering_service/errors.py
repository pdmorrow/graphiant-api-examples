class PeeringServiceError(Exception):
    """Base class for all peering service errors"""


class PeeringServiceClientError(PeeringServiceError):
    """Base class for all client side errors"""


class PeeringServiceConfigurationError(PeeringServiceError):
    """Base class for exceptions generated when configuring services."""
