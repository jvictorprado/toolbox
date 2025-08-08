import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Configurações
GITLAB_URL = 'https://example'
PRIVATE_TOKEN = 'blablabla-example'  
USER_IDS = [747, 748, 749, 750, 751, 753, 754, 755, 756, 757, 758, 759, 760, 761, 768, 769, 787, 803, 804, 809, 818, 878, 922, 993, 1057, 1185, 1189, 1207, 1211]  
HEADERS = {'PRIVATE-TOKEN': PRIVATE_TOKEN}

def get_user_activity(user_id, per_page=100):
    events = []
    page = 1
    
    while True:
        url = f"{GITLAB_URL}/api/v4/users/{user_id}/events?per_page={per_page}&page={page}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        page_events = response.json()
        
        if not page_events:
            break
            
        events.extend(page_events)
        page += 1
    
    return events

def collect_user_actions(user_id):
    events = get_user_activity(user_id)
    data = []

    for event in events:
        if event['action_name'] in ['approved', 'commented on', 'merged']:
            data.append({
                'merge_request_id': event['target_id'],
                'action': event['action_name'],
                'created_at': event['created_at'],
                'author': event['author']['username']
            })
    
    return pd.DataFrame(data)

def filter_last_two_weeks_actions(df):
    two_weeks_ago = datetime.now(pytz.utc) - timedelta(weeks=2)
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce', utc=True)
    return df[df['created_at'] >= two_weeks_ago]

def get_user_name(user_id):
    """Function to obtain user name through their ID."""
    url = f"{GITLAB_URL}/api/v4/users/{user_id}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Error searching the name for user: {user_id}. Status Code: {response.status_code}, Response: {response.text}")
        return f"User {user_id}"
    
    user_info = response.json()
    return user_info.get('name', f"Usuário {user_id}")

def check_actions_for_users(user_ids):
    for user_id in user_ids:
        user_name = get_user_name(user_id)
        df = collect_user_actions(user_id)
        
        if df.empty:
            print(f"No data for: {user_name} (ID: {user_id}).")
        else:
            df_last_two_weeks = filter_last_two_weeks_actions(df)
            print(f"\nActions in the last two weeks for: {user_name} (ID: {user_id})")
            
            # Agrupar ações e adicionar nome do autor
            grouped = df_last_two_weeks.groupby(['action', 'author']).size().reset_index(name='count')
            
            for _, row in grouped.iterrows():
                action = row['action']
                author = row['author']
                count = row['count']
                print(f"{action:<15} {author:<15} {count}")

# calls main function
check_actions_for_users(USER_IDS)

