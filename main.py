"""main.py - This file contains a handler that is called by the cron job
cronjobs."""

import webapp2
from google.appengine.api import mail, app_identity
from service import GameService
import logging


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about an active game"""
        users = GameService.get_reminder_data()
        # logging for testing purpose
        logging.info('Users from main.py')
        logging.info(users)

        if not users:
            return

        app_id = app_identity.get_application_id()
        for user in users:
            subject = 'Your Hangman game is waiting'
            body = 'Hello {}, you have an active Hangman game. ' \
                   'Guess a letter to continue playing!'.format(user[0])
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user[1],
                           subject,
                           body)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail)
], debug=True)
