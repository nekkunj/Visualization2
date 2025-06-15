'''
    Contains the server to run our application.
'''
from flask_failsafe import failsafe
from app import app  # your Dash app
application = app.server  # expose the Flask server as `application`




@failsafe
def create_app():
    '''
        Gets the underlying Flask server from our Dash app.

        Returns:
            The server to be run
    '''
    # the import is intentionally inside to work with the server failsafe
    from app import app  # pylint: disable=import-outside-toplevel
    application=app.server
    return app.server


if __name__ == "__main__":

    application.run(port=8050, debug=True)
