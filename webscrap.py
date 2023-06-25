from flask import Flask, render_template, request
import requests
from tabulate import tabulate
import time

app = Flask(__name__)

def fetch_all_items(url):
    items = []
    page = 1
    per_page = 100

    while True:
        response = requests.get(url, params={'page': page, 'per_page': per_page})
        if response.status_code == 200:
            current_items = response.json()
            items.extend(current_items)
            if len(current_items) < per_page:
                break
            else:
                page += 1
        else:
            break

    return items

def retrieve_user_info(username):
    user_info_url = f"https://api.github.com/users/{username}"
    retries = 3

    while retries > 0:
        response = requests.get(user_info_url)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to retrieve information for user: {username}")
            retries -= 1
            time.sleep(1)  # Wait for a second before retrying

    return None

def scrape_github_profiles(usernames, language, repositories):
    user_activity = []

    for username in usernames:
        user_info = retrieve_user_info(username)

        if user_info is not None:
            user_data = {
                'Username': username,
                'Name': user_info['name'],
                'Email': user_info['email'],
                'LinkedIn': user_info['blog'],
                'Location': user_info['location'],
                'Activity': 0
            }

            # Divide the list of usernames found while traversing following and followers
            following_usernames = set()
            followers_usernames = set()

            for repo in repositories:
                contributors_url = f"https://api.github.com/repos/{repo}/contributors"
                contributors = fetch_all_items(contributors_url)

                for contributor in contributors:
                    if contributor['login'] == username:
                        user_data['Activity'] += 1

                watchlist_url = f"https://api.github.com/repos/{repo}/subscribers"
                watchers = fetch_all_items(watchlist_url)

                for watcher in watchers:
                    if watcher['login'] == username:
                        user_data['Activity'] += 1

                issues_url = f"https://api.github.com/repos/{repo}/issues"
                issues = fetch_all_items(issues_url)

                for issue in issues:
                    if issue['user']['login'] == username:
                        user_data['Activity'] += 1

                stargazers_url = f"https://api.github.com/repos/{repo}/stargazers"
                stargazers = fetch_all_items(stargazers_url)

                for stargazer in stargazers:
                    if stargazer['login'] == username:
                        user_data['Activity'] += 1

                forks_url = f"https://api.github.com/repos/{repo}/forks"
                forks = fetch_all_items(forks_url)

                for fork in forks:
                    fork_owner_username = fork['owner']['login']
                    fork_owner_info = retrieve_user_info(fork_owner_username)

                    if fork_owner_info is not None:
                        if fork_owner_info['login'] == username:
                            user_data['Activity'] += 1

                            if username in fork_owner_info['following']:
                                user_data['Activity'] += 1

                                followers_url = f"https://api.github.com/users/{fork_owner_username}/followers"
                                followers = fetch_all_items(followers_url)
                                followers_usernames.update([follower['login'] for follower in followers])

                            following_url = f"https://api.github.com/users/{fork_owner_username}/following"
                            following = fetch_all_items(following_url)
                            following_usernames.update([follow['login'] for follow in following])

            user_data['Following'] = ', '.join(following_usernames)
            user_data['Followers'] = ', '.join(followers_usernames)
            user_activity.append(user_data)

    ranked_users = sorted(user_activity, key=lambda x: x['Activity'], reverse=True)

    headers = ['Username', 'Name', 'Email', 'LinkedIn', 'Location', 'Following', 'Followers', 'Activity']
    rows = [[user['Username'], user['Name'], user['Email'], user['LinkedIn'], user['Location'],
             user['Following'], user['Followers'], user['Activity']] for user in ranked_users]

    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return user_activity

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        usernames = request.form.getlist('usernames') or ["rishav887"]
        language = request.form.get('language') or "Java"
        repositories = request.form.getlist('repositories') or ["FormWorks"]

        data = scrape_github_profiles(usernames, language, repositories)

        headers = ['Username', 'Name', 'Email', 'LinkedIn', 'Location', 'Following', 'Followers', 'Activity']
        rows = []

        print("Data:", data)
        for user in data:
            username = user.get('Username', '')
            name = user.get('Name', '')
            email = user.get('Email', '')
            linkedin = user.get('LinkedIn', '')
            location = user.get('Location', '')
            following = user.get('Following', '')
            followers = user.get('Followers', '')
            activity = user.get('Activity', '')

            rows.append([username, name, email, linkedin, location, following, followers, activity])

        return render_template('result.html', headers=headers, rows=rows)
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
