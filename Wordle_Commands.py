import random

from discord.ext import commands


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
        # Check if valid guess
        if len(guess) != 5:
            return False, "Guess must be 5 characters."
        elif guess not in self.wordlist:
            return False, "Guess not in word list."

        # Get to use reacts
        response = ""
        for i in range(len(guess)):
            if guess[i] == word[i]:
                response += guess[i].upper()
            elif guess[i] in word:
                response += guess[i].lower()
            else:
                response += '\\'
        return True, response

    @commands.command(name="wordle", description="Starts a wordle game with the server")
    async def _wordle(self, ctx):
        tries = 6
        word = self.wordlist[random.randint(0, len(self.wordlist))]
        await ctx.send(f"```Now Playing Wordle with {ctx.author.name}\nGuess the hidden word in 6 tries.\nAfter each guess:\n\tA capital letter means a correct letter.\n\tA lowercase letter means the letter is in the wrong spot.\n\tAnd a \\ means the letter was wrong.\nHint: the word is {word.upper()}```")
        while tries > 0:
            valid = False
            while not valid:
                msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)
                guess = msg.content.lower()
                valid, response = self.check(word, guess)
                if valid:
                    tries -= 1

                if response == response.upper() and '\\' not in response:
                    await ctx.send(f"```Correct! The word was {word.upper()}. You got it in {6-tries} guesses```")
                    return
                else:
                    plural = "guess" if tries == 1 else "guesses"
                    await ctx.send(f"```{response}\t{tries} {plural} left```")
        if tries == 0:
            await ctx.send(f"```You didn't get the word, it was {word.upper()}```")
