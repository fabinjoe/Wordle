
from typing import Dict, List, Set, Tuple
import os
import time
import math
import pickle
import matplotlib.pyplot as plt

from selenium import webdriver
from pynput.keyboard import Key, Controller
import mouse

PATH = "C:\Program Files (x86)\chromedriver.exe"

GREEN = 1
YELLOW = 2
GRAY = 3

class Configuration():
    '''Represents a possible response for an entered WORD in the puzzle'''
    def __init__(self, *args) -> None:
        ''' This object can be initialized in multiple ways
        1: Configuration(): This will return a dufault all GRAY configuration.
        2: Configuration(config_str: str): This will use a config string '11233' to create a Configuration Object.
        3: Configuration(mystery_word: str, check_word: str): This will create the configuration that would be generated
            if the answer to the puzzle was 'mystery_word' and the user entered 'check_word'.
        '''
        # 1. Configuration()
        if len(args) == 0:
            self.colors = [GRAY,GRAY,GRAY,GRAY,GRAY]
        # 2. Configuration(config_str: str)
        elif len(args) == 1 and isinstance( args[0], str ): 
            config_string = args[0]
            self.colors = []
            self.colors.append( int(config_string[0]) )
            self.colors.append( int(config_string[1]) )
            self.colors.append( int(config_string[2]) )
            self.colors.append( int(config_string[3]) )
            self.colors.append( int(config_string[4]) )
        # 3. Configuration(mystery_word: str, check_word: str)
        elif len(args) == 2 and isinstance( args[0], str ) and isinstance( args[1], str ):
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
        '''Returns the configuration in Tuple Format'''
        return tuple(self.colors)
    
class ConfigMap():
    '''
    Represents a lookup-table that related words to other words based on the 
    configuration that would be generated
    '''
    def __init__(self, path_to_config, word_list) -> None:
        ''' We will look at 'path_to_config' to check if the config map has been precomputed:
        If it is precomputed, then load it to the object.
        If not, then compute the config map.
        '''
        # If the configuration map is already obtained
        if os.path.isfile( path_to_config ):
            a_file = open(path_to_config, "rb")
            self.config_map = pickle.load(a_file)
            return

        # Else lets loop through all the words to find the configuration map and save the map

        # check_word -> config -> set of mystery_word
        self.config_map = {} 
        for i, check_word in enumerate(word_list):
            print( f"Processing word {i}..." )
            for mystery_word in word_list:

                configuration = Configuration(mystery_word, check_word)

                if check_word not in self.config_map:
                    self.config_map[check_word] = {}
                if configuration.get_config() not in self.config_map[check_word]:
                    self.config_map[check_word][configuration.get_config()] = set()
                self.config_map[check_word][configuration.get_config()].add( mystery_word )
                    
        # Store the computed config map to reduce time on later runs
        a_file = open(path_to_config, "wb")
        pickle.dump(self.config_map, a_file)
        a_file.close()

    def get_config_map(self) -> Dict:
        '''Returns the complete config map.'''
        return self.config_map

    def word(self, word: str) -> Dict:
        '''Returns all possible configs that 'word' can generate, and the mystery_words associated with each config.'''
        if word not in self.config_map:
            raise Exception("<ConfigMap>: Invalid word")
        return self.config_map[word]

    def word_config(self, word: str, config: Tuple) -> Set:
        '''Returns the set of mystery_words that satisfy a given 'word' and 'config'.'''
        word_config_map = self.word(word)
        if config not in word_config_map:
            raise Exception("<ConfigMap>: Invalid word-config pair")
        return word_config_map[config]

class WordSet():
    '''Represents the sample space of possible answers to the puzzle.'''
    def __init__(self, word_list) -> None:
        '''Create a set with a list of all possible answers.'''
        self.word_set = set(word_list)
    
    def __str__(self) -> str:
        return f"<Word Set Object> Size: {len(self.word_set)}"
    
    def size(self) -> int:
        '''Return the number of possible answers.'''
        return len(self.word_set)
    
    def pop(self) -> str:
        '''Return the set of possible answers.'''
        return next(iter(self.word_set))

    def reduceWordSet(self, my_word, config_map: ConfigMap, configuration: Configuration):
        '''
        Reduce the set of possible answers once we make a guess(my_word) and recieve
        feedback on the guess(configuration).
        '''
        set_to_intersect = config_map.word_config(my_word, configuration.get_config())
        self.word_set = self.word_set.intersection( set_to_intersect )
        if len(self.word_set) == 0:
            raise Exception("<WordSet>: No Words match the word-config pairs entered")
    
    def fraction(self, set: Set) -> float:
        '''Returns the fraction of possible answers that are in 'set' to the total possible answers.'''
        return float(len(self.word_set.intersection( set ))) / len(self.word_set)

