"""service.py - File for the game logic and accessing the data store."""

from __future__ import division
from collections import namedtuple
from models import User, Game, Score
from utils import get_by_urlsafe
from google.appengine.ext import ndb
from collections import Counter
import operator
import itertools
from datetime import datetime, timedelta

# game bundle is used to pass game status between functions
GameBundle = namedtuple('GameBundle', 'word_status wrong_attempts_count letters_missed message game error_msg')


class GameService(object):
    # game handling methods
    @classmethod
    def create_user(cls, username, email):
        error_msg = ''
        if User.query(User.name == username).get():
            error_msg = "The user already exists"
        else:
            user = User(name=username, email=email)
            user.put()
        return error_msg

    @classmethod
    def new_game(cls, user_name):
        user = User.query(User.name == user_name).get()
        if not user:
            error_msg = 'Cound not find the user name'
            game_bundle = GameBundle(
                word_status=None,
                wrong_attempts_count=None,
                letters_missed=None,
                message=None,
                game=None,
                error_msg=error_msg)
        else:
            game = Game.new_game(user)
            game_bundle = cls.get_bundle(game.key.urlsafe(), 'Good luck playing Hangman! Make a guess!')
        return game_bundle

    @classmethod
    def get_user_games(cls, user_name):
        error_msg = None
        game_keys = []
        user = User.query(User.name == user_name).get()
        if not user:
            error_msg = 'Cound not find the user name'
            return error_msg, game_keys
        games = Game.query(ancestor=user.key)
        games = games.filter(Game.game_status == 'Active').fetch()
        game_keys = [game.key.urlsafe() for game in games]
        return error_msg, game_keys

    @classmethod
    def get_reminder_data(cls):
        # get emails of users that have active game for longer than a day
        users_data = None
        games = Game.query()

        games = games.filter(Game.created_at < (datetime.utcnow()-timedelta(1)))
        # if you want to test immediately, use this line instead:
        # games = games.filter(Game.created_at < (datetime.utcnow()))

        games = games.filter(Game.game_status == 'Active').fetch()

        if not games:
            return users_data  # returns empty list, if no games found

        user_ids = set([g.user for g in games])
        users = User.query(User.key.IN(user_ids))
        users = users.filter(User.email <> None).fetch()
        users_data = [(u.name, u.email)for u in users]

        return users_data

    @classmethod
    def get_high_scores(cls, number_of_results):
        # returns all winning games and sorts by the number of guesses
        error_msg = None
        score_table = []
        scores = Score.query()
        scores = scores.filter(Score.won == True)
        scores = scores.order(Score.total_guesses).fetch(number_of_results)
        if not scores:
            error_msg = 'Could not retrieve the scores'
            return error_msg, score_table

        user_ids = set([i.user for i in scores])
        users = User.query(User.key.IN(user_ids)).fetch()

        if not users:
            error_msg = 'Could not retrieve user data'
            return error_msg, score_table

        user_names = {u.key: u.name for u in users}
        score_table = [(user_names[i.user], i.total_guesses, i.missed_guesses) for i in scores]
        return error_msg, score_table

    @classmethod
    def get_user_rankings(cls):
        # getting games scores from the data store
        error_msg = None
        rankings = []
        scores = Score.query().fetch()
        if not scores:
            error_msg = 'Could not retrieve the scores'
            return error_msg, rankings

        user_ids = set([i.user for i in scores])

        # getting user names
        users = User.query(User.key.IN(user_ids)).fetch()
        if not users:
            error_msg = 'Could not retrieve user data'
            return error_msg, rankings
        user_names = {u.key: u.name for u in users}

        # creating a scores list with user names
        scores_list = [(user_names[i.user], i.won, i.total_guesses) for i in scores]

        # counting the number of total games for each user
        game_count = Counter(elem[0] for elem in scores_list)

        # counting the number of wins for each user
        win_count = Counter(elem[0] for elem in scores_list if elem[1] == True)

        # gouping by scores by the username
        user_groupby_iterator = itertools.groupby(
            sorted(scores_list, key=operator.itemgetter(0)),
            key=operator.itemgetter(0))

        # calculating sum of guesses for each user
        sums_of_guesses = [(user, sum(score[2] for score in iterator)) for (user, iterator) in user_groupby_iterator]

        # calculating avg guesses and win ration per user and assigning them to the rankings list
        rankings=[(i[0],
                  win_count[i[0]] / game_count[i[0]],
                  i[1] / game_count[i[0]])
                  for i in sums_of_guesses]

        # sorting rankings by win ratio and then by avg guesses
        rankings.sort(key=lambda x: (-x[1], x[2]))
        return error_msg, rankings

    @classmethod
    def cancel_game(cls, urlsafe_game_key):
        message = None
        error_msg = None

        game = get_by_urlsafe(urlsafe_game_key, Game)

        if not game:
            error_msg = "Could not find the game"
            return error_msg, message

        if game.game_status == 'Active':
            game.game_status = 'Canceled'
            game.put()
            message = 'The game was canceled'

        else:
            message = 'The game is over and cannot be canceled'
        return message, error_msg

    @classmethod
    def get_bundle(cls, urlsafe_game_key, message):
        game = get_by_urlsafe(urlsafe_game_key, Game)
        if not game:
            return GameBundle(
                word_status=None,
                wrong_attempts_count=None,
                letters_missed=None,
                message=None,
                game=None,
                error_msg="Could not find the game",
            )
        word_status = cls.get_word_status(game)
        wrong_attempts_count = cls.get_wrong_attempts_count(game)
        letters_missed = cls.get_missed_guesses(game)

        if message:
            message = message
        elif (game.game_status == 'Active') and (wrong_attempts_count < 6):
            message = 'Time to make a move!'
        elif game.game_status == 'Canceled':
            message = 'This game was canceled. Please start a new one!'
        elif game.game_status == 'Finished':
            message = 'This game is over. Please start a new one!'
        else:
            message = 'You should not end up here.'
        return GameBundle(
            word_status=word_status,
            wrong_attempts_count=wrong_attempts_count,
            letters_missed=letters_missed,
            message=message,
            game=game,
            error_msg=""
        )

    @classmethod
    def get_word_status(cls, game):
        target_word = game.word
        letters_guessed = game.user_guesses
        if game.word in game.user_guesses:
            word_status = game.word
        else:
            word_status = ''.join(l if l in letters_guessed else '*' for l in target_word)
        return word_status

    @classmethod
    def get_wrong_attempts_count(cls, game):
        return len(cls.get_missed_guesses(game))

    @classmethod
    def get_missed_guesses(cls, game):
        missed_guesses = [i for i in game.user_guesses if (i not in set(game.word)) and (i != game.word)]
        return missed_guesses

    @classmethod
    def get_history(cls, urlsafe_game_key):
        game_history = []
        error_msg = None

        game = get_by_urlsafe(urlsafe_game_key, Game)

        if not game:
            error_msg = 'Could not find the game'
            return error_msg, game_history

        guesses_replayed = []
        wrong_count = 0

        for i in game.user_guesses:
            state, message = cls.get_result(
                game.word,
                guesses_replayed,
                i,
                wrong_count)
            guesses_replayed.append(i)
            if state == 1:
                wrong_count +=1
            result = {
                'Guess': i,
                'Message': message
            }
            game_history.append(result)
        return error_msg, game_history

    @classmethod
    def get_result(cls, word, user_guesses, guess, wrong_attempts_count):
        # state=0, right guess.
        # state=1, wrong guess.
        # state=2, game over, won.
        # state=3, game over, lost.
        # state=4, invalid or repeated character
        user_guesses = [x.lower() for x in user_guesses]
        guess = guess.lower()
        word = word.lower()

        if not guess.isalpha():
            message = 'Please enter a valid character or a word'
            state = 4
            return state, message

        if guess in user_guesses:
            message = 'You already guessed this character. Try a different one!'
            state = 4
            return state, message

        user_guesses = set(user_guesses)
        user_guesses.add(guess)
        if guess == word \
                or user_guesses > set(word):
            message = 'You Won!'
            state = 2
            return state, message

        elif (wrong_attempts_count == 5) and (guess not in set(word)):
            message = 'You Lost! The word was: ' + str(word)
            state = 3
            return state, message

        if guess in set(word):
            message = 'Good guess! Make another move!'
            state = 0
        else:
            message = 'You missed it! Try another letter!'
            state = 1
        return state, message

    @classmethod
    @ndb.transactional(xg=True)
    def make_move(cls, urlsafe_game_key, guess):
        # get game bundle
        message = None
        game_bundle = cls.get_bundle(urlsafe_game_key, message=message)

        # if there is and error or game is over, return unmodified bundle
        if game_bundle.error_msg\
                or game_bundle.wrong_attempts_count == 6 \
                or game_bundle.game.game_status != 'Active':
            return game_bundle

        state, message = cls.get_result(
            game_bundle.game.word,
            game_bundle.game.user_guesses,
            guess,
            game_bundle.wrong_attempts_count)

        # state=4, invalid or repeated character
        if state == 4:
            game_bundle = game_bundle._replace(message=message)
            return game_bundle

        game_bundle.game.user_guesses.append(guess.lower())

        # state=2, game over, won. state=3, game over, lost.
        if state in [2, 3]:
            game_bundle.game.game_status = 'Finished'

        # updating the game with the new guess and game status (if changed)
        game_bundle.game.put()

        # get updated bundle with the latest guess
        updated_game_bundle = cls.get_bundle(urlsafe_game_key, message=message)

        # state=2, game over, won. state=3, game over, lost.
        if state in [2, 3]:
            score = Score(
                user=updated_game_bundle.game.user,
                won=True if state == 2 else False,
                missed_guesses=cls.get_wrong_attempts_count(updated_game_bundle.game),
                total_guesses=len(updated_game_bundle.game.user_guesses))
            score.put()

        return updated_game_bundle

