import random

from discord.ext import commands
from asyncio.exceptions import TimeoutError


class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wordlist = self.get_words()

    def get_words(self):
        with open("./words.txt") as file:
            content = file.read()
            wordlist = content.split('","')
        return wordlist

    def check(self, word, guess):
        # If correct, take off list
        # Check if valid guess
        if guess == "quit":
            return True, "quit"
        if len(guess) != 5:
            return False, "Guess must be 5 characters."
        elif guess not in self.wordlist:
            return False, "Guess not in word list."

        # TODO reacts instead of '\\'
        response = ['\\' for _ in range(5)]

        # Match correct letters
        for i in range(len(guess)):
            if guess[i] == word[i]:
                response [i] = guess[i].upper()
        
        # Match improperly placed letters
        for i in range(len(guess)):
            if guess[i] in word and response.count(guess[i].upper()) < word.count(guess[i]) and guess[i] != word[i]:
                response[i] = guess[i].lower()

        return True, ''.join(response)

    @commands.command(name="wordle", description="Starts a wordle game with the server")
    async def _wordle(self, ctx):
        tries = 6
        word = self.wordlist[random.randint(0, len(self.wordlist))]
        await ctx.send(f"```Now Playing Wordle with {ctx.author.name}\nGuess the hidden word in 6 tries.\nAfter each guess:\n\tA capital letter means a correct letter.\n\tA lowercase letter means the letter is in the wrong spot.\n\tAnd a \\ means the letter was wrong.```")
        while tries > 0:
            valid = False
            while not valid:
                try:
                    msg = await self.bot.wait_for('message', check=lambda message: (message.author == ctx.author and message.content.split(' ')[0] == ".guess" and len(message.content.split(' ')) == 2), timeout=600)
                except TimeoutError:
                    return await ctx.send(f"```No guesses have been made in 10 minutes, timing out. Word was {word.upper()}```")

                guess = msg.content.split(' ')[1].lower()

                valid, response = self.check(word, guess)

                if valid:
                    tries -= 1

                if response == "quit":
                    return await ctx.send(f"```{ctx.author} quit. The word was {word.upper()}.```")

                if response == response.upper() and '\\' not in response:
                    return await ctx.send(f"```Correct! The word was {word.upper()}. You got it in {6-tries} guesses```")
                else:
                    plural = "guess" if tries == 1 else "guesses"
                    await ctx.send(f"```{response}\t{tries} {plural} left```")
        if tries == 0:
            return await ctx.send(f"```You didn't get the word, it was {word.upper()}```")
