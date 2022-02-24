
import os
import time
import math
import pickle
import json
import winsound
from typing import Dict, List, Set, Tuple

GREEN = 1
YELLOW = 2
GRAY = 3


class Configuration():
    def __init__(self, *args) -> None:
        if len(args) == 0:
            self.colors = [GRAY,GRAY,GRAY,GRAY,GRAY]
        elif len(args) == 1 and isinstance( args[0], str ):
            config_string = args[0]
            self.colors = []
            self.colors.append( int(config_string[0]) )
            self.colors.append( int(config_string[1]) )
            self.colors.append( int(config_string[2]) )
            self.colors.append( int(config_string[3]) )
            self.colors.append( int(config_string[4]) )
        elif len(args) == 2 and isinstance( args[0], str ) and isinstance( args[1], str ):
            '''
            Input: 
                mystery_word - The solution of the Wordle Puzzle
                check_word - A given entry to puzzle
            Output:
                The configuration the check_word would obtain when the solution is mystery_word.
            '''
            mystery_word = args[0]
            check_word = args[1]

            self.colors = [GRAY,GRAY,GRAY,GRAY,GRAY]
            # For loop to check the Green Condition
            for char_pos, char in enumerate(check_word):
                if check_word[char_pos] != mystery_word[char_pos]:
                    continue
                
                self.colors[char_pos] = GREEN
                check_word = check_word[: char_pos] + "_" + check_word[char_pos+1:]
                mystery_word = mystery_word[: char_pos] + "_" + mystery_word[char_pos+1:]
            
            # For loop to check the Yellow Condition
            for char_pos, char in enumerate(check_word):
                if char == "_":
                    continue
                if check_word[char_pos] not in mystery_word:
                    continue

                self.colors[char_pos] = YELLOW

                mystery_char_pos = mystery_word.find( check_word[char_pos] )
                check_word = check_word[: char_pos] + "_" + check_word[char_pos+1:]
                mystery_word = mystery_word[: mystery_char_pos] + "_" + mystery_word[mystery_char_pos+1:]

        # Performing a check to test the validity of the configuration
        for color in self.colors:
            if color in [GREEN, YELLOW, GRAY]:
                continue                
            raise Exception("<Configuration>: Invalid configuration in __init__")

    def __str__(self) -> str:
        config_string = "("
        for c in self.colors:
            if c == GREEN:
                config_string += " GREEN,"
            elif c == YELLOW:
                config_string += " YELLOW,"
            else:
                config_string += " GRAY,"
        config_string += ")"
        return config_string
    
    def get_config(self):
        return tuple(self.colors)
    
class ConfigMap():
    def __init__(self, path_to_config, word_list) -> None:
        # If the configuration map is already obtained
        if os.path.isfile( path_to_config ):
            a_file = open(path_to_config, "rb")
            self.config_map = pickle.load(a_file)
            return

        # Else lets loop through all the words to find the configuration map and save the map
        self.config_map = {} # word1 -> config -> set of words
        for i, word1 in enumerate(word_list):
            print( f"Processing word {i}..." )
            for word2 in word_list:

                configuration = findWordConfiguration(word2, word1)

                if word1 not in self.config_map:
                    self.config_map[word1] = {}
                if configuration not in self.config_map[word1]:
                    self.config_map[word1][configuration] = set()
                self.config_map[word1][configuration].add(word2)
                    
        a_file = open(path_to_config, "wb")
        pickle.dump(self.config_map, a_file)
        a_file.close()

    def get_config_map(self) -> Dict:
        return self.config_map

    def word(self, word: str) -> Dict:
        if word not in self.config_map:
            raise Exception("<ConfigMap>: Invalid word")
        return self.config_map[word]

    def word_config(self, word: str, config: Tuple) -> Set:
        word_config_map = self.word(word)
        if config not in word_config_map:
            raise Exception("<ConfigMap>: Invalid word-config pair")
        return word_config_map[config]

class WordSet():
    def __init__(self, word_list) -> None:
        self.word_set = set(word_list)
    
    def __str__(self) -> str:
        return f"<Word Set Object> Size: {len(self.word_set)}"
    
    def size(self) -> int:
        return len(self.word_set)
    
    def pop(self) -> str:
        return next(iter(self.word_set))


    def reduceWordSet(self, my_word, config_map: ConfigMap, configuration: Configuration):
        set_to_intersect = config_map.word_config(my_word, configuration.get_config())
        self.word_set = self.word_set.intersection( set_to_intersect )
        if len(self.word_set) == 0:
            raise Exception("<WordSet>: No Words match the word-config pairs entered")
    
    def fraction(self, set: Set) -> float:
        return float(len(self.word_set.intersection( set ))) / len(self.word_set)

