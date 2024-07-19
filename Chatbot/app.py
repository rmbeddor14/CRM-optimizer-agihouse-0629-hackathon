## make sure you run the Add Data to Data Store part first so that you can seed the data store 

from flask import Flask, render_template, request
import sys, json
from sentence_transformers import SentenceTransformer
from astrapy import DataAPIClient
from openai import OpenAI
import os

openaiclient =  OpenAI()

app = Flask(__name__)

client = DataAPIClient(os.environ.get('DATASTAX_API_KEY'))
db = client.get_database_by_api_endpoint(
  os.environ.get('DATASTAX_API_ENDPOINT')
)

## match the collection name to the astra collection you created in the Add Data to Data Store part 
collection_name = "masked_data_with_metadata"


def ask(query):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_vector = model.encode(query).tolist()
    collection0 = db.get_collection(collection_name)
    results = collection0.find({}, sort={"$vector": query_vector}, limit=5)
    output = ""
    for res in results:
        for key in res:
            entry = f"<td>{res[key]}</td>"
            output += entry
        entry = f"<tr>{entry}</tr>"
    prompt = output + query
    print(prompt)


    completion = openaiclient.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
        {"role": "system", "content": output},
        {"role": "user", "content": query}
        ]
        )
    print(completion.choices[0].message)

    # # Pretty print the result
    # completion_dict = completion.choices[0].message.to_dict()
    # pretty_output = json.dumps(completion_dict, indent=4)
    # Convert the completion object to a dictionary
    completion_dict = completion.to_dict()

    # Extract the content
    content = completion_dict['choices'][0]['message']['content']
    # Replace newline characters with spaces
    cleaned_content = content.replace('\n', ' ')
    print(cleaned_content)


    
    return f"{cleaned_content}" #removed table

class Object:
    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__, 
            sort_keys=True,
            indent=4)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get")
def get_bot_response():
    query = request.args.get('msg')
    return ask(query)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=54321)
