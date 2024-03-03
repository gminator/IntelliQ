from flask import Flask, redirect, render_template, request, session, jsonify
import yaml

from mendeley import Mendeley
from mendeley.session import MendeleySession
import os
import requests
import os
import requests
import json
from rag import * 

def calculate_rag_count(json_data):
    rag_true_count = sum(1 for file_data in json_data.values() if file_data['rag'])
    rag_false_count = len(json_data) - rag_true_count
    total_count = len(json_data)
    rag_true_percentage = (rag_true_count / total_count) * 100 if total_count > 0 else 0
    rag_false_percentage = (rag_false_count / total_count) * 100 if total_count > 0 else 0
    return rag_true_count, rag_false_count, rag_true_percentage, rag_false_percentage, total_count

def check_file_existence(file_id):
    lib_folder = "lib"
    subdirectories = ["pwd", "html", "abstract"]
    return os.path.exists(os.path.join(lib_folder, "pdf", f"{file_id}_1.pdf")) \
                or os.path.exists(os.path.join(lib_folder, "html",f"{file_id}.html")) \
                or os.path.exists(os.path.join(lib_folder, "abstract", f"{file_id}.txt"))
           
def store_catalog_metadata(documents):
    catalog = {}

    for document in documents:
        #raise Exception(document.fields())
        doc_metadata = {
            "id": document.id,
            "title": document.title,
            "year": document.year,
            "read": document.read,
            "abstract": document.abstract,
            #"parts" : [f.download_url for f in document.files.list().items] if document.file_attached else [],
            "websites" : [ w for w in document.websites] if document.websites else [],
            "rag" : check_file_existence(document.id),
            "parts" : len(document.files.list().items) if document.file_attached else 1,
            "authors": [{"first_name": author.first_name, "last_name": author.last_name} for author in document.authors] if document.authors else [],
            "journal_details": {
                "name": document.publisher,
                "volume": document.volume,
                "issue": document.issue,
                "pages": document.pages
            }
        }
        catalog[document.id] = doc_metadata

    lib_folder = "lib"
    catalog_file_path = os.path.join(lib_folder, "catalog.json")

    with open(catalog_file_path, "w") as catalog_file:
        json.dump(catalog, catalog_file, indent=4)

    print(f"Catalog metadata stored in {catalog_file_path}")

import os
import json


# Example usage:
# catalog_data = load_catalog_metadata()
# print(catalog_data)


# Example usage:
# store_catalog_metadata(list_of_documents)

def download_mendeley_documents(documents):
    lib_folder = "lib"
    
    # Create 'lib' folder if it doesn't exist
    if not os.path.exists(lib_folder):
        os.makedirs(lib_folder)

    for document in documents:
        # Create subfolder for each document
        #raise Exception()
        if check_file_existence(document.id):
            print(f"Already Downloaded for document {document.id}")
            continue

        try:
            # Download attached files (assuming they are PDFs)
            if document.file_attached:
                document_folder = os.path.join(lib_folder, f"pdf")
                os.makedirs(document_folder, exist_ok=True)

                part = 0
                for file in document.files.list().items:
                    if hasattr(file, 'download_url'):
                        part += 1
                        response = requests.get(file.download_url)
                        if response.status_code == 200:
                            extension = "pdf"
                            file_type_folder = document_folder  # Get folder based on extension
                            #Exception(file_type_folder)
                            os.makedirs(file_type_folder, exist_ok=True)
                            file_path = os.path.join(file_type_folder, f"{document.id}_{part}.{extension}")
                            with open(file_path, "wb") as f:
                                f.write(response.content)
                            print(f"Downloaded {extension} for document {document.id} to {file_path}")
                        else:
                            print(f"Failed to download file for document {document.id} from {file.download_url} {response.status_code}")
                    # Download content from URLs if available
            elif document.websites:
                #document_folder = os.path.join(lib_folder, f"html")
                for website in document.websites:
                    response = requests.get(website)
                    if response.status_code == 200:
                        website_folder = os.path.join(lib_folder, "html")
                        os.makedirs(website_folder, exist_ok=True)
                        website_path = os.path.join(website_folder, f"{document.id}.html")
                        with open(website_path, "w") as website_file:
                            website_file.write(response.text)
                        print(f"Downloaded content from {website} for document {document.id} to {website_path}")
                    else:
                        print(f"Failed to download content from {website} for document {document.id} {response.status_code}")

            # Store abstract as plain text if available
            elif document.abstract:
                abstract_folder = os.path.join(lib_folder, "abstract")
                os.makedirs(abstract_folder, exist_ok=True)
                abstract_path = os.path.join(abstract_folder, f"{document.id}.txt")
                with open(abstract_path, "w") as abstract_file:
                    abstract_file.write(document.abstract)
                print(f"Stored abstract as plain text for document {document.id} to {abstract_path}")
        except:
            continue


