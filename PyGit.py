from flask import Flask, render_template, request, redirect, url_for
from requests import post
import github
from github import Github
import datetime

app = Flask(__name__)

CLIENT_ID = '######'
CLIENT_SECRET = '#######'
token = None


@app.route('/')
def home():
    # dont forget to pass in your scopes!!!
    return render_template('home.html', CLIENT_ID=CLIENT_ID)


@app.route('/callback')
def callback():
    global token
    session_code = request.args.get('code', '')
    headers = {'Content-type': 'application/json'}
    params = {'client_id': CLIENT_ID,
              'client_secret': CLIENT_SECRET,
              'code': session_code}
    result = post(
        "https://github.com/login/oauth/access_token",
        params=params, headers=headers)
    # the token is in the result. split on the =
    result = result.content.split("=")[1]
    # split on the &
    result = result.split('&')[0]
    # result is the access token
    token = result
    return redirect(url_for('add_project'))


@app.route('/git')
def git():
    # create a github instance with the current token
    g = Github(token)
    # get user will get me, because I authenticated my account
    user = g.get_user()
    # I want to get the OSF-test repo
    repo = user.get_repo('OSF-test')
    # we're going to create a blob. our first step is to get the content
    # of that blob
    file = open('/Users/samportnow/Documents/git-test/test.txt', 'r')
    contents = file.read()
    # now we can create a blob of the contents
    my_blob = repo.create_git_blob(contents, 'utf-8')
    # now we need to get the master branch
    master_branch = repo.get_git_ref('heads/master')
    # and the base commit of that master branch
    base_commit = repo.get_commit(sha=master_branch._object._sha)
    # and the tree were are going to committing to
    tree = github.InputGitTreeElement(
        path='test.txt',
        mode='100755', type='blob', sha=my_blob.sha)
    # now we create a NEW Tree!
    new_tree = repo.create_git_tree(
        base_tree=base_commit._commit.tree, tree=[tree])
    # now we can finally commit!
    # lets try to use a DIFFERENT author, whose on my collaborator team
    # (this works)
    contributor = g.get_user('sullytesting1987')
    email = contributor._email
    name = contributor._name
    author = github.InputGitAuthor(name=name, email=email, date=str(datetime.datetime.now()))
    commit = repo.create_git_commit(
        "This is a commit", tree=new_tree,
        parents=[master_branch._object._sha], author=author)
    # note: i changed the pygithub code for the parents list.
    # they are looking for github commit objects, but all that
    # is really needed is the sha of the master branch. so i got that instead

    # and finally we update the ref
    # note: pygithub's equivalent of update ref is edit!
    master_branch.edit(commit.sha)
    return 'SUCCESS'


@app.route('/add_project')
def add_project():
    g = Github(token)
    user = g.get_user()
    new_repo = user.create_repo('Practice Repo')
    return 'AWESOME'

@app.route('/add_collaborator')
def add_collaborator():
    g = Github(token)
    user = g.get_user()
    repo = g.get_repo('Practice Repo')
    repo.add_to_collaborators('sullytesting1987')
    return 'GREAT'



# create a repo. figure out what we need to store. need to be able to programatically add to github contributors.

if __name__ == '__main__':
    app.run(debug=True)