class Wordle():
    def __init__(self, path_to_config, path_to_word_list) -> None:

        self.solved = False
        self.steps = 0
        self.mystery_word = "UNSOLVED"

        self.word_list = self.load_wordlist(path_to_word_list)
        self.word_set = WordSet(self.word_list)
        self.config_map = ConfigMap(path_to_config, self.word_list)

    def __str__(self) -> str:
        string = ""
        if not self.solved:
            string = f"<Wordle Object> Unsolved, Uncertainity Size: {self.word_set.size()}"
        else:
            string = f"<Wordle Object> Solved, Mystery Word: {self.mystery_word}, Steps: {self.steps}"
        return string
    
    def solve(self):
        self.mystery_word = self.findNextWord() # obtain the next Word
        self.steps = 1
        while not self.solved:
            config = self.userConfigurationInput(f"Chosen word is {self.mystery_word}. Enter Configuration: ")
            
            if self.isCompleteConfig(config):
                self.solved = True
                break
            
            self.word_set.reduceWordSet(self.mystery_word, self.config_map, config)
            self.mystery_word = self.findNextWord() # obtain the next Word
            self.steps += 1
        return self.mystery_word

    def load_wordlist(self, path_to_file: str) -> List:
        with open(path_to_file, 'r') as f:
            return f.read().splitlines()
    
    def userConfigurationInput(self, string) -> Configuration:
        return Configuration( input(string) )
    
    def isCompleteConfig(self, config: Configuration) -> bool:
        if config.get_config() == (GREEN,GREEN,GREEN,GREEN,GREEN):
            return True
        return False

    def expectedBitsInWord( self, my_word: str ):
        expected_bits = 0.0

        for config in self.config_map.word( my_word ):

            probability = self.word_set.fraction( self.config_map.word_config(my_word, config) )
            
            bits = 0.0
            if probability != 0:
                bits = -math.log2(probability)

            expected_bits += probability * bits

        return expected_bits

    def findNextWord(self) -> str:
        if self.solved:
            return

        highest_bits = -math.inf
        next_word = ""

        for word in self.config_map.get_config_map():

            bits = self.expectedBitsInWord(word)
            if bits > highest_bits:
                highest_bits = bits
                next_word = word    

        if highest_bits == 0:
            if self.word_set.size() == 0:
                raise Exception("<Wordle>: Exception raised in findNextWord. Recheck logic...")
            self.solved = True
            self.mystery_word = self.word_set.pop()
            return self.mystery_word

        return next_word
    
    def revealMysteryWord( self ) -> str:
        if self.solved:
            return self.mystery_word
        return "UNSOLVED"

    def reset( self ) -> None:
        self.solved = False
        self.steps = 0
        self.mystery_word = "UNSOLVED"

        self.word_set = WordSet(self.word_list)

class WordleHard(Wordle):
    def __init__(self, path_to_config, path_to_word_list) -> None:
        super().__init__(path_to_config, path_to_word_list)
        
        self.prev_word = ""
        self.prev_config = Configuration()

    def __str__(self) -> str:
        string = ""
        if not self.solved:
            string = f"<WordleHard Object> Unsolved, Uncertainity Size: {self.word_set.size()}"
        else:
            string = f"<WordleHard Object> Solved, Mystery Word: {self.mystery_word}, Steps: {self.steps}"
        return string

    def solve(self):
        self.mystery_word = self.findNextWord() # obtain the next Word
        self.steps = 1
        while not self.solved:
            config = self.userConfigurationInput(f"Chosen word is {self.mystery_word}. Enter Configuration: ")
            
            if self.isCompleteConfig(config):
                self.solved = True
                break
            
            self.word_set.reduceWordSet(self.mystery_word, self.config_map, config)
            self.prev_word = self.mystery_word
            self.prev_config = config
            self.mystery_word = self.findNextWord() # obtain the next Word
            self.steps += 1
        return self.mystery_word

    def findNextWord(self) -> str:
        if self.solved:
            return

        highest_bits = -math.inf
        next_word = ""

        for word in self.config_map.get_config_map():
            if not self.isValidWord(word):
                continue
            bits = self.expectedBitsInWord(word)
            if bits > highest_bits:
                highest_bits = bits
                next_word = word    

        if highest_bits == 0:
            if self.word_set.size() == 0:
                raise Exception("<Wordle>: Exception raised in findNextWord. Recheck logic...")
            self.solved = True
            self.mystery_word = self.word_set.pop()
            return self.mystery_word

        return next_word
    
    def isValidWord(self, word) -> bool:
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

