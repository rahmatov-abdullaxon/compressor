from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LiteralToken:
    value: int

    def __post_init__(self):
        if not 0 <= self.value <= 255: raise ValueError("LiteralToken.value must be in the range 0..255.")


@dataclass(frozen=True, slots=True)
class MatchToken:
    distance: int
    length: int

    def __post_init__(self):
        if self.distance <= 0: raise ValueError("MatchToken.distance must be positive.")
        if self.length <= 0: raise ValueError("MatchToken.length must be positive.")

Token = LiteralToken | MatchToken

@dataclass(frozen=True, slots=True)
class LZ77Config:
    window_size: int = 4096
    lookahead_size: int = 258
    min_match_length: int = 3

    def __post_init__(self):
        if self.window_size <= 0: raise ValueError("window_size must be positive.")
        if self.lookahead_size <= 0: raise ValueError("lookahead_size must be positive.")
        if self.min_match_length <= 0: raise ValueError("min_match_length must be positive.")
        if self.min_match_length > self.lookahead_size: raise ValueError("min_match_length cannot exceed lookahead_size.")

@dataclass(slots=True)
class LZ77Archive:
    config: LZ77Config
    original_size: int
    tokens: list
