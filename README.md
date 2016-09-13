#Hangman game

##Live version of the API
You can check the live version of the API here:
https://daliavi-hangman.appspot.com/_ah/api/explorer

## Set-Up Instructions
1. Download the project files from Github
2. Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
3.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
 
##Game Description
The word to guess is represented by a row of stars `*`, representing each letter of the word.
If the player suggests a letter which occurs in the word, the program writes it in all its correct positions. 
If the suggested letter does not occur in the word, the program increments the missed guesses counter (max 6 allowed).
The player guessing the word may, at any time, attempt to guess the whole word.
If the word is correct, the game is over and the guesser wins.
Otherwise, the program will penalize the guesser by incrementing the missed guesses counter.
If the player makes 6 incorrect guesses, the game is also over.
However, the guesser can also win by guessing all the letters that appears in the word.

###How to play
 - create a user using `create_user` endpoint. Remember your user name!
 - using the user name, create a new game by sending a request to `new_game`.
 Remember to save the `urlsafe_game_key` of the new game.
 - to play the game, send a request to `make_move` endpoint with the `urlsafe_game_key`
 and the guess from the player. You will receive the state of the game after each move.
 - at any time, you can check the status of the game by calling `get_game` endpoint
 with the `urlsafe_game_key`
 - you can get the history of the game by calling `get_game_history` endpoint with the `urlsafe_game_key`
 - to cancel an active game, send a request to `cancel_game` endpoint
 - to get the high scores call `get_high_scores` endpoint
 - for user ranking send a request to `get_user_rankings` endpoint
 - to get keys of all the active games of a user call `get_user_games` endpoint with the user name.
 
###Score calculation
After each game a score record is added to teh data store. It contains player's username, win/lose indication,
a count of missed guesses and a count of total guesses made during that game.
The `get_high_scores` endpoint returns data of the users who won the game ordered by the number
of total guesses. The less tries it takes to guess a word, the better.

###User rankings calculation
Players are ranked by the winning ratio (desc) and then by the average number of guesses (asc).
Win ratio for each user is calculated using this formula:

`count of all the games the user won / count of all the games the user played`

Average guesses for each user calculated:

`sum of the number of guesses for each user / count of total games`


##Files Included:
 - api.py: Contains endpoints.
 - app.yaml: App configuration.
 - cron.yaml: Cron job configuration.
 - main.py: Handler for cron jobs.
 - models.py: Entity and message definitions including helper methods.
 - service.py: Game logic and connections to the data store.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints:
- **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming the creation of the User.
    - Description: Creates a new User in the data store. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.

- **new_game**
    - Path: 'game/new'
    - Method: POST
    - Parameters: user_name
    - Returns: GameForm with initial state of the game.
    The form contains:
        - game status (string),
        - message to the player (string), 
        - url safe key (string), 
        - username (string), 
        - word status (string)
        - wrong attempt count (int)
    - Description: Creates a new Game. The user_name provided must correspond to an existing user, otherwise it will raise a NotFoundException.

- **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with the current state of the game.
    The form contains:
        - game status (string),
        - message to the player (string), 
        - url safe key (string), 
        - username (string), 
        - word status (string)
        - wrong attempt count (int)
    - Description: Returns the current state of the game. If the game key does not exist, it will raise a NotFoundException.
    
- **make_move**
    - Path: 'game/move/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess (can be either a letter or the whole word)
    - Returns: GameForm with new game state.
    The form contains:
        - game status (string),
        - message to the player (string), 
        - url safe key (string), 
        - username (string), 
        - word status (string)
        - wrong attempt count (int)
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes the game to end, a corresponding Score entity will be created.
    If the game key does not exist, it will raise a NotFoundException.

- **get_game_history**
    - Path: 'history/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key, 
    - Returns: HistoryForms with all the player guesses and results.
    The form contains:
        - game status (string),
        - message to the player (string)
    - Description: the game can be replayed move by move. If the game key does not exist, it will raise a NotFoundException.
 
- **get_user_games**    
    - Path: 'game/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: UserGameForm with url safe IDs of all the active games of the user.
    - Description: Gets all the games that have not been completed yet by the user. If the game key does not exist, it will raise a NotFoundException.
    
- **get_high_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: number_of_results (optional)
    - Returns: ScoreForms showing the results of the games that users won, ordered by the number of total guesses.
    The form contains:
        - username (string),
        - count of missed guesses (int),
        - total guesses guesses (int)
    - Description: The function gets the results of the games that users won and sorts the results by the number of total guesses. If it cannot retreive the scores or users, it will raise a NotFoundException.

- **get_user_rankings**
    - Path: 'rankings'
    - Method: GET
    - Parameters: None
    - Returns: RankingForms showing the list of ranked players and their performance indication
    The form contains:
        - username (string),
        - wins_ratio (float),
        - avg_guesses (float)
    - Description: gets all scores from the data store, groups the data by username, calculates win/loose ratio and average guesses for each user, sorts the data by the ration (desc) and then by the average guess (asc)

- **cancel_game**
    - Path: 'cancel/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: GameForm with new game state.
    - Description: This endpoint allows users to cancel an active game. Game status property is chnages to 'Canceled'. If the game key does not exist, it will raise a NotFoundException.
    
##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

##Forms Included:
 - **GameForm**
    - Representation of a Game's state
    (urlsafe_key, word_status, wrong_attempst_count, game_status, message, user_anme)
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, total guesses, missed guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **RankingForm**
    - Representation of user rankings (user_name, wins_ratio, avg_guesses).
 - **RankingForms**
    - Multiple RankingForm container.
 - **HistoryForm**
    - Representation of the history of user moves during the game (guess, message).
 - **HistoryForms**
    - Multiple HistoryForm container.
 - **StringMessage**
    - General purpose String container.
