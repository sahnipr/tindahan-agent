from agent import Agent
from tools import Sandbox

if __name__ == '__main__':
    agent = Agent(Sandbox())
    print('Tindahan demo. Example: pabili po 2 sardinas at 3 kopiko brown')
    print('Copy the CONFIRM command from the proposal. Type quit to exit.')
    while True:
        try:
            message = input('Owner: ')
        except (EOFError, KeyboardInterrupt):
            break
        if message.lower() == 'quit':
            break
        print(agent.reply('store-001', message))
