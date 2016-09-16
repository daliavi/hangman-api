"""models.py - File describing data models."""

import random
from protorpc import messages
from google.appengine.ext import ndb
from datetime import datetime, timedelta

WORD_LIST = ['authentic', 'mama', 'lizard', 'canyon', 'shallow', 'ant', 'rat', 'bubble']


class User(ndb.Model):
    """User object"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()


class Game(ndb.Model):
    """Game object"""
    word = ndb.StringProperty(required=True) # the word to be guessed
    game_status = ndb.StringProperty(required=True, default='Active') # can be Active, Canceled or Finished
    user = ndb.KeyProperty(required=True, kind='User')
    user_guesses = ndb.StringProperty(repeated=True)
    created_at = ndb.DateTimeProperty(required=True, auto_now=True)

    @classmethod
    def new_game(cls, user):
        """Creates  a new game"""
        game = Game(user=user.key,
                    word=random.choice(WORD_LIST),
                    game_status='Active',
                    user_guesses=[],
                    parent=user.key
                    )
        game.put()
        return game

    def to_form(self, word_status, wrong_attempts_count, letters_missed, message, **kw):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.word_status = word_status  # example: ***** or *a***a*
        form.wrong_attempts_count = wrong_attempts_count
        form.missed_guesses = letters_missed
        form.game_status = self.game_status
        form.message = message
        return form


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateTimeProperty(required=True, auto_now=True)
    won = ndb.BooleanProperty(required=True)
    missed_guesses = ndb.IntegerProperty(required=True)
    total_guesses = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), missed_guesses=self.missed_guesses,
                         total_guesses=self.total_guesses)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    word_status = messages.StringField(2, required=False)
    wrong_attempts_count = messages.IntegerField(3, required=True)
    missed_guesses = messages.StringField(4, repeated=True)
    game_status = messages.StringField(5, required=True)
    message = messages.StringField(6, required=True)
    user_name = messages.StringField(7, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    total_guesses = messages.IntegerField(2, required=True)
    missed_guesses = messages.IntegerField(3, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class RankingForm(messages.Message):
    """RankingForm for user standings"""
    user_name = messages.StringField(1, required=True)
    wins_ratio = messages.FloatField(2, required=True)
    avg_guesses = messages.FloatField(3, required=True)


class RankingForms(messages.Message):
    """Return multiple RankingForms"""
    items = messages.MessageField(RankingForm, 1, repeated=True)


class HistoryForm(messages.Message):
    """Return o move in game history"""
    guess = messages.StringField(1, required=True)
    message = messages.StringField(2, required=True)


class HistoryForms(messages.Message):
    """Return multiple HistoryForms"""
    history = messages.MessageField(HistoryForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage outbound (single) string message"""
    message = messages.StringField(1, required=True)

class UserGamesForm(messages.Message):
    """Return a list of user games"""
    item = messages.StringField(1, repeated=True)