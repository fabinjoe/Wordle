
import time
from typing import List, Set
import math
import pickle
import os
import json
import winsound
from sklearn.exceptions import NonBLASDotWarning

from tables import Unknown

GREEN = 1
YELLOW = 2
GRAY = 3

def strToTuple(string):
    return (int(string[0]), int(string[1]), int(string[2]), int(string[3]), int(string[4]))

class Wordle():
    def __init__(self, path_to_config_file, word_list) -> None:
        self.solved = False
        self.steps = 0
        self.mystery_word = ""
        self.config_map = ConfigurationMap(path_to_config_file, word_list)

        self.word_set = set(word_list)
        self.probability_curve = BitProbabilityDistribution(self.word_set, "", self.config_map)
    
    def findNextWord(self):
        highest_bits = -1.0
        next_word = ""
        for word in self.word_set:
            self.probability_curve.update_prob_dist(self.word_set, word, self.config_map)
            bits = self.probability_curve.get_expected_bits()

            if bits > highest_bits:
                highest_bits = bits
                next_word = word
        return next_word
    
    def completeEntry(self):
        self.steps += 1
        next_word = self.findNextWord()
        configuration = strToTuple( input( f"Next Word is {next_word}. Enter Configuration: " ) )

        if( configuration == (GREEN,GREEN,GREEN,GREEN,GREEN) ):
            self.solved = True
            self.mystery_word = next_word

        self.reduceWordSet( next_word, configuration )
    
    def reduceWordSet( self, word, configuration ):
        if word not in self.config_map:
            return
        if configuration not in self.config_map[word]:
            return
        self.word_set = self.word_set.intersection( self.config_map[word][configuration] )
    
    def revealMysteryWord( self ):
        if self.solved:
            return self.mystery_word
        print("Wordle Puzzle is not yet Solved")

class CheckWord():
    def __init__(self, check_word = None) -> None:
        self.check_word = check_word
        if check_word is None:
            self.check_word = ""
    
    def update_check_word(self, check_word):
        self.check_word = check_word

    def find_configuration(self, mystery_word):
        temp = self.check_word
        color = [GRAY, GRAY, GRAY, GRAY, GRAY]
        # For loop to check the Green Condition
        for char_pos, char in enumerate(self.check_word):
            if self.check_word[char_pos] != mystery_word[char_pos]:
                continue
            
            color[char_pos] = GREEN
            # checked_char.append( check_word[char_pos] )
            self.check_word = self.check_word[: char_pos] + "_" + self.check_word[char_pos+1:]
            mystery_word = mystery_word[: char_pos] + "_" + mystery_word[char_pos+1:]
        
        # For loop to check the Yellow Condition
        for char_pos, char in enumerate(self.check_word):
            if char == "_":
                continue
            if self.check_word[char_pos] not in mystery_word:
                continue

            color[char_pos] = YELLOW

            # checked_char.append( check_word[char_pos] )
            mystery_char_pos = mystery_word.find( self.check_word[char_pos] )
            self.check_word = self.check_word[: char_pos] + "_" + self.check_word[char_pos+1:]
            mystery_word = mystery_word[: mystery_char_pos] + "_" + mystery_word[mystery_char_pos+1:]
        
        self.check_word = temp
        return tuple(color)

class BitProbabilityDistribution():
    def __init__(self, word_set, my_word, config_map) -> None:
        self.expected_bits = 0.0

        self.word_set = word_set
        self.my_word = my_word
        self.config_map = config_map

    def configure_prob_dist(self):
        self.expected_bits = 0.0
        for configuration in self.config_map[self.my_word]:
            probability = float(len(self.word_set.intersection( self.config_map[self.my_word][configuration] ))) / len(self.word_set)
            bits = 0
            if probability != 0:
                bits = -math.log2(probability)

            self.expected_bits += probability * bits

    def update_prob_dist(self, word_set = None, my_word = None, config_map = None):
        if word_set is not None:
            self.word_set = word_set
        if my_word is not None:
            self.my_word = my_word
        if config_map is not None:
            self.my_word = config_map
        
        self.configure_prob_dist()

    def get_expected_bits(self):
        return self.expected_bits

