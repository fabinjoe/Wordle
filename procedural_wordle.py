
from lib2to3.pgen2 import driver
from re import search
import time 
from typing import List, Set
import math
import pickle
import os
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from urllib3 import Retry

# Constants
GREEN = 1
YELLOW = 2
GRAY = 3

EASY = 0
HARD = 1
DOUBLE = 2

PATH = "C:\Program Files (x86)\chromedriver.exe"

def strToTuple(string):
    #Converts string user input '33133' to tuple (3,3,1,3,3). Output: Tuple of size 5.
    return (int(string[0]), int(string[1]), int(string[2]), int(string[3]), int(string[4]))

def get_wordlist(path_to_file):
    with open(path_to_file, 'r') as f:
        return f.read().splitlines() 

def findWordConfiguration( mystery_word, check_word ):
    '''
    Input: 
        mystery_word - The solution of the Wordle Puzzle
        check_word - A given entry to puzzle
    Output:
        The configuration the check_word would obtain when the solution is mystery_word.
    '''
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

# def obtainConfigurationProbability( word_set, my_word, config_map, configuration ):
    count = 0
    if configuration in config_map[my_word]:
        count = float(len(word_set.intersection( config_map[my_word][configuration] )))
    return count / len(word_set)
    
def expectedBitsInWord( word_set, my_word, config_map, ):
    # if( len(word_set) == 0 ):
    #     return 0.0

    expected_bits = 0.0

    for configuration in config_map[my_word]:
        probability = float(len(word_set.intersection( config_map[my_word][configuration] ))) / len(word_set)
        
        bits = 0.0
        # if depth > 1:
        #     mod_word_set = reduceWordSet(word_set, my_word, config_map, configuration)
        #     bits = expectedBitsInWord( mod_word_set, my_word, config_map, depth-1 )
        # else:
        if probability != 0:
            bits = -math.log2(probability)

        expected_bits += probability * bits

    return expected_bits

def wordLegalForHard(my_word, must_use):
    for i in range(len(my_word)):
        if my_word[i] in must_use:
            must_use.remove(my_word[i])
    return len(must_use) == 0

def generateMustUse(my_word, configuration):
    must_use = []
    for i, color in enumerate(configuration):
        if color == GRAY:
            continue
        must_use.append(my_word[i])
    return must_use

def findBestWord(word_set, config_map, mode=EASY, must_use=None, second_word_set=None):
    highest_bits = -1.0
    best_word = ""
    for word in config_map:
        
        if mode == HARD:
            # print("HELLLO")
            # temp_must_use = must_use.copy()
            if not wordLegalForHard(word, must_use.copy()):
                continue

        bits = expectedBitsInWord(word_set, word, config_map)
        if mode == DOUBLE:
            bits += expectedBitsInWord(second_word_set, word, config_map)
        if bits > highest_bits:
            highest_bits = bits
            best_word = word
    
    if highest_bits == 0:
        if len(word_set) == 0:
            print("Error in Code, or word not in word_list. Recheck logic...")
        return word_set.pop()
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

def testAlgorithm(word_list, config_map, mode):
    avg_steps = 0.0
    failures = 0
    failure_list = []
    count = 0

    start = time.time()
    print("Beginning Wordle Testing...")
    for mystery_word in word_list:
        count += 1

        # Solve for the mystery word
        word_set = set(word_list)
        steps = 0
        must_use = []
        while True:
            steps += 1
            next_word = findBestWord(word_set, config_map, mode, must_use) 
            # print(next_word)
            configuration = findWordConfiguration( mystery_word, next_word )
            if configuration == (1,1,1,1,1):
                break
            word_set = reduceWordSet( word_set, next_word, config_map, configuration )
            must_use = generateMustUse( next_word, configuration )

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

    path_to_test_data = 'test_hard1.json'
    with open(path_to_test_data, 'w') as f:
        json.dump(test_result, f)
 
    return test_result

def runWordle(word_list, config_map, mode = EASY):
    word_set = set(word_list)
    steps = 0

    if mode == HARD:
        prev_word = ""
        prev_config = ()
    
    if mode == DOUBLE:
        double_word_set = set(word_list)

    while True:
        steps += 1
        # FInding the next best word
        if mode == EASY:
            next_word = findBestWord(word_set, config_map, mode) 
        elif mode == HARD:
            next_word = findBestWord(word_set, config_map, mode, must_use) 
        elif mode == DOUBLE:
            pass

        # Obtaining the user input on the configuration
        configuration = strToTuple( input( f"Chosen word is {next_word}. Enter Configuration: " ) )
        if mode == DOUBLE:
            second_configuration = strToTuple( input( f"Chosen word is {next_word}. Enter Second Configuration: " ) )

        # Exit from the loop once wordle is completed
        if configuration == (0,0,0,0,0):
            mystery_word = next_word
            break

        # Reduce the word set and modify any other information for the different modes
        word_set = reduceWordSet( word_set, next_word, config_map, configuration )

        if mode == DOUBLE and second_configuration != (1,1,1,1,1):
            second_word_set = reduceWordSet( second_word_set, next_word, config_map, second_configuration )
        must_use = generateMustUse( next_word, configuration )
    
    print( f"Mystery Word '{mystery_word}' successfully found in {steps} steps." )

def solveDailyWordle(path_to_word_list, path_to_config):
    driver = webdriver.Chrome(PATH)

    driver.get("https://www.nytimes.com/games/wordle/index.html")
    search = driver.find_element_by_class("close-icon")
    # print(type(search)) 

    search.click()

    # time.sleep(5)

def loadWordle(path_to_word_list, path_to_config):
    word_list = get_wordlist(path_to_word_list)
    print(f"List size is {len(word_list)} ")

    config_map = generateConfigurationMap(path_to_config, word_list)
    return word_list, config_map


if __name__ == "__main__":

    path_to_word_list = "wordle_words.txt"
    path_to_config = "modData.pkl"

    word_list, config_map = loadWordle(path_to_word_list, path_to_config)
    runWordle(word_list, config_map, mode=EASY)
    # solveDailyWordle(path_to_word_list, path_to_config)
    # test_result = testAlgorithm(word_list, config_map, mode=HARD)