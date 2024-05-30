import os
import re
import subprocess
import requests
from flask import Flask, request, jsonify, render_template
from git import Repo
import openai
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

app = Flask(__name__)

# LangChain 설정
template = "Translate the following English comment to Korean:\n\n\"{comment}\""
prompt_template = PromptTemplate(input_variables=["comment"], template=template)

def translate_comment(comment, llm_chain):
    prompt = f"Translate the following English comment to Korean:\n\n\"{comment}\""
    translated_comment = llm_chain.run(prompt)
    return translated_comment.strip()

def translate_comments_in_file(file_path, llm_chain):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    translated_lines = []
    for line in lines:
        match = re.match(r'^\s*//(.*)', line)
        if match:
            comment = match.group(1).strip()
            translated_comment = translate_comment(comment, llm_chain)
            translated_lines.append(f'// {translated_comment}\n')
        else:
            translated_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(translated_lines)

def translate_comments_in_directory(directory_path, llm_chain):
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.rs'):
                file_path = os.path.join(root, file)
                translate_comments_in_file(file_path, llm_chain)

def clone_repo(repo_url):
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    if os.path.exists(repo_name):
        subprocess.run(["rm", "-rf", repo_name])
    Repo.clone_from(repo_url, repo_name)
    return repo_name

def create_pull_request(repo_name, branch_name, base_branch, github_token):
    repo = Repo(repo_name)
    origin = repo.remote(name='origin')
    new_branch = repo.create_head(branch_name)
    new_branch.checkout()
    repo.git.add(A=True)
    repo.index.commit("Translate comments to Korean")
    origin.push(refspec=f"{branch_name}:{branch_name}")

    url = f"https://api.github.com/repos/{repo_name}/pulls"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "title": "Translate comments to Korean",
        "head": branch_name,
        "base": base_branch,
        "body": "This PR translates all English comments to Korean."
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.form
    repo_url = data['repo_url']
    branch_name = data['branch_name']
    base_branch = data.get('base_branch', 'main')
    openai_api_key = data['openai_api_key']
    github_token = data['github_token']

    # OpenAI API 키 설정
    openai.api_key = openai_api_key

    # LangChain 설정
    llm = OpenAI(api_key=openai_api_key, model="text-davinci-003")
    llm_chain = LLMChain(llm=llm, prompt=prompt_template)

    repo_name = clone_repo(repo_url)
    translate_comments_in_directory(repo_name, llm_chain)
    pr_response = create_pull_request(repo_name, branch_name, base_branch, github_token)

    return jsonify(pr_response)

if __name__ == '__main__':
    app.run(debug=True)
