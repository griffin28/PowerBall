import cmd2
from cmd2 import style, Fg

from agent_plugin import AgentPlugin

import argparse
import sys
import os
import warnings
warnings.filterwarnings("ignore", category=Warning)
import traceback

import json
from typing import override

from smolagents import CodeAgent, MultiStepAgent, HfApiModel, PromptTemplates

class AgentShell(AgentPlugin, cmd2.Cmd, object):
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    AGENT_CATEGORY = 'Agent Commands'

    agent = None
    agent_type = None
    model_id = None

    def __init__(self):
        super(AgentShell, self).__init__(persistent_history_file=os.getenv('HOME') + '/.self_healing_history.dat')

        try:
            model_config = os.path.join(self.APP_DIR, 'conf/model_config.json')
            with open(model_config) as f:
                config = json.load(f)
                model_id = config['model_id']
                agent_type = config['agent_type']
                self._create_agent(agent_type, model_id)
        except:
            traceback.print_exc(file=sys.stdout)

        # self.prompt = '[Agent]: '
        self.debug = False
        self.ruler = '='
        self.locals_in_py = True
        self.default_category = 'Default Commands'

    @override
    def precmd(self, line):
        """
        Check for special character/operator commands

        :param line: command line
        :return: line
        """

        return line

    @override
    def postcmd(self, stop, line):
        """
        Save current state for undo/redo

        :param stop: stop flag
        :param line: command line
        :return: stop
        """
        return stop

    def do_shell(self, line):
        """
        Execute shell commands
        """

        os.system(line)

    def help_shell(self):
        print("\n   Procedure: Execute shell commands. The symbol \'!\' is a synonym for \'shell\'."
              "\n   Usage: <shell> <command>\n")

    ########################################################################################################
    # default command functions #
    ########################################################################################################

    def do_debug(self, line):
        """
        Turn on debug tracebacks for commands
        """

        try:
            line = line.strip()
            if line == '0' or line.upper() == 'OFF':
                self.debug = False
            elif line == '1' or line.upper() == 'ON':
                self.debug = True
            else:
                print('invalid input: requires on or off as argument')
        except:
            if self.debug:
                traceback.print_exc(file=sys.stdout)

    def help_debug(self):
        print('\n   Variable: Show debug tracebacks if True\n   Usage: debug on | off\n')

    def do_intro(self, _):
        """
        Display the introduction message
        """

        self.poutput(self.intro)

    def do_load_documents(self, line):
        """
        Load documents in the vector database
        """

        self.poutput('Loading documents...')

    def help_load_documents(self):
        print('\n   Procedure: Load documents in the vector database\n'
              '   Usage: load_documents <list_of_documents>\n')

    ########################################################################################################
    # agent command functions #
    ########################################################################################################

    # do_create_agent parser
    create_agent_parser = cmd2.Cmd2ArgumentParser(description='Create a new agent')
    create_agent_parser.add_argument('-t', '--type', choices=['local', 'hf', 'openai'], required=True, help='agent type')
    create_agent_parser.add_argument('-m', '--model', required=True, help='model name')

    @cmd2.with_argparser(create_agent_parser)
    def do_create_agent(self, args: argparse.Namespace):
        """
        Create a new agent
        """
        self._create_agent(args.type, args.model)

    # do-run parser
    run_parser = cmd2.Cmd2ArgumentParser(description='Run the agent')
    run_parser.add_argument('-t', '--task', required=True, help='task to run')
    run_parser.add_argument('-r', '--reset', action='store_true', help='reset the conversation')

    @cmd2.with_argparser(run_parser)
    def do_run_agent(self, args: argparse.Namespace):
        """
        Run the agent
        """

        if self.agent is not None:
            reset = args.reset if args.reset else False
            self.agent.run(task=args.task, reset=reset)
        else:
            self.poutput('Agent not created. Use create_agent command.')

    # do_agent_state parser
    agent_state_parser = cmd2.Cmd2ArgumentParser(description='Show the agent state')
    agent_state_parser.add_argument('-i', '--item', help='inspect an item in the agent state')

    @cmd2.with_argparser(agent_state_parser)
    def do_agent_state(self, args: argparse.Namespace):
        """
        Show the agent state
        """

        if self.agent is not None:
            if args.item:
                self.poutput(self.agent.python_executor.state[args.item])
            else:
                self.poutput(self.agent.python_executor.state)
        else:
            self.poutput('Agent not created. Use create_agent command.')

    def do_show_agents(self, _):
        """
        Show the multi-agent hierarchy
        """

        if self.agent is not None:
            # self.poutput(f'Agent: {self.agent_type} Model: {self.model_id}')
            self.poutput(self.agent.visualize())
        else:
            self.poutput('Agent not created. Use create_agent command.')

    # do_save_agent parser
    save_agent_parser = cmd2.Cmd2ArgumentParser(description='Save the agent')
    save_agent_parser.add_argument('-t', '--type', choices=['local', 'hf', 'openai'], required=True, help='agent type')
    save_agent_parser.add_argument('-p', '--path', required=True, help='path or repo id')

    @cmd2.with_argparser(save_agent_parser)
    def do_save_agent(self, args: argparse.Namespace):
        """
        Save the current agent
        """
        if self.agent is not None:
            if args.type == 'hf':
                self.agent.push_to_hub(args.path)
            else:
                self.poutput('Currently, only hf agents are supported for saving.')
        else:
            self.poutput('Agent not created. Use create_agent command.')

    # do_load_agent parser
    load_agent_parser = cmd2.Cmd2ArgumentParser(description='Load the agent')
    load_agent_parser.add_argument('-t', '--type', choices=['local', 'hf', 'openai'], required=True, help='agent type')
    load_agent_parser.add_argument('-p', '--path', required=True, help='path or repo id')
    load_agent_parser.add_argument('--trust', action='store_true', help='trust remote code')

    @cmd2.with_argparser(load_agent_parser)
    def do_load_agent(self, args: argparse.Namespace):
        """
        Load the agent
        """
        if args.type == 'hf':
            trust_remote_code = args.trust if args.trust else False
            self.agent = CodeAgent.from_hub(args.path, trust_remote_code=trust_remote_code)
        else:
            self.poutput('Currently, only hf agents are supported for loading')

    cmd2.categorize([do_create_agent, do_run_agent,
                     do_show_agents, do_save_agent,
                     do_load_agent, do_agent_state],
                    AGENT_CATEGORY)

    ################################################################################################
    # PRIVATE functions #
    ################################################################################################
    def _create_agent(self, atype:str, mid:str)-> None:
        """
        Create a new agent

        :param atype: agent type
        :param mid: model id
        """

        success = False

        if atype == 'local':
            success = False
        elif atype == 'hf':
            ca_model = HfApiModel("Qwen/Qwen2.5-Coder-32B-Instruct",
                                  token=os.getenv('HF_TOKEN'),
                                  max_tokens=8156,
                                  provider="together")

            self.agent = CodeAgent(tools=AgentPlugin.get_tools(self),
                                   model=ca_model)
            success = True
        elif atype == 'openai':
            success = False
        else:
            self.poutput('Invalid argument. Use -h for help.')
            success = False

        if success:
            self.model_id = mid
            self.agent_type = atype
            self.poutput(f'Agent created with model: {mid}')

    ################################################################################################
    # main function #
    ################################################################################################
    def main(self):
        sys.exit(self.cmdloop())

def main():
    app = AgentShell()
    app.set_window_title('AI Agent Console')
    app.main()

if __name__ == '__main__':
    main()
