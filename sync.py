from mendeley import Mendeley
from mendeley.session import MendeleySession
from mendeley.exception import MendeleyApiException
import yaml
from requests_oauthlib import OAuth2Session

with open('config.yml') as f:
    config = yaml.load(f)

def pull_mendeley_documents(client_id, client_secret, access_token, download_dir):
    try:
        # Create a Mendeley session
        oauth2_session = OAuth2Session(token={'access_token': access_token})

        session = MendeleySession(oauth2_session)
        session.token = access_token

        # Create a Mendeley client
        mendeley = Mendeley(session)

        # Retrieve documents
        documents = mendeley.documents.list(view='all')

        # Create the download directory if it doesn't exist
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # Download files
        for doc in documents.iter():
            for attachment in doc.attachments:
                # Get the filename
                filename = os.path.join(download_dir, attachment.filename)
                # Download the file
                with open(filename, 'wb') as f:
                    attachment.download(f)

        print("Files downloaded successfully.")

    except MendeleyApiException as e:
        print("Mendeley API Exception:", e)


# Example usage
client_id = config['clientId']
client_secret = config['clientSecret']
redirect_uri = 'http://127.0.0.1:5000/oauth'
access_token = 'MSwxNzA3NTA2Mzk5Mzc2LDUzOTIzODEzMSwxNzY3NCxhbGwsLCxlYzE0OGJmNzNhNmE5MDRkNTU0YjE0ZjM2ODZjYjFlNTZjNTZneHJxYSxjNDU5YTdmNC0xY2M1LTM3OWItYTc0MC1mM2NjMmUyZjQwMmMsYUFGZ3VFc00tYnNwaU1yOWVISnhWLUlXel93'

download_dir = 'lib'  # Directory where files will be saved

pull_mendeley_documents(client_id, client_secret, access_token, download_dir)

