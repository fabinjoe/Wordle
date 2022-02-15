
import time
from typing import List, Set
import math
import pickle
import os
import json

# Constants
GREEN = 1
YELLOW = 2
GRAY = 3

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
    for word in config_map:
        # print(f"Processing word {count}...")
        count+=1

        bits = expectedBitsInWord(word_set, word, config_map)
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

def runWordle(path_to_word_list, path_to_config):
    word_list = get_wordlist(path_to_word_list)
    print(f"List size is {len(word_list)} ")

    config_map = generateConfigurationMap(path_to_config, word_list)

    word_set = set(word_list)
    steps = 0
    while True:
        steps += 1
        next_word = findBestWord(word_set, config_map) 
        # print(next_word)
        configuration = strToTuple( input( f"Chosen word is {next_word}. Enter Configuration: " ) )
        if configuration == (1,1,1,1,1):
            mystery_word = next_word
            break
        word_set = reduceWordSet( word_set, next_word, config_map, configuration )
    
    print( f"Mystery Word '{mystery_word}' successfully found in {steps} steps." )

if __name__ == "__main__":

    path_to_word_list = "wordle_words.txt"
    path_to_config = "modData.pkl"

    runWordle(path_to_word_list, path_to_config)
    # test_result = testAlgorithm("modData.pkl", word_list)