class ConfigurationMap():
    def __init__(self, path_to_file, word_list) -> None:
        self.word_list = word_list
        self.path_to_file = path_to_file
    
    def calculateConfigurationMap(self):
        if os.path.isfile( self.path_to_file ):
            a_file = open( self.path_to_file, "rb")
            return pickle.load(a_file)

        # Else lets loop through all the words to find the configuration map and save the map
        config_map = {} # word1 -> config -> set of words
        
        check_word = CheckWord()
        for i, word1 in enumerate(word_list):
            print( f"Processing word {i}..." )
            check_word.update_check_word( word1 )
            for word2 in word_list:
                if word1 == word2:
                    continue

                configuration = check_word.find_configuration( word2 )
                # findWordConfiguration(word2, word1)

                if word1 not in config_map:
                    config_map[word1] = {}
                if configuration not in config_map[word1]:
                    config_map[word1][configuration] = set()
                config_map[word1][configuration].add(word2)
                    
        a_file = open(self.path_to_file, "wb")
        pickle.dump(config_map, a_file)
        a_file.close()

def get_wordlist(path_to_file):
    with open(path_to_file, 'r') as f:
        return f.read().splitlines() 

def wordInConfiguration2( mystery_word, check_word, configuration ):

    checked_char = []
    # For loop to check the Green Condition
    for char_pos, color in enumerate(configuration):
        if color != GREEN:
            continue
        if check_word[char_pos] != mystery_word[char_pos]:
            # print("Green False")
            return False

        # checked_char.append( check_word[char_pos] )
        check_word = check_word[: char_pos] + "_" + check_word[char_pos+1:]
        mystery_word = mystery_word[: char_pos] + "_" + mystery_word[char_pos+1:]
    
    # For loop to check the Yellow Condition
    for char_pos, color in enumerate(configuration):
        if color != YELLOW:
            continue
        if check_word[char_pos] not in mystery_word:
            # print("Yello False")
            return False

        # checked_char.append( check_word[char_pos] )
        mystery_char_pos = mystery_word.find( check_word[char_pos] )
        check_word = check_word[: char_pos] + "_" + check_word[char_pos+1:]
        mystery_word = mystery_word[: mystery_char_pos] + "_" + mystery_word[mystery_char_pos+1:]
    
    # For loop to check the Gray Condition
    for char_pos, color in enumerate(configuration):
        # print(char_pos, check_word, mystery_word)
        if color != GRAY:
            continue

        if check_word[char_pos] in mystery_word:
            # print(f"Gray False: {check_word} - {mystery_word} ")
            return False
            
    return True

def findWordConfiguration( mystery_word, check_word ):
    checked_char = []
    color = [3,3,3,3,3]
    # For loop to check the Green Condition
    for char_pos, char in enumerate(check_word):
        if check_word[char_pos] != mystery_word[char_pos]:
            continue
        
        color[char_pos] = GREEN
        # checked_char.append( check_word[char_pos] )
        check_word = check_word[: char_pos] + "_" + check_word[char_pos+1:]
        mystery_word = mystery_word[: char_pos] + "_" + mystery_word[char_pos+1:]
    
    # For loop to check the Yellow Condition
    for char_pos, char in enumerate(check_word):
        if char == "_":
            continue
        if check_word[char_pos] not in mystery_word:
            continue

        color[char_pos] = YELLOW

        # checked_char.append( check_word[char_pos] )
        mystery_char_pos = mystery_word.find( check_word[char_pos] )
        check_word = check_word[: char_pos] + "_" + check_word[char_pos+1:]
        mystery_word = mystery_word[: mystery_char_pos] + "_" + mystery_word[mystery_char_pos+1:]
                
    return tuple(color)

def obtainConfigurationProbability( word_set, my_word, config_map, configuration ):
    count = 0
    if configuration in config_map[my_word]:
        count = float(len(word_set.intersection( config_map[my_word][configuration] )))
    return count / len(word_set)

def expectedBitsInWord( word_set, my_word, config_map ):

    expected_bits = 0.0

    for configuration in config_map[my_word]:
        probability = float(len(word_set.intersection( config_map[my_word][configuration] ))) / len(word_set)
        bits = 0
        if probability != 0:
            bits = -math.log2(probability)

        expected_bits += probability * bits

    return expected_bits

