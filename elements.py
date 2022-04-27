
import os
import math
import pickle

WORD_SIZE = 5
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
    
    def get_config(self) -> tuple:
        '''Returns the configuration in Tuple Format'''
        return tuple(self.colors)
    
    def isComplete(self) -> bool:
        '''Checks the configuration is all GREEN'''
        if self.get_config() == (GREEN,GREEN,GREEN,GREEN,GREEN):
            return True
        return False

    
class ConfigMap():
    '''
    Represents a lookup-table that related words to other words based on the 
    configuration that would be generated
    '''
    def __init__(self, path_to_config: str, possible_word_list: list[str] = None, accepted_word_list: list[str] = None) -> None:
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
        if possible_word_list == None:
            raise Exception("<ConfigMap>: Unable to create configuration map without a list of possible words")
        if accepted_word_list == None:
            accepted_word_list = possible_word_list

        self.createConfigMap(possible_word_list, accepted_word_list)
    
        # Store the computed config map to reduce time on later runs
        a_file = open(path_to_config, "wb")
        pickle.dump(self.config_map, a_file)
        a_file.close()

    def createConfigMap(self, possible_word_list: list[str], accepted_word_list: list[str]) -> None:
        # check_word -> config -> set of mystery_word
        self.config_map = {} 

        for i, check_word in enumerate(accepted_word_list):
            print( f"Processing word {i}..." )
            for mystery_word in possible_word_list:

                configuration = Configuration(mystery_word, check_word)

                if check_word not in self.config_map:
                    self.config_map[check_word] = {}
                if configuration.get_config() not in self.config_map[check_word]:
                    self.config_map[check_word][configuration.get_config()] = set()
                self.config_map[check_word][configuration.get_config()].add( mystery_word )
                    

    def get_config_map(self) -> dict[str, dict[tuple, set]]:
        '''Returns the complete config map.'''
        return self.config_map

    def word(self, word: str) -> dict[tuple, set[str]]:
        '''Returns all possible configs that 'word' can generate, and the mystery_words associated with each config.'''
        if word not in self.config_map:
            raise Exception("<ConfigMap>: Invalid word")
        return self.config_map[word]

    def word_config(self, word: str, config: tuple) -> set[str]:
        '''Returns the set of mystery_words that satisfy a given 'word' and 'config'.'''
        word_config_map = self.word(word)
        if config not in word_config_map:
            raise Exception("<ConfigMap>: Invalid word-config pair")
        return word_config_map[config]

class WordSet():
    '''Represents the sample space of possible answers to the puzzle.'''
    def __init__(self, word_list: list[str]) -> None:
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

    def reduceWordSet(self, my_word: str, config_map: ConfigMap, configuration: Configuration) -> None:
        '''
        Reduce the set of possible answers once we make a guess(my_word) and recieve
        feedback on the guess(configuration).
        '''
        set_to_intersect = config_map.word_config(my_word, configuration.get_config())
        self.word_set = self.word_set.intersection( set_to_intersect )
        if len(self.word_set) == 0:
            raise Exception("<WordSet>: No Words match the word-config pairs entered")
    
    def fraction(self, set: set[str]) -> float:
        '''Returns the fraction of possible answers that are in 'set' to the total possible answers.'''
        return float(len(self.word_set.intersection( set ))) / len(self.word_set)
    
    def expectedBitsInWord( self, config_map: ConfigMap, my_word: str ) -> float:
        '''Returns the expected bits(information) that can be provided by a given 'my_word'.'''
        # Using a concept from information theory: bits
        # Where bits = - logbase2( probability )
        # And the expected bits = Summation( probabilty * bits )
        expected_bits = 0.0
        for config in config_map.word( my_word ):

            probability = self.fraction( config_map.word_config(my_word, config) )
            
            bits = 0.0
            if probability != 0:
                bits = -math.log2(probability)

            expected_bits += probability * bits

        return expected_bits

    # def findBestPair(self, config_map: ConfigMap):
    #     expected_bits = 0.0
    #     highest_bit = 0.0
    #     for config in config_map.word( my_word ):
    #         pass

def load_wordlist(path_to_file: str) -> list[str]:
    '''Loads the list of words to the program.'''
    with open(path_to_file, 'r') as f:
        return f.read().splitlines()

