
from elements import load_wordlist, ConfigMap
from puzzle import WordlePuzzle, WordleHardPuzzle, WordleMultiPuzzle
from UI import TerminalUI, WordleBrowserUI, DordleBrowserUI

# Wordle Browser Constants
CONFIGURATION_MAP_PATH = "master_wordle_data.pkl"
POSSIBLE_WORD_LIST_PATH = "wordle_words.txt"
ACCEPTED_WORD_LIST_PATH = "all_words.txt"

if __name__ == "__main__":

    possible_words = load_wordlist(POSSIBLE_WORD_LIST_PATH)
    accepted_words = load_wordlist(ACCEPTED_WORD_LIST_PATH)

    configuration_map = ConfigMap(CONFIGURATION_MAP_PATH, possible_words, accepted_words)

    wordle_puzzle = WordlePuzzle(configuration_map, possible_words)
    browser = WordleBrowserUI(wordle_puzzle)
    
    browser.solve()

    print(browser)
