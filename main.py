import os
import re
import openai
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# OpenAI API 키 설정
openai.api_key = ''  # 실제 API 키로 변경

def translate_comment(comment, llm_chain):
    prompt = f"Translate the following English comment to Korean:\n\n\"{comment}\""
    translated_comment = llm_chain.run({"comment": comment})
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

# LangChain 설정
llm = ChatOpenAI(openai_api_key=openai.api_key, model="gpt-4")
template = "Translate the following English comment to Korean:\n\n\"{comment}\""
prompt_template = PromptTemplate(input_variables=["comment"], template=template)
llm_chain = LLMChain(llm=llm, prompt=prompt_template)

# TODO: fix the target path
translate_comments_in_directory('C:\\Users\\krnom\\work\\rust\\100-exercises-to-learn-rust', llm_chain)
