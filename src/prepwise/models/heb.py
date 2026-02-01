"""HEB cart data models for PrepWise."""

from pydantic import BaseModel, Field
from typing import Optional


class HEBCartItem(BaseModel):
    """A single item added to the HEB cart."""

    search_term: str = Field(description="Original search term used")
    product_name: Optional[str] = Field(default=None, description="Actual product name found")
    price: Optional[float] = Field(default=None, description="Item price")
    quantity: int = Field(default=1, description="Quantity added")
    success: bool = Field(description="Whether item was successfully added")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    suggestion: Optional[str] = Field(
        default=None, description="Alternative search suggestion if not found"
    )


class HEBCartResult(BaseModel):
    """Result of adding items to HEB cart."""

    items: list[HEBCartItem] = Field(default_factory=list, description="All items processed")
    total_added: int = Field(default=0, description="Number of items successfully added")
    total_not_found: int = Field(default=0, description="Number of items not found")
    total_errors: int = Field(default=0, description="Number of errors encountered")
    cart_total: Optional[float] = Field(default=None, description="Estimated cart total")
    cart_url: str = Field(default="https://www.heb.com/cart", description="URL to view cart")

    @property
    def added_items(self) -> list[HEBCartItem]:
        """Get list of successfully added items."""
        return [item for item in self.items if item.success]

    @property
    def failed_items(self) -> list[HEBCartItem]:
        """Get list of items that failed to add."""
        return [item for item in self.items if not item.success]

    def summary(self) -> str:
        """Generate a human-readable summary of the cart operation."""
        lines = [
            "HEB Cart Summary",
            "=" * 40,
            "",
        ]

        if self.added_items:
            lines.append(f"Added ({len(self.added_items)} items):")
            for item in self.added_items:
                price_str = f" - ${item.price:.2f}" if item.price else ""
                name = item.product_name or item.search_term
                lines.append(f"  - {name}{price_str}")
            lines.append("")

        if self.failed_items:
            lines.append(f"Not Found ({len(self.failed_items)} items):")
            for item in self.failed_items:
                suggestion = f" -> Try: {item.suggestion}" if item.suggestion else ""
                lines.append(f"  - {item.search_term}{suggestion}")
            lines.append("")

        if self.cart_total:
            lines.append(f"Estimated Total: ${self.cart_total:.2f}")

        lines.append(f"Review cart: {self.cart_url}")

        return "\n".join(lines)


class HEBSessionStatus(BaseModel):
    """Status of the HEB browser session."""

    logged_in: bool = Field(description="Whether user is logged in")
    session_exists: bool = Field(description="Whether a session directory exists")
    message: str = Field(description="Human-readable status message")