class WordleMulti(Wordle):
    def __init__(self, path_to_config, path_to_word_list, no_of_games) -> None:
        super().__init__(path_to_config, path_to_word_list)
        
        self.no_of_games = no_of_games
        self.complete = False
        self.solved = []
        self.steps = 0
        self.mystery_word = []

        word_list = self.load_wordlist(path_to_word_list)
        self.word_set = []
        for index in range(no_of_games):
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
    
    def solve(self):
        next_word = self.findNextWord() # obtain the next Word
        self.steps = 1
        while not self.complete:
            configs = self.userConfigurationInput(f"Chosen word is {next_word}. Enter Configuration: ")
            
            if self.isCompleteConfig(configs, next_word):
                self.complete = True
                break
            for game_index in range(self.no_of_games):
                self.word_set[game_index].reduceWordSet(next_word, self.config_map, configs[game_index])
            next_word = self.findNextWord() # obtain the next Word
            self.steps += 1
        return self.mystery_word

    def userConfigurationInput(self, string) -> List[Configuration]:
        configs = []
        x = input(string)
        for index in range(self.no_of_games):
            configs.append( Configuration( x[index*5:(index+1)*5] ) )
        return configs
    

    def isCompleteConfig(self, configs: List[Configuration], next_word: str) -> bool:
        returnValue = True
        for game_index in range(self.no_of_games):
            if self.solved[game_index]:
                continue
            if configs[game_index].get_config() == (GREEN,GREEN,GREEN,GREEN,GREEN):
                self.solved[game_index] = True
                self.mystery_word[game_index] = next_word
                continue
            returnValue = False
        return returnValue


    def expectedBitsInWord( self, my_word: str, game_index: int):
        expected_bits = 0.0

        for config in self.config_map.word( my_word ):

            probability = self.word_set[game_index].fraction( self.config_map.word_config(my_word, config) )
            
            bits = 0.0
            if probability != 0:
                bits = -math.log2(probability)

            expected_bits += probability * bits

        return expected_bits

    def findNextWord(self) -> str:
        if self.complete:
            return

        highest_bits = -math.inf
        next_word = ""

        for word in self.config_map.get_config_map():

            bits = 0
            for game_index in range(self.no_of_games):
                bits += self.expectedBitsInWord(word, game_index)
            # print(word, bits)
            if bits > highest_bits:
                highest_bits = bits
                next_word = word    

        if highest_bits == 0:
            self.steps -= 1
            for game_index in range(self.no_of_games):
                if self.solved[game_index]:
                    continue
                if self.word_set[game_index].size() == 0:
                    raise Exception("<Wordle>: Exception raised in findNextWord. Recheck logic...")
                self.solved[game_index] = True
                self.mystery_word[game_index] = self.word_set[game_index].pop()
                next_word = self.mystery_word[game_index]
                self.steps += 1
            self.complete = True

        return next_word

def testAlgorithm(path_to_config, path_to_word_list):
    avg_steps = 0.0
    failures = 0
    failure_list = []
    count = 0


    wordle_puzzle = Wordle(path_to_config, path_to_word_list)
    word_list = wordle_puzzle.word_list

    start = time.time()
    print("Beginning Wordle Testing...")
    for mystery_word in word_list:
        wordle_puzzle.solve()

        if wordle_puzzle.steps > 6:
            failures += 1
            failure_list.append(mystery_word)
        
        avg_steps = ((avg_steps * (count-1)) + wordle_puzzle.steps)/count

        print(f"Completed Word: {mystery_word}. Failures: {failures}. Average Steps: {avg_steps}", end="\r")

        wordle_puzzle.reset()

    print("\n")
    test_result = {}
    test_result["test_size"] = count
    test_result["time"] = time.time() - start
    test_result["average_steps"] = avg_steps
    test_result["failures"] = failures 
    test_result["failure_list"] = failure_list

    path_to_test_data = 'test3.json'
    with open(path_to_test_data, 'w') as f:
        json.dump(test_result, f)
 
    return test_result

if __name__ == "__main__":

    path_to_config = "modData.pkl"
    path_to_word_list = "wordle_words.txt"
    
    # testAlgorithm(path_to_config, path_to_word_list)

    no_of_games = 4
    wordle_puzzle = WordleMulti(path_to_config, path_to_word_list, no_of_games)
    wordle_puzzle.solve()
    print(wordle_puzzle)
