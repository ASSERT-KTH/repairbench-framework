from abc import ABC, abstractmethod
from typing import Optional


class CostStrategy(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @staticmethod
    @abstractmethod
    def compute_costs(samples: list, model_name: str) -> Optional[dict]:
        pass