def findBestWord(word_set, config_map):
    highest_bits = -1.0
    best_word = ""
    count = 1
    for word in word_set:
        # print(f"Processing word {count}...")
        count+=1

        bits = expectedBitsInWord(word_set, word, config_map)
        if bits > highest_bits:
            highest_bits = bits
            best_word = word
    return best_word

def reduceWordSet(word_set, my_word, config_map, configuration):
    return word_set.intersection( config_map[my_word][configuration] )

def generateConfigurationMap(path_to_config, word_list):
    # If the configuration map is already obtained
    if os.path.isfile( path_to_config ):
        a_file = open(path_to_config, "rb")
        return pickle.load(a_file)

    # Else lets loop through all the words to find the configuration map and save the map
    config_map = {} # word1 -> config -> set of words
    for i, word1 in enumerate(word_list):
        print( f"Processing word {i}..." )
        for word2 in word_list:
            if word1 == word2:
                continue

            configuration = findWordConfiguration(word2, word1)

            if word1 not in config_map:
                config_map[word1] = {}
            if configuration not in config_map[word1]:
                config_map[word1][configuration] = set()
            config_map[word1][configuration].add(word2)
                
    a_file = open(path_to_config, "wb")
    pickle.dump(config_map, a_file)
    a_file.close()

    return config_map

def testAlgorithm(path_to_config, word_list):
    avg_steps = 0.0
    failures = 0
    failure_list = []
    count = 0

    config_map = generateConfigurationMap(path_to_config, word_list)

    start = time.time()
    print("Beginning Wordle Testing...")
    for mystery_word in word_list:
        count += 1

        # Solve for the mystery word
        word_set = set(word_list)
        steps = 0
        while True:
            steps += 1
            next_word = findBestWord(word_set, config_map) 
            # print(next_word)
            configuration = findWordConfiguration( mystery_word, next_word )
            if configuration == (1,1,1,1,1):
                break
            word_set = reduceWordSet( word_set, next_word, config_map, configuration )
        
        if steps > 6:
            failures += 1
            failure_list.append(mystery_word)
        avg_steps = ((avg_steps * (count-1)) + steps)/count

        print(f"Completed Word: {mystery_word}. Failures: {failures}. Average Steps: {avg_steps}", end="\r")
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
    word_list = get_wordlist("wordle_words.txt")
    print(f"List size is {len(word_list)} ")

    wordle_puzzle = Wordle("modData.pkl", word_list)

    print(wordle_puzzle.findNextWord())
    # test_result = testAlgorithm("modData.pkl", word_list)
    # winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)


# Try 1 Error
#     print(len(['admit', 'adopt', 'adore', 'agile', 'aider', 'angry', 'argue', 'azure', 'badly', 'baler', 'bayou', 'bleat', 'bound', 'brine', 'buggy', 'bunch', 'buxom', 'cache', 'cedar', 'chart', 'cheap', 'chore', 'clear', 'clerk', 'comfy', 'cramp', 'credo', 'cried', 'dance', 
# 'daunt', 'debar', 'dingo', 'drank', 'eclat', 'ember', 'enjoy', 'epoxy', 'essay', 'ethic', 'ethos', 'every', 'evoke', 'fetus', 'fibre', 'fiery', 'flaky', 'flare', 'foamy', 'fraud', 'fried', 'frown', 'gecko', 'giant', 'glare', 'gnash', 'graze', 'gripe', 'guide', 'gummy', 'happy', 'hilly', 'holly', 'homer', 'hyena', 'ideal', 'jazzy', 'joker', 'knead', 'lefty', 'light', 'loamy', 'loath', 'lowly', 'lucid', 'maker', 'mammy', 'maple', 'match', 'micro', 'midst', 'mound', 'mucky', 'night', 'noise', 'nudge', 'ocean', 'ombre', 'opera', 'owner', 'paste', 'patch', 'pitch', 'pizza', 'primo', 'prize', 'prove', 'quark', 'query', 'saint', 'saner', 'sappy', 'saucy', 'saute', 'scaly', 'scare', 'score', 'scout', 'shady', 'shank', 'shave', 'smear', 'snare', 'snore', 'soapy', 'spawn', 'spear', 'stain', 'stamp', 'stare', 'swear', 'sweat', 'tally', 'tense', 'their', 'tower', 'tried', 'truer', 'tweak', 'ultra', 'umbra', 'usage', 'usher', 'wacky', 'watch', 'weary', 'wooer', 'zebra']))