class Wordle():
    '''Represts a classic Wordle Puzzle'''
    def __init__(self, path_to_config, path_to_word_list) -> None:
        '''Require path to list of words and config map to initialize the variables.'''
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
        '''Begins a feedback loop, wherein the program suggests the next best word, and requests
        the user to enter the obtained configuration output.'''
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
        '''Loads the list of words to the program.'''
        with open(path_to_file, 'r') as f:
            return f.read().splitlines()
    
    def userConfigurationInput(self, string) -> Configuration:
        '''Obtains a user input on the recieved configuration, and returns a Configuration Object'''
        return Configuration( input(string) )
    
    def isCompleteConfig(self, config: Configuration) -> bool:
        '''Checks wether the puzzle has been solved'''
        if config.get_config() == (GREEN,GREEN,GREEN,GREEN,GREEN):
            return True
        return False

    def expectedBitsInWord( self, my_word: str ):
        '''Returns the expected bits(information) that can be provided by a given 'my_word'.'''
        # Using a concept from information theory: bits
        # Where bits = - logbase2( probability )
        # And the expected bits = Summation( probabilty * bits )

        expected_bits = 0.0
        for config in self.config_map.word( my_word ):

            probability = self.word_set.fraction( self.config_map.word_config(my_word, config) )
            
            bits = 0.0
            if probability != 0:
                bits = -math.log2(probability)

            expected_bits += probability * bits

        return expected_bits

    def findNextWord(self) -> str:
        '''Returns the best next word, given the current state of the puzzle'''

        # If the puzzle is solved then this function has no purpose and hence returns empty
        if self.solved:
            return

        # Find which word give the highest bits, ie would provide the most information.
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
        '''Returns the answer of the puzzle, if solved.'''
        if self.solved:
            return self.mystery_word
        return "UNSOLVED"

    def reset( self ) -> None:
        '''Resets the variables of the puzzle.'''
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

class WordleBrowser():
    def __init__(self, path_to_config, path_to_word_list, path_to_char_to_cord) -> None:

        self.wordle_puzzle = Wordle(path_to_config, path_to_word_list)
        self.loadCharToCord(path_to_char_to_cord)

        self.driver = webdriver.Chrome(PATH)
        self.driver.get( "https://www.nytimes.com/games/wordle/index.html" )

        mouse.move(100, 500, absolute=True, duration=0.2)
        mouse.click('left')
        self.keyboard = Controller()

    def __str__(self) -> str:
        string = ""
        if not self.wordle_puzzle.solved:
            string = f"<WordleBrowser Object> Unsolved, Uncertainity Size: {self.wordle_puzzle.word_set.size()}"
        else:
            string = f"<WordleBrowser Object> Solved, Mystery Word: {self.wordle_puzzle.mystery_word}, Steps: {self.wordle_puzzle.steps}"
        return string

    def loadCharToCord(self, path_to_char_to_cord):
        with open(path_to_char_to_cord, 'rb') as f:
            self.char_to_cord = pickle.load(f)


    def solve(self):
        self.wordle_puzzle.mystery_word = self.wordle_puzzle.findNextWord() # obtain the next Word
        self.enterNextWord( self.wordle_puzzle.mystery_word )
        steps = 1
        while not self.wordle_puzzle.solved:
            # config = self.wordle_puzzle.userConfigurationInput(f"Chosen word is {self.mystery_word}. Enter Configuration: ")
            config = self.findConfig(self.wordle_puzzle.mystery_word)

            if self.wordle_puzzle.isCompleteConfig(config):
                self.solved = True
                break
            
            self.wordle_puzzle.word_set.reduceWordSet(self.wordle_puzzle.mystery_word, self.wordle_puzzle.config_map, config)
            self.wordle_puzzle.mystery_word = self.wordle_puzzle.findNextWord() # obtain the next Word
            self.enterNextWord( self.wordle_puzzle.mystery_word )
            self.wordle_puzzle.steps += 1
        return self.wordle_puzzle.mystery_word

    def enterNextWord(self, my_word):
        '''Types a given 'my_word' using the laptop keyboard.'''
        for char in my_word:
            self.keyboard.press( char )
            self.keyboard.release( char )
            time.sleep(0.12)
        self.keyboard.press( Key.enter )
        self.keyboard.release( Key.enter )
        time.sleep(2)

    def findConfig(self, my_word):
        '''Uses image proccessing to identify the configuration of the entered my_word.'''
        self.driver.save_screenshot("ss.png")
        screenshot = plt.imread("ss.png")
        config = ""
        for char in my_word:
            x = self.char_to_cord[char][0]
            y = self.char_to_cord[char][1]
            color = screenshot[y, x, :3]
            red = int(color[0] * 10)
            green = int(color[1] * 10)
            blue = int(color[2] * 10)
            
            if red == green and green == blue:
                config += "3"
            elif red > 5:
                config += "2"
            else:
                config += "1"
        return Configuration(config)
    
    def quitBrowser(self):
        self.driver.quit()

if __name__ == "__main__":

    path_to_config = "wordle_data.pkl"
    path_to_word_list = "wordle_words.txt"
    path_to_char_to_cord = "wordle_char_to_coordinates.pkl"
    
    # testAlgorithm(path_to_config, path_to_word_list)

    # no_of_games = 4
    wordle_puzzle = WordleBrowser(path_to_config, path_to_word_list, path_to_char_to_cord)
    wordle_puzzle.solve()
    print()
    print(wordle_puzzle)
    print()

    time.sleep(4)
    wordle_puzzle.quitBrowser()

