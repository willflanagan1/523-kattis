import os
import unittest
from selenium import webdriver

class ChromeTests(unittest.TestCase):

    # Prerequisite: install ChromeDriver to tests directory
    # at https://sites.google.com/chromium.org/driver/downloads?authuser=0
    # Testing configured for local development
    # Configure port to your local instance

    def setup():
        os.chmod('./chromedriver', 755)
        driver = webdriver.Chrome('./chromedriver')

    def getHome():
        driver.get('http://localhost:{your-port}/')

    def postSubmitAsStudent():
        mockSubmission = {'mock submissions object'}
        driver.post('http://localhost:{your-port}/problem/1', mockSubmission)

    def getSubmitsAsStudent():
        driver.get('http://localhost:{your-port}/submittedproblems')
    
    def postProblemAsAdmin():
        mockProblem = {'mock problem object'}
        driver.post('http://localhost:{your-port}/create-problem', mockProblem)

    def getProblemsAsAdmin():
        driver.get('http://localhost:{your-port}/problems')


    if __name__ == "__main__":
        unittest.main()