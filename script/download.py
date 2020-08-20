import config as cfg
import requests

# Global client session
session = requests.Session()

#####
# Login to Recogito
#####
def login():
  print(f'Logging in as: {cfg.RECOGITO_USER}')

  payload = { 'username': cfg.RECOGITO_USER, 'password': cfg.RECOGITO_PW }
  return session.post(f'{cfg.RECOGITO_URL}/login', data=payload)

#####
# List user directory from Recogito, so we can check if docs exist already
#####
def list_workspace_dir():
  response = session.get(f'{cfg.RECOGITO_URL}/api/directory/my')
  return response.json()['items']

#####
# Download list of collaborators on this document
#####
def get_collaborators(doc_id):
  response = session.get(f'{cfg.RECOGITO_URL}/document/{doc_id}/settings/collaborators')
  return [ collaborator['shared_with'] for collaborator in response.json() ]

#####
# Download JSON-LD annotations for the given document
#####
def get_annotations(doc_id):
  response = session.get(f'{cfg.RECOGITO_URL}/document/{doc_id}/downloads/annotations/jsonld')
  return response.json()

#####
# Counts contributions per user to the annotations
#####
def count_contributions(annotations):
  contributions = {}

  for a in annotations:
    for b in a['body']:
      creator = b['creator'].split('/')
      creator = creator[len(creator) - 1]

      if creator in contributions:
        contributions[creator] += 1
      else:
        contributions[creator] = 1

  return contributions


###############################
#
# Download process starts here
#
###############################
try:
  response = login()

  if response.status_code != 200:
    raise Exception(f'Login failed with code {response.status_code}')

  # Fetch all document IDs in the workspace root
  for item in list_workspace_dir():
    doc_id = item['id']
    print(f'Downloading data for {doc_id}')
    
    collaborators = set(get_collaborators(doc_id))
    print(f'  Shared with: {", ".join(collaborators)}')

    annotations = get_annotations(doc_id)
    print(f'  Document has {len(annotations)} annotations')

    contributions_per_user = count_contributions(annotations)
    for username in contributions_per_user:
      print(f'    {username}: {contributions_per_user[username]} contributions')

    # Check if every user has contributed
    contributing_users = set(contributions_per_user.keys())
    lazy_users = collaborators.difference(contributing_users)

    if len(lazy_users) == 0:
      print('  ALL ANNOTATORS HAVE CONTRIBUTED - ready to download')
    else:
      print(f'  {len(lazy_users)} users have not contributed yet ({", ".join(lazy_users)})')

except Exception as e:
  print(f'Error: {str(e)}')