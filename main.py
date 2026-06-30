import asyncio
from src.game import Game

game = Game()

async def main():
    while True:
        game.tick()
        await asyncio.sleep(0)

asyncio.run(main())
