import warnings

# To suppress all warnings
warnings.filterwarnings("ignore")

# To suppress a specific warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

#from common import * 


import openai  # Ensure you have the OpenAI Python library installed
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain.prompts import ChatPromptTemplate
import shutil
import settings
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain.chat_models import ChatOpenAI
from cachetools import TTLCache
from datetime import datetime, timedelta


import math

# Set your OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"] 
DATA_PATH = "RAG"
FIA_PATH = "fia"

CONVERSATION_FILE = 'lib/conversation.json'
MAX_CONVERSATION_AGE = timedelta(hours=6)
def get_conversations(as_json=False):
    # Check if the conversation file exists
    if not os.path.exists(CONVERSATION_FILE):
        # If the file doesn't exist, return an empty string or an empty list, depending on the format
        return {} if as_json else ''
    # Load conversations from the JSON file
    with open(CONVERSATION_FILE, 'r') as file:
        conversations = json.load(file)
    if as_json:
        return conversations
    else:
        # Concatenate user messages and responses with separator
        conversation_text = '\n---\n'.join(f"{conv['user_message']}\n{conv['response']}" for conv in conversations)
        return conversation_text

def store_conversation(user_message, response):
    # Load existing conversations
    conversations = get_conversations(True)
    # Remove conversations older than 6 hours
    conversations = [conv for conv in conversations if datetime.now() - datetime.strptime(conv['timestamp'], '%Y-%m-%d %H:%M:%S') <= MAX_CONVERSATION_AGE]
    # Add the new conversation to the list
    conversations.append({'user_message': user_message, 'response': response, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    # Write conversations back to the JSON file
    with open(CONVERSATION_FILE, 'w') as file:
        json.dump(conversations, file)

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_colorful_intro(name):
    clear_terminal()
    print("\033[1;32m")  # Set text color to green
    
    print("**************************************************************")
    print("*                                                            *")
    print("*               Hi, I'm David, your Formula 1 Expert!        *")
    print("*                                                            *")
    print("**************************************************************")
    print("\033[0m")  # Reset text color
    
    # Print a simple ASCII art resembling the Formula 1 logo
    print("\033[1;33m")  # Set text color to yellow
    print("    _______  _______  _______  _______  _______  _______ ")
    print("   |       ||       ||       ||       ||       ||       |")
    print("   |    _  ||    _  ||   _   ||       ||   _   ||    ___|")
    print("   |   |_| ||   |_| ||  | |  ||       ||  | |  ||   |___ ")
    print("   |    ___||    ___||  |_|  ||      _||  |_|  ||    ___|")
    print("   |   |    |   |    |       ||     |_ |       ||   |___ ")
    print("   |___|    |___|    |_______||_______||_______||_______|")
    print("\033[0m")  # Reset text color
    
    # Print link
    print("\033[1;35m")  # Set text color to magenta
    print(name)
    print("\033[0m")  # Reset text color


def print_text_on_one_line(text):
    return re.sub(r'\s+', ' ', text.strip())




#print_colorful_intro("I will now udpate my RAG and construct Vectors")
def delete_chroma_directory(db):
    """Delete the 'Chroma' directory if it exists."""
    chroma_directory = os.path.join(os.getcwd(), db)
    if os.path.exists(chroma_directory):
        shutil.rmtree(chroma_directory)
        print(f"Deleted Chroma directory at '{chroma_directory}'")
    else:
        print("Chroma directory does not exist.")

def print_text_on_one_line(text):
    return re.sub(r'\s+', ' ', text.strip())


def load_catalog_metadata():
    lib_folder = "lib"
    catalog_file_path = os.path.join(lib_folder, "catalog.json")

    if not os.path.exists(catalog_file_path):
        print("Catalog file does not exist.")
        return {}

    with open(catalog_file_path, "r") as catalog_file:
        catalog = json.load(catalog_file)

    return catalog

import re

def flatten_array_to_json(input_array):
    flattened_array = {}
    for key, value in input_array.items():
        flattened_item = {}
        for k, v in value.items():
            if isinstance(v, (int, str, bool)):
                flattened_item[k] = v
            else:
                flattened_item[k] = json.dumps(v)
        flattened_array[key] = flattened_item
    return flattened_array


def extract_uuid(file_path):
    # Define the regular expression pattern to match the UUID
    pattern = r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
    
    # Find all matches of the pattern in the file path
    matches = re.findall(pattern, file_path)
    
    if matches:
        # Extract the first match (UUID) from the list
        uuid = matches[0]
        return uuid
    else:
        return None

def extract_json_from_string(document):
    metadata = flatten_array_to_json(load_catalog_metadata())
    uid = extract_uuid(document.metadata['source']);
    #raise Exception(metadata[uid])
    return metadata[uid] if uid in metadata else {}


def eval_meta_data(document):
    document.metadata.update(extract_json_from_string(document))
    return document



CROMA_PATH = "intelliq"
def parse_plain_text_documents(path):
    delete_chroma_directory(CROMA_PATH)
    documents = load_documents(path) + load_documents("lib/abstract","*.txt") + get_rag_documents("lib/pdf")
    #documents =  get_rag_documents("lib/pdf")
    #raise Exception(documents[0].metadata)
    chunks = split_text(documents)
    db = Chroma.from_documents(chunks, OpenAIEmbeddings(), persist_directory=CROMA_PATH)

def load_documents(path,glob="*.html"):
    if not os.path.exists(path):
        return []

    loader = DirectoryLoader(path, glob=glob)
    documents = [ eval_meta_data(d) for d in loader.load()]
    return documents


def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # document = chunks[10]
    # print(document.page_content)
    # print(document.metadata)

    return chunks


def read_files_in_directory(limit=None, encoding='utf-8', errors='ignore'):
    """Read files in the 'RAG' directory located in the current working directory."""
    directory_path = os.path.join(os.getcwd(), "RAG")
    
    # Get a list of files sorted by their filenames (which include the date)
    files_sorted = sorted(os.listdir(directory_path), reverse=True)
    
    # Initialize variables to track the number of files read and the file contents
    file_count = 0
    file_contents = []

    # Iterate over sorted files
    for filename in files_sorted:
        # Check if the limit has been reached
        if limit is not None and file_count >= limit:
            break
        
        # Read file contents
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding=encoding, errors=errors) as file:
                file_contents.append(file.read())
                file_count += 1
    
    return file_contents

# delete_chroma_directory("chroma")
# delete_chroma_directory("fiadb")
# delete_chroma_directory("reporter")

def extract_info(text):
    # Define regex patterns to extract relevant information
    patterns = {
        "author": r"From\s+(.*)\s+To",
        "address to": r"To\s+(.*)\s+Date",
        "published on": r"Date\s+(\d{2}\s+\w+\s+\d{4})",
        "document_id": r"Document\s+(\d+)",
        "title": r"Title\s+(.*)\n",
        "description": r"Description\s+(.*)"
    }

    # Initialize extracted information dictionary
    extracted_info = {}

    # Extract information using regex patterns
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            extracted_info[key] = match.group(1).strip()

    json_data = json.dumps(extracted_info, indent=4)
    return extracted_info

def get_rag_documents(folder_path):
    """
    Returns a list of documents related to Retrieval Augmentation Generation (RAG)
    from the specified folder containing PDFs.
    
    Parameters:
    folder_path (str): The path to the folder containing PDF documents.
    
    Returns:
    list: A list of PDF documents related to RAG.
    """
    rag_documents = []
    errors = []
    openai_emb = OpenAIEmbeddings()

    
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            try:
                print("\033[92mSucces:\033[0m %s" % file_path)
                pdf_loader = PyPDFLoader(file_path)
                document = pdf_loader.load()
                rag_documents.append(eval_meta_data(document[0]))
            except Exception as e: 
                print("\033[91mFailed: %s\033[0m %s" % (e,file_path))
                errors.append({"file" : file_path, "error" : e})
    #raise Exception(rag_documents)
    return rag_documents

PDF_PATH = "lib/pdf"
HTML_PATH = "lib/html"
TEXT_PATH= "lib/abstract"


def generate_apa_citation(data):
    # Decode JSON-encoded values if necessary
    authors = json.loads(data['authors'])
    journal_details = json.loads(data['journal_details'])
    websites = ["http://127.0.0.1:5000/document?document_id=%s" % data["id"]]

    # Format authors
    authors_str = ', '.join([f"{author['last_name']}, {author['first_name']}" for author in authors])

    # Format year
    if data['year']:
        year = str(data['year'])
    else:
        year = '(n.d.)'

    # Format title and remove file extension
    title = os.path.splitext(data['title'])[0]

    # Format journal details
    journal_info = ''
    # if journal_details['volume'] and journal_details['issue'] and journal_details['pages']:
    #     journal_info = f"<i>{journal_details['name']}</i>, {journal_details['volume']}({journal_details['issue']}), {journal_details['pages']}"
    # elif journal_details['volume']:
    #     journal_info = f"<i>{journal_details['name']}</i>, {journal_details['volume']}"
    # else:
    #     journal_info = ''

    # Format websites
    website_str = f"<a target='_blank' href='{websites[0]}'><i class='fa-solid fa-arrow-up-right-from-square'></i></a>" if websites else ''

    # Construct citation
    citation = f"{authors_str} ({year}). {title}. {journal_info} {website_str}"
    return citation

def read_personas_from_file(file_path):
    """
    Read text from a file.

    Args:
        file_path (str): The path to the text file.

    Returns:
        str: The text read from the file.
    """
    try:
        with open(file_path, 'r') as file:
            text = file.read()
        return text
    except FileNotFoundError:
        print("File not found.")
        return ""

def write_personas_to_file(file_path, personas):
    """
    Write personas to a text file.

    Args:
        file_path (str): The path to the text file.
        personas (list): A list of personas to write to the file.
    """
    try:
        with open(file_path, 'w') as file:
            file.write(personas)
        print("Personas have been written to the file.")
    except IOError:
        print("Error writing to the file.")


def respond_to_prompt(question):
    db = Chroma(persist_directory=CROMA_PATH, embedding_function=OpenAIEmbeddings())
    results = db.similarity_search_with_relevance_scores(question, k=20)

    if len(results) == 0 or results[0][1] < 0.7:
        return f"Mmmmm 🤔 I don't seem to have any information on this topic..."

    persona = read_personas_from_file("lib/whoami.txt")

    PROMPT_TEMPLATE="""
    {persona}
    {context}

    ---
    Past Conversion: 
    {conversation}
    --- 

    Answer the question based on the above context: {query}
    """

    context_text="\n\n---\n\n".join([ doc.page_content for doc, score in results])
    conversation = get_conversations()
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    #raise Exception(prompt_template)
    prompt = prompt_template.format(context=context_text, query=question,conversation=conversation, persona=persona)
    #return prompt

    model = ChatOpenAI()
    response_text = model.predict(prompt)
    formatted_response = f"\n{response_text}\n\n<strong>My References</strong>\n\n"

    store_conversation(question, response_text)
    # conversation = get_conversations()
    # return conversation
    meta = load_catalog_metadata()
    for doc, _score in results:
        icon = ""
        if meta[doc.metadata['id']]["abstract"]:
            icon ="<i class='fa-regular fa-lightbulb'></i>"
        formatted_response +=  "\n<div  document-id='%s' class='references'><strong class='text-success'>%s [%s%%]</strong> %s</div>" % (doc.metadata['id'], icon, math.ceil(_score * 100),  generate_apa_citation(doc.metadata) )


    return formatted_response


