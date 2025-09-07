import cmd2
from cmd2 import style, Fg, Bg

from smolagents import Tool, tool, DuckDuckGoSearchTool

import pandas as pd
from sodapy import Socrata
from tabulate import tabulate
import collections

import random
import datetime
import os
import json
import traceback
import sys

class AgentPlugin:
    ASCII_ART_HEADER = r"""
╔═║╔═║║║║╔═╝╔═║╔═ ╔═║║  ║    ╔═║╔═╝╔═╝╔═ ═╔╝
╔═╝║ ║║║║╔═╝╔╔╝╔═║╔═║║  ║    ╔═║║ ║╔═╝║ ║ ║
╝  ══╝══╝══╝╝ ╝══ ╝ ╝══╝══╝  ╝ ╝══╝══╝╝ ╝ ╝
"""
    PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
    PLUGIN_CATEGORY = 'Plugin Commands'

    plugin_version = '0.0.0'
    plugin_date = datetime.datetime.now().strftime('%m.%d.%Y')

    def __init__(self, *args, **kwargs):
        # code placed here will execute before cmd is initialized
        try:
            plugin_info = os.path.join(self.PLUGIN_DIR, 'plugin_info.json')
            with open(plugin_info) as f:
                info = json.load(f)
                self.plugin_version = info['version']
                self.plugin_date = info['date']
        except:
            traceback.print_exc(file=sys.stdout)

        super().__init__(*args, **kwargs)
        # code placed here runs after cmd2 initializes
        # this is where you register any hook functions
        self.intro = style(self.ASCII_ART_HEADER +  f'\n\tPowerBall Agent Plugin\n\tVersion: {self.plugin_version} Date: {self.plugin_date}\n\tType "help" for more information.\n', fg=Fg.CYAN)
        self.prompt = '[PowerBall Agent]: '

    ########################################################################################################
    # Plugin Commands #
    ########################################################################################################

    def do_list_tools(self, _):
        """
        List all available tools
        """
        tools = self.get_tools()
        tool_list = [(tool.name, tool.description.strip().split('\n')[0]) for tool in tools]
        table = tabulate(tool_list, headers=["Tool Name", "Description"], tablefmt="grid")

        self.poutput(style("\nAvailable Plugin Tools", fg=Fg.CYAN))
        self.poutput(style("======================", fg=Fg.CYAN))
        self.poutput(style(table, fg=Fg.CYAN))
        self.poutput("\n")

    cmd2.categorize([do_list_tools], PLUGIN_CATEGORY)

    ########################################################################################################
    # Tools #
    ########################################################################################################

    @tool
    def powerball_query_answer(n:int = 5)-> str: #it's import to specify the return type
        #Keep this format for the description / args / args description but feel free to modify the tool
        """A tool that fetches the most recent 'n' Powerball drawings.
        Args:
            n: The number of Powerball drawings to fetch.
        Return:
            str: A string representation of the most recent 'n' Powerball drawings.
        """
        # Unauthenticated client only works with public data sets. Note 'None'
        # in place of application token, and no username or password:
        client = Socrata("data.ny.gov", None)

        # Example authenticated client (needed for non-public datasets):
        # client = Socrata(data.ny.gov,
        #                  MyAppToken,
        #                  username="user@example.com",
        #                  password="AFakePassword")

        # First n results, returned as JSON from API / converted to Python list of
        # dictionaries by sodapy.
        results = client.get("d6yy-54nr", limit=n)

        # Convert to pandas DataFrame
        results_df = pd.DataFrame.from_records(results)

        # Return the results as a string
        return results_df[["draw_date", "winning_numbers"]].to_string()

    @tool
    def powerball_creation_answer(num_drawings:int = 10, num_previous_drawings:int = 500)-> list[list[int]]:
        """
        A tool that generates new Powerball drawings based on the frequency of numbers in previous drawings.
        Args:
            num_drawings: The number of new Powerball drawings to generate.
            num_previous_drawings: The number of previous drawings to analyze for frequency.
        Return:
            list[list[int]]: A list of new Powerball drawings, each represented as a list of integers.
        """
        # Get previous drawings to analyze frequency
        client = Socrata("data.ny.gov", None)
        results = client.get("d6yy-54nr", limit=num_previous_drawings)

        # Convert to pandas DataFrame
        results_df = pd.DataFrame.from_records(results)

        drawings = results_df[["winning_numbers"]].values.tolist()
        drawings = [[int(num) for num in draw[0].split()] for draw in drawings]
        #print("Previous Powerball drawings:", drawings)

        # Separate the main numbers and the Powerball numbers
        main_numbers = [num for draw in drawings for num in draw[:5]]
        powerball_numbers = [draw[5] for draw in drawings]

        # Count the frequency of each number
        main_counts = collections.Counter(main_numbers)
        # print("Main counts:", main_counts)
        powerball_counts = collections.Counter(powerball_numbers)
        # print("Powerball counts:", powerball_counts)

        # Generate the specified number of new drawings
        # new_drawings = [generate_new_drawing(main_counts, powerball_counts) for _ in range(num_drawings)]
        new_drawings = []

        for _ in range(num_drawings):
            # Generate random numbers between 1 and 69 and weight based on frequency
            new_main_numbers = random.choices(list(main_counts.keys()), weights=list(main_counts.values()), k=5)
            new_main_numbers = [num for num in new_main_numbers if 1 <= num <= 69]

            # Ensure the new main numbers are unique
            while len(new_main_numbers) != len(set(new_main_numbers)):
                new_main_numbers = random.choices(list(main_counts.keys()), weights=list(main_counts.values()), k=5)
                new_main_numbers = [num for num in new_main_numbers if 1 <= num <= 69]

            # Generate a new Powerball number based on its frequency
            new_powerball_number = random.choices(list(powerball_counts.keys()), weights=list(powerball_counts.values()), k=1)[0]
            # Ensure the Powerball number is between 1 and 26
            while not (1 <= new_powerball_number <= 26):
                new_powerball_number = random.choices(list(powerball_counts.keys()), weights=list(powerball_counts.values()), k=1)[0]

            # Combine the new main numbers and the new Powerball number
            new_drawing = new_main_numbers + [new_powerball_number]

            # Sort the main numbers in ascending order
            new_drawing = sorted(new_drawing[:5]) + [new_drawing[5]]
            new_drawings.append(new_drawing)

        return new_drawings

    def get_tools(self)-> list:
        """
        Get all tools the agent has access to
        """
        return [DuckDuckGoSearchTool(), self.powerball_query_answer, self.powerball_creation_answer]
