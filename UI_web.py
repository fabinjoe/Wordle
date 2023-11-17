from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pynput.keyboard import Key, Controller
import mouse

from UI import UI
from elements import WORD_SIZE


CROMEDRIVER_PATH = "C:\Program Files (x86)\chromedriver.exe"

WORDLE_PATH = "https://www.nytimes.com/games/wordle/index.html"
WORDLE_START_COORDINATES = (450, 150)
WORDLE_X_DIFF = 84
WORDLE_Y_DIFF = 84
WORDLE_WAIT_TIME = 2

DORDLE_PATH = "https://zaratustra.itch.io/dordle"
DORDLE_START_COORDINATES = (295, 115)
DORDLE_X_DIFF = 68
DORDLE_Y_DIFF = 65
DORDLE_WAIT_TIME = 0.23

class WordleBrowserUI(UI):
    def __init__(self, wordle_object: WordlePuzzle, suppress_error_check: bool = False) -> None:
        if not suppress_error_check and wordle_object.getPuzzleSize() != 1:
            raise Exception("<WordleBrowserUI> Wordle Puzzle is not compatable with the UI.") 

        super().__init__(wordle_object)
        self.name = "WordleBrowserUI"

    def launchBrowser(self):
        self.driver = webdriver.Chrome(CROMEDRIVER_PATH)
        self.driver.get( WORDLE_PATH )

        self.keyboard = Controller()
        mouse.move(100, 500, absolute=True, duration=0.2)
        mouse.click('left')

        self.start_cord = WORDLE_START_COORDINATES
        self.x_diff = WORDLE_X_DIFF
        self.y_diff = WORDLE_Y_DIFF
        self.wait_time = WORDLE_WAIT_TIME

    def quitBrowser(self):
        time.sleep(2)
        self.driver.quit()

    def solve(self):
        self.launchBrowser()        
        super().solve()
        self.quitBrowser()

    def enterWordEntry(self, my_word) -> None:
        '''Types a given 'my_word' using the laptop keyboard.'''
        for char in my_word:
            self.keyboard.press( char )
            self.keyboard.release( char )
            time.sleep(0.12)
        self.keyboard.press( Key.enter )
        self.keyboard.release( Key.enter )
        time.sleep(self.wait_time)

    def obtainConfiguration(self):
        '''Uses image proccessing to identify the configuration of the entered my_word.'''
        def findColor(screenshot, x_coordinate, y_coordinate):
            color = screenshot[y_coordinate, x_coordinate, :3]
            red = int(color[0] * 10)
            green = int(color[1] * 10)
            blue = int(color[2] * 10)

            if red == green and red == blue:
                return "3"
            elif red > 5:
                return "2"
            return "1"

        self.driver.save_screenshot("ss.png")
        screenshot = plt.imread("ss.png")
        config = ""

        y = self.start_cord[1] + (self.wordle_puzzle.steps - 1 ) * self.y_diff
        for i in range(WORD_SIZE * self.wordle_puzzle.getPuzzleSize()):
            x = self.start_cord[0] + i * self.x_diff

            config += findColor(screenshot, x, y)

        return config

class DordleBrowserUI(WordleBrowserUI):
    def __init__(self, wordle_object: WordleMultiPuzzle, suppress_error_check: bool = False) -> None:
        if not suppress_error_check and wordle_object.getPuzzleSize() != 2:
            raise Exception("<DordleBrowserUI> Wordle Puzzle is not compatable with the UI.") 

        super().__init__(wordle_object, suppress_error_check=True)

    def launchBrowser(self):
        self.driver = webdriver.Chrome(CROMEDRIVER_PATH)
        self.driver.get( DORDLE_PATH )

        self.keyboard = Controller()
        mouse.move(500, 400, absolute=True, duration=0.2)
        mouse.click('left')

        self.start_cord = DORDLE_START_COORDINATES
        self.x_diff = DORDLE_X_DIFF
        self.y_diff = DORDLE_Y_DIFF
        self.wait_time = DORDLE_WAIT_TIME
