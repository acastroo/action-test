import json
import os

import firebase_admin
import firebase_admin.auth
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import credentials

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/alerts/token/")

"""
 Firebase auth work to be used in all apis
"""


def get_config():
    with open(os.environ['GOOGLE_APPLICATION_CREDENTIALS'], 'r') as fp:
        credentials = json.load(fp)
    project_id = credentials['project_id']
    config = {
        "apiKey": os.environ['FIREBASE_API_KEY'],
        "authDomain": "{}.firebaseapp.com".format(project_id),
        "databaseURL": "https://{}.firebaseio.com".format(project_id),
        "projectId": project_id,
        "storageBucket": "{}.appspot.com".format(project_id)
    }
    return config


# firebase_app = firebase_admin.initialize_app(options=get_config())
cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
firebase_app = firebase_admin.initialize_app(cred)


def verify_token(token):
    try:
        return firebase_admin.auth.verify_id_token(token, app=firebase_app,
                                                   check_revoked=True)
    except firebase_admin.auth.InvalidIdTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")
    except firebase_admin.auth.ExpiredIdTokenError:
        raise HTTPException(status_code=403, detail="Expired token")
    except firebase_admin.auth.RevokedIdTokenError:
        raise HTTPException(status_code=403, detail="Revoked token")
    except firebase_admin.auth.CertificateFetchError:
        raise HTTPException(status_code=403, detail="Certificate fetch error")
