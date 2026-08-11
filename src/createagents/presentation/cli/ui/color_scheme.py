class ColorScheme:
    """Manages ANSI color codes for terminal output.

    Responsibility: Centralize all color definitions in one place.
    This follows SRP by having a single reason to change: updating color scheme.
    """

    # Modern color palette - vibrant and professional
    BLUE: str = '\033[38;5;75m'  # Sky Blue (modern, softer than bright blue)
    PURPLE: str = '\033[38;5;141m'  # Medium Purple (elegant, not too bright)
    GREEN: str = '\033[38;5;84m'  # Mint Green (fresh, easy on eyes)
    YELLOW: str = '\033[38;5;221m'  # Soft Yellow (warm, readable)
    RED: str = '\033[38;5;204m'  # Soft Red (error messages)
    CYAN: str = '\033[38;5;87m'  # Bright Cyan (accents)
    GRAY: str = '\033[38;5;245m'  # Medium Gray (subtle text)
    DARK_GRAY: str = '\033[38;5;240m'  # Dark Gray (timestamps, metadata)

    # Styles
    RESET: str = '\033[0m'
    BOLD: str = '\033[1m'
    DIM: str = '\033[2m'
    ITALIC: str = '\033[3m'
    UNDERLINE: str = '\033[4m'

    # Control sequences
    CLEAR_SCREEN: str = '\033[2J\033[H'
    CLEAR_LINE: str = '\033[K'
    MOVE_UP: str = '\033[F'

    @classmethod
    def get_user_color(cls) -> str:
        """Get color for user messages."""
        return cls.BLUE

    @classmethod
    def get_ai_color(cls) -> str:
        """Get color for AI messages."""
        return cls.PURPLE

    @classmethod
    def get_system_color(cls) -> str:
        """Get color for system messages."""
        return cls.CYAN

    @classmethod
    def get_success_color(cls) -> str:
        """Get color for success messages."""
        return cls.GREEN

    @classmethod
    def get_error_color(cls) -> str:
        """Get color for error messages."""
        return cls.RED

    @classmethod
    def get_timestamp_color(cls) -> str:
        """Get color for timestamps."""
        return cls.DARK_GRAY
