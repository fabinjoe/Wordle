
from abc import ABC, abstractclassmethod

from puzzle import WordlePuzzle

class UI(ABC):
    def __init__(self, wordle_object: WordlePuzzle):
        self.wordle_puzzle = wordle_object

    def __str__(self) -> str:
        return f"<{self.name} Object>\n {self.wordle_puzzle.__str__()}"

    def solve(self):
        solution_generator = self.wordle_puzzle.solutionGenerator()
        next_word = next(solution_generator)
        while next_word != "COMPLETED":
            self.enterWordEntry(next_word)
            config = self.obtainConfiguration()
            next_word = solution_generator.send(config)

    @abstractclassmethod
    def enterWordEntry(self, my_word):
        pass

    @abstractclassmethod
    def obtainConfiguration(self):
        pass

class TerminalUI(UI):
    def __init__(self, wordle_object: WordlePuzzle):
        super().__init__(wordle_object)
        self.name = "TerminalUI"

    def enterWordEntry(self, my_word):
        print(f'Chosen word is "{my_word}"') 

    def obtainConfiguration(self):
        return input("  Enter Configuration: ")

