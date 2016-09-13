"""api.py - API file, used for communication to/from the API's users."""

import endpoints
from protorpc import remote, messages
from service import GameService
import logging

from models import(
    StringMessage,
    GameForm,
    ScoreForms,
    HistoryForm,
    HistoryForms,
    UserGamesForm,
    ScoreForm,
    RankingForm,
    RankingForms
)

NEW_GAME_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1))

GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)

GET_USER_GAMES_REQUEST = endpoints.ResourceContainer(
    user_name = messages.StringField(1, required=True))

GET_HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results = messages.IntegerField(1))

GET_HISTORY_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1), )

CANCEL_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1), )

MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),
    guess = messages.StringField(2,required=True))

USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))


@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Hangman Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Creates a User. Requires a unique username. You must have a user to play!"""
        error_msg = GameService.create_user(request.user_name, request.email)
        if error_msg:
            raise endpoints.ConflictException(error_msg)
        else:
            return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/new',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game. Requires an existing user name"""
        game_bundle = GameService.new_game(request.user_name)
        if game_bundle.error_msg:
            raise endpoints.NotFoundException(game_bundle.error_msg)
        else:
            return game_bundle.game.to_form(**game_bundle._asdict())

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Returns the current game state."""
        game_bundle = GameService.get_bundle(request.urlsafe_game_key, message=None)
        if game_bundle.error_msg:
            raise endpoints.NotFoundException(game_bundle.error_msg)
        else:
            return game_bundle.game.to_form(**game_bundle._asdict())

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/move/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with a message"""
        game_bundle = GameService.make_move(request.urlsafe_game_key, request.guess)
        if game_bundle.error_msg:
            raise endpoints.NotFoundException(game_bundle.error_msg)
        else:
            return game_bundle.game.to_form(**game_bundle._asdict())

    @endpoints.method(request_message=GET_HISTORY_REQUEST,
                      response_message=HistoryForms,
                      path='history/{urlsafe_game_key}',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Returns history of the game, step by step."""
        error_msg, game_history = GameService.get_history(request.urlsafe_game_key)
        if error_msg:
            raise endpoints.NotFoundException(error_msg)
        else:
            return HistoryForms(history=[
                HistoryForm(guess=d['Guess'],
                            message=d['Message']) for d in game_history])

    @endpoints.method(request_message=GET_USER_GAMES_REQUEST,
                      response_message=UserGamesForm,
                      path='games/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns IDs of all active games of the given user."""
        error_msg, games = GameService.get_user_games(request.user_name)
        if error_msg:
            raise endpoints.NotFoundException(error_msg)
        else:
            return UserGamesForm(item=[g for g in games])

    @endpoints.method(request_message=GET_HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Returns winners ordered by the number of guesses."""
        try:
            error_msg, high_scores = GameService.get_high_scores(request.number_of_results)
        except KeyError:
            error_msg = 'Could not find required user data'
        if error_msg:
            raise endpoints.NotFoundException(error_msg)
        else:

                return ScoreForms(items=[
                    ScoreForm(user_name=s[0],
                              total_guesses=s[1],
                              missed_guesses=s[2]) for s in high_scores])

    @endpoints.method(response_message=RankingForms,
                      path='rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Returns users ranked by winning ratio and average number of guesses."""
        try:
            error_msg, rankings = GameService.get_user_rankings()
        except KeyError:
            error_msg = 'Could not find required user data'
        if error_msg:
            raise endpoints.NotFoundException(error_msg)
        else:
            return RankingForms(items=[
                RankingForm(user_name=r[0],
                            wins_ratio=r[1],
                            avg_guesses=r[2]) for r in rankings])

    @endpoints.method(request_message=CANCEL_REQUEST,
                      response_message=StringMessage,
                      path='cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """Cancel the given game."""
        message, error_msg = GameService.cancel_game(request.urlsafe_game_key)
        if error_msg:
            raise endpoints.NotFoundException(error_msg)
        else:
            return StringMessage(message=message)

api = endpoints.api_server([HangmanApi])
