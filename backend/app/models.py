from datetime import date, time
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class LoginRequest(StrictModel):
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr

class SessionRequest(StrictModel):
    access_token: SecretStr
    refresh_token: SecretStr

class EmailRequest(StrictModel):
    email: str = Field(min_length=3, max_length=254)

class PasswordRequest(StrictModel):
    password: SecretStr

class GuestRequest(StrictModel):
    display_name: str = Field(min_length=2, max_length=80)
    community_id: int = Field(gt=0)

class ProfileRequest(StrictModel):
    username: str = Field(min_length=3, max_length=40)
    community_id: int = Field(gt=0)

class ModeratorAssignment(StrictModel):
    profile_id: UUID
    community_id: int = Field(gt=0)
    enabled: bool
    reason: str = Field(min_length=10, max_length=2000)

class DisputeResolution(StrictModel):
    decision: Literal["VERIFY", "CANCEL"]
    reason: str = Field(min_length=10, max_length=2000)

class MatchResult(StrictModel):
    type: Literal["winner", "draw"]
    winner_player_id: int | None = Field(default=None, gt=0)

class MatchRequest(StrictModel):
    community_id: int = Field(gt=0)
    format_id: int = Field(gt=0)
    match_date: date
    approximate_start_time: time
    participant_ids: list[int] = Field(min_length=2)
    result: MatchResult

    @model_validator(mode="after")
    def validate_registration(self):
        if self.approximate_start_time.tzinfo is not None:
            raise ValueError("Informe o horário local de Brasília, sem deslocamento de fuso.")
        if any(player <= 0 for player in self.participant_ids) or len(set(self.participant_ids)) != len(self.participant_ids):
            raise ValueError("Os participantes devem ser identificadores positivos e distintos.")
        winner = self.result.winner_player_id
        if self.result.type == "draw" and winner is not None:
            raise ValueError("Empate da mesa não possui vencedor.")
        if self.result.type == "winner" and winner not in self.participant_ids:
            raise ValueError("O vencedor deve ser um dos participantes.")
        return self
