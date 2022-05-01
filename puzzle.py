
import math

from elements import Configuration, WordSet, ConfigMap
from elements import GREEN, YELLOW, GRAY

class WordlePuzzle():
    '''Represts a classic Wordle Puzzle'''
    def __init__(self, configuration_map: ConfigMap, word_list: list[str]) -> None:
        '''Require path to list of words and config map to initialize the variables.'''
        self.complete = False
        self.steps = 0
        self.mystery_word = "UNSOLVED"

        self.word_set = WordSet(word_list)
        self.config_map = configuration_map

    def __str__(self) -> str:
        string = ""
        if not self.complete:
            string = f"<Wordle Object> Unsolved, Uncertainity Size: {self.word_set.size()}"
        else:
            string = f"<Wordle Object> Solved, Mystery Word: {self.mystery_word}, Steps: {self.steps}"
        return string

    def solutionGenerator(self) -> str:
        '''Begins a feedback loop, wherein the program suggests the next best word, and requests
        the user to enter the obtained configuration output.'''
        self.mystery_word = self.findNextWord() # obtain the next Word
        # self.mystery_word = "crane"
        self.steps = 1
        
        while True:
            config: Configuration = self.configurationGenerator((yield self.mystery_word))
            # self.userConfigurationInput(f"Chosen word is {self.mystery_word}. Enter Configuration: ")
            
            if self.isCompleteConfig(config) or self.complete:
                self.complete = True
                break
            
            self.word_set.reduceWordSet(self.mystery_word, self.config_map, config)
            self.mystery_word = self.findNextWord() # obtain the next Word
            self.steps += 1

        yield "COMPLETED"
    
    def configurationGenerator(self, string: str) -> Configuration:
        '''Obtains a user input on the recieved configuration, and returns a Configuration Object'''
        return Configuration( string )
    
    def isCompleteConfig(self, config: Configuration) -> bool:
        '''Checks wether the puzzle has been solved'''
        return config.isComplete()

    def findNextWord(self) -> str:
        '''Returns the best next word, given the current state of the puzzle'''

        # If the puzzle is solved then this function has no purpose and hence returns empty
        if self.complete:
            return

        # Find which word give the highest bits, ie would provide the most information.
        highest_bits = -math.inf
        next_word = ""

        for word in self.config_map.get_config_map():
            if not self.isValidWord(word):
                continue

            bits = self.word_set.expectedBitsInWord(self.config_map, word)
            if bits > highest_bits:
                highest_bits = bits
                next_word = word  
            elif bits>0 and bits == highest_bits and self.word_set.hasWord(word):  
                highest_bits = bits
                next_word = word

        if highest_bits == 0:
            if self.word_set.size() == 0:
                raise Exception("<Wordle>: Exception raised in findNextWord. Recheck logic...")
            self.complete = True
            self.mystery_word = self.word_set.pop()
            return self.mystery_word

        return next_word
    
    def revealMysteryWord( self ) -> str:
        '''Returns the answer of the puzzle, if solved.'''
        if self.complete:
            return self.mystery_word
        return "UNSOLVED"

    def isValidWord(self, _) -> bool:
        return True

    def reset( self ) -> None:
        '''Resets the variables of the puzzle.'''
        self.complete = False
        self.steps = 0
        self.mystery_word = "UNSOLVED"

        self.word_set = WordSet(self.word_list)

    def getPuzzleSize(_) -> int:
        return 1

class WordleHardPuzzle(WordlePuzzle):
    def __init__(self, configuration_map: ConfigMap, word_list: list[str]) -> None:
        super().__init__(configuration_map, word_list)
        
        self.prev_word = ""
        self.prev_config = Configuration()

    def __str__(self) -> str:
        string = ""
        if not self.complete:
            string = f"<WordleHard Object> Unsolved, Uncertainity Size: {self.word_set.size()}"
        else:
            string = f"<WordleHard Object> Solved, Mystery Word: {self.mystery_word}, Steps: {self.steps}"
        return string

    def findNextWord(self) -> str:
        self.prev_word = super().findNextWord()
        return self.prev_word
    
    def configurationGenerator(self, string: str) -> Configuration:
        '''Obtains a user input on the recieved configuration, and returns a Configuration Object'''
        self.prev_config = super().configurationGenerator(string)
        return self.prev_config

    def isValidWord(self, word: str) -> bool:
        prev_config = self.prev_config.get_config()
        temp_word = self.prev_word
        for index in range(len(temp_word)):
            if prev_config[index] != GREEN:
                continue
            if temp_word[index] != word[index]:
                return False
            word = word[0:index] + "_" + word[index+1:]
            
        for index in range(len(temp_word)):
            if prev_config[index] != YELLOW:
                continue
            if temp_word[index] not in word:
                return False
            word = word[0:index] + "_" + word[index+1:]
        return True