# Example usage:
# download_mendeley_documents(list_of_documents)

with open('config.yml') as f:
    config = yaml.load(f,Loader=yaml.Loader)

REDIRECT_URI = 'http://127.0.0.1:5000/oauth'

app = Flask(__name__)
app.debug = True
app.secret_key = config['clientSecret']

mendeley = Mendeley(config['clientId'], config['clientSecret'], REDIRECT_URI)



@app.route('/assistant')
def assistant():
    # This route will handle the assistant chat interface
    catalog = load_catalog_metadata()
    return render_template('chat.html', catalog=catalog)

@app.route('/respond', methods=['POST'])
def respond():
    # This route will handle the AJAX request sent by the chat client
    # Implement the logic to process the user's message and return the response
    # Example:
    user_message = request.form.get('message')
    # Process the user's message and generate a response
    # For demonstration purposes, let's just return a dummy response
    response = "This is a dummy response."
    #return jsonify({"message": "\nThis is what the literature has to say on the matter: Systems thinking refers to a holistic approach to understanding and analyzing complex systems. It involves considering the interrelationships and interactions between various components of a system, rather than focusing solely on individual parts. Systems thinking allows for the examination of how different elements of a system influence each other and how changes in one part can affect the entire system.\n\nIn the context of the research paper \"A Definition of Systems Thinking: A Systems Approach,\" systems thinking is defined as an approach that integrates different components as a system. It is considered critical in handling the complexity that the world is facing and has potential applications in various disciplines.\n\nOverall, systems thinking involves understanding the interconnectedness and interdependencies of parts within a system, and how they contribute to the overall functioning and behavior of the system. It emphasizes a holistic perspective and can be applied to various domains, including management, engineering, and social sciences.\n\n<strong>My References</strong>\n\n\n<div  document-id='915cd929-5734-3aaa-91df-c12254115696' class='references'><strong class='text-success'>81%</strong> Arnold, Ross D., Wade, Jon P. (2015). A definition of systems thinking: A systems approach. <i>Elsevier Masson SAS</i>, 44(C), 669-678. Retrieved from <a href='http://dx.doi.org/10.1016/j.procs.2015.03.050'>http://dx.doi.org/10.1016/j.procs.2015.03.050</a></div>\n<div  document-id='915cd929-5734-3aaa-91df-c12254115696' class='references'><strong class='text-success'>81%</strong> Arnold, Ross D., Wade, Jon P. (2015). A definition of systems thinking: A systems approach. <i>Elsevier Masson SAS</i>, 44(C), 669-678. Retrieved from <a href='http://dx.doi.org/10.1016/j.procs.2015.03.050'>http://dx.doi.org/10.1016/j.procs.2015.03.050</a></div>\n<div  document-id='915cd929-5734-3aaa-91df-c12254115696' class='references'><strong class='text-success'>80%</strong> Arnold, Ross D., Wade, Jon P. (2015). A definition of systems thinking: A systems approach. <i>Elsevier Masson SAS</i>, 44(C), 669-678. Retrieved from <a href='http://dx.doi.org/10.1016/j.procs.2015.03.050'>http://dx.doi.org/10.1016/j.procs.2015.03.050</a></div>\n<div  document-id='915cd929-5734-3aaa-91df-c12254115696' class='references'><strong class='text-success'>79%</strong> Arnold, Ross D., Wade, Jon P. (2015). A definition of systems thinking: A systems approach. <i>Elsevier Masson SAS</i>, 44(C), 669-678. Retrieved from <a href='http://dx.doi.org/10.1016/j.procs.2015.03.050'>http://dx.doi.org/10.1016/j.procs.2015.03.050</a></div>\n<div  document-id='8f5bae5c-94f8-3591-a616-72e5555959ec' class='references'><strong class='text-success'>77%</strong> Cld, The (2018). Causal Loop Diagrams - Archetypes. . </div>"})
    return jsonify({'message': respond_to_prompt(user_message)})

