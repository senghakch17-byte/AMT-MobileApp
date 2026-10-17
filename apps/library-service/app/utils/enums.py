from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending"      # waiting for an admin decision
    APPROVED = "approved"    # holds the room for that time slot
    REJECTED = "rejected"    # declined by an admin
    CANCELLED = "cancelled"  # withdrawn by the user (or cancelled by an admin)