class WordleMultiPuzzle(WordlePuzzle):
    def __init__(self, configuration_map: ConfigMap, word_list: list[str], no_of_games: int) -> None:
        super().__init__(configuration_map, word_list)
        
        self.no_of_games = no_of_games
        self.complete = False
        self.solved = []
        self.steps = 0
        self.mystery_word = []

        # word_list = load_wordlist(path_to_word_list)
        self.word_set = []
        for _ in range(no_of_games):
            self.solved.append(False)
            self.mystery_word.append("UNSOLVED")
            self.word_set.append(WordSet(word_list))

    def __str__(self) -> str:
        string = f"<WordleMulti Object> {f'Complete, Steps: {self.steps}' if self.complete else 'Incomplete'}"
        for index in range(self.no_of_games):
            if not self.solved[index]:
                string += f"\n   Unsolved, Uncertainity Size: {self.word_set[index].size()}"
            else:
                string += f"\n   Solved, Mystery Word: {self.mystery_word[index]}"
        return string
    
    def solutionGenerator(self) -> str:
        '''Begins a feedback loop, wherein the program suggests the next best word, and requests
        the user to enter the obtained configuration output.'''
        next_word, more_next_words = self.findNextWord() # obtain the next Word
        self.steps = 1

        while True:
            configs: list[Configuration] = self.configurationGenerator((yield next_word))

            if self.isCompleteConfig(configs, next_word) or self.complete:
                self.complete = True
                break

            for game_index in range(self.no_of_games):
                self.word_set[game_index].reduceWordSet(next_word, self.config_map, configs[game_index])
            next_word, more_next_words = self.findNextWord() # obtain the next Word
            self.steps += 1
         
        if self.complete and len(more_next_words) != 0:
            for next_word in more_next_words:
                yield next_word
        
        yield "COMPLETED"

    def configurationGenerator(self, string: str) -> list[Configuration]:
        configs = []
        for index in range(self.no_of_games):
            configs.append( Configuration( string[index*5:(index+1)*5] ) )
        return configs
    
    def isCompleteConfig(self, configs: list[Configuration], next_word: str) -> bool:
        returnValue = True
        for game_index in range(self.no_of_games):
            if self.solved[game_index]:
                continue
            if configs[game_index].isComplete():
                self.solved[game_index] = True
                self.mystery_word[game_index] = next_word
                continue
            returnValue = False
        return returnValue

    def findNextWord(self) -> str:
        if self.complete:
            return

        highest_bits = -math.inf
        next_word = ""
        more_next_words = []

        for word in self.config_map.get_config_map():

            bits = 0.0
            for game_index in range(self.no_of_games):
                bits += self.word_set[game_index].expectedBitsInWord( self.config_map, word )
            if bits > highest_bits:
                highest_bits = bits
                next_word = word    

        if highest_bits == 0:
            next_word = ""
            self.steps -= 1
            for game_index in range(self.no_of_games):
                if self.solved[game_index]:
                    continue
                if self.word_set[game_index].size() == 0:
                    raise Exception("<Wordle>: Exception raised in findNextWord. Recheck logic...")
                if next_word != "":
                    more_next_words.append(next_word)
                self.solved[game_index] = True
                self.mystery_word[game_index] = self.word_set[game_index].pop()
                next_word = self.mystery_word[game_index]
                self.steps += 1
            self.complete = True

        return next_word, more_next_words

    def getPuzzleSize(self) -> int:
        return self.no_of_games