@app.route('/')
def home():
    if 'token' in session:
        return redirect('/listDocuments')

    auth = mendeley.start_authorization_code_flow()
    session['state'] = auth.state

    return render_template('home.html', login_url=(auth.get_login_url()))


@app.route('/oauth')
def auth_return():
    auth = mendeley.start_authorization_code_flow(state=session['state'])
    mendeley_session = auth.authenticate(request.url)

    session.clear()
    session['token'] = mendeley_session.token

    return redirect('/listDocuments')


@app.route('/listDocuments')
def list_documents():
    if 'token' not in session:
        return redirect('/')

    mendeley_session = get_session_from_cookies()

    name = mendeley_session.profiles.me.display_name
    docs = mendeley_session.documents.list(page_size=500,view='all').items

    catalog = load_catalog_metadata()
    rag_true_count, rag_false_count, rag_true_percentage, rag_false_percentage, total_count = calculate_rag_count(catalog)


    return render_template('library.html', name=name, docs=docs,catalog=catalog,
        rag_true_count=rag_true_count, 
        rag_false_count=rag_false_count, 
        rag_true_percentage=rag_true_percentage, 
        rag_false_percentage=rag_false_percentage, 
        total_count=total_count )


@app.route('/document')
def get_document():
    if 'token' not in session:
        return redirect('/')

    mendeley_session = get_session_from_cookies()

    document_id = request.args.get('document_id')
    doc = mendeley_session.documents.get(document_id)

    return render_template('metadata.html', doc=doc)


@app.route('/metadataLookup')
def metadata_lookup():
    if 'token' not in session:
        return redirect('/')

    mendeley_session = get_session_from_cookies()

    doi = request.args.get('doi')
    doc = mendeley_session.catalog.by_identifier(doi=doi)

    return render_template('metadata.html', doc=doc)


@app.route('/download')
def download():
    if 'token' not in session:
        return redirect('/')

    mendeley_session = get_session_from_cookies()

    name = mendeley_session.profiles.me.display_name
    docs = mendeley_session.documents.list(page_size=500,view='all').items

    download_mendeley_documents(docs)
    store_catalog_metadata(docs)
    catalog = load_catalog_metadata()
    rag_true_count, rag_false_count, rag_true_percentage, rag_false_percentage, total_count = calculate_rag_count(catalog)
    

    #Build Rag 
    parse_plain_text_documents("lib/html")
    


    return render_template('library.html', name=name, docs=docs, catalog=catalog,
        rag_true_count=rag_true_count, 
        rag_false_count=rag_false_count, 
        rag_true_percentage=rag_true_percentage, 
        rag_false_percentage=rag_false_percentage, 
        total_count=total_count )


@app.route('/logout')
def logout():
    session.pop('token', None)
    return redirect('/')


def get_session_from_cookies():
    return MendeleySession(mendeley, session['token'])


if __name__ == '__main__':
    app.run()
