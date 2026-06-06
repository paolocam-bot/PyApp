from dataclasses import dataclass
from typing import List

@dataclass
class StepRisoluzione:
    id_step: int
    id_problema: int
    numero_passo: int
    testo: str
    immagine_path: str
    video_url: str

@dataclass
class Problema:
    id_problema: int
    macro_categoria: str
    sotto_categoria: str
    titolo: str
    steps: List[StepRisoluzione] = None