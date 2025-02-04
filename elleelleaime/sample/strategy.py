from abc import ABC, abstractmethod
from typing import Optional, Union

from elleelleaime.core.benchmarks.bug import Bug


class PromptingStrategy(ABC):
    def __init__(self, strategy_name: str, **kwargs):
        self.strategy_name = strategy_name

    @abstractmethod
    def prompt(self, bug: Bug) -> dict[str, Optional[str]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        :return: A dictionary containing the prompt and other relevant information.
        """
        pass
