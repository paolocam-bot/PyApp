from enum import Enum
from dataclasses import dataclass

class Urgenza(Enum):
    BASSA = "Bassa"
    MEDIA = "Media"
    ALTA = "Alta"

@dataclass
class Ticket:
    titolo: str
    descrizione: str
    urgenza: str