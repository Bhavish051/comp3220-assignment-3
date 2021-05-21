import requests
from bs4 import BeautifulSoup
import spacy
from spacy.language import FactoryMeta
from spacy.matcher import Matcher
from tqdm import tqdm
import pandas as pd
import os

r = requests.get('http://localhost:8080/student.html', auth=('user', 'pass'))


with open('/Users/bhavish051/Desktop/comp3220-assignment-3/student.html', 'r') as f:
    contents = f.read()
    soup = BeautifulSoup(contents, 'html.parser')

textlist = []

for para_tag in soup.find_all('p'):
    Text = para_tag.decode_contents()
    # print(Text)
    textlist.append(Text)

nlp = spacy.load('en_core_web_sm')

# print(textlist)

ent_pairs = []


def get_entities(sent):
    ent1 = ""           # Variable for storing the subject.
    ent2 = ""           # Variable for storing the object.

    # Variable for dependency tag of previous token in the sentence.
    prv_tok_dep = ""
    prv_tok_text = ""   # Variable for previous token in the sentence.

    prefix = ""         # Variable for storing compounds.
    modifier = ""       # Variable for storing modifieres.

    # Loop through the tokens in the sentence.
    for tok in nlp(sent):
        # Check if a token is a punctuation mark or not.
        if tok.dep_ != "punct":
            # Check if a token is a compound one or not.
            if tok.dep_ == "compound":
                # If yes, then store the token in the prefix variable.
                prefix = tok.text
                # print("Prefix at 49: " + prefix)
                # Check if the previous token was also a compound one.
                if prv_tok_dep == "compound":
                    # If yes, then update the prefix variable.
                    prefix = prv_tok_text + " " + tok.text
                    # print("Prefix at 54: " + prefix)

            # Check if a token is a modifier or not.
            if tok.dep_.endswith("mod") == True:
                # If yes, then store the token in the modifier varible.
                modifier = tok.text
                # Check if the previous token was a compound one.
                if prv_tok_dep == "compound":
                    # If yes, then update the modifier variable.
                    modifier = prv_tok_text + " " + tok.text

            # Check if a token is the subject.
            if tok.dep_.find("subj") == True:
                # If yes, then concatenate the modifier, prefix, and token
                # and assign the result to the subject variable (ent1).
                ent1 = modifier + " " + prefix + " " + tok.text
                # print("At line 68" + ent1)
                # print("At line 68 Prefix: " + prefix)
                # Reset the following variables: prefix, modifier, prv_tok_dep, and prv_tok_text.
                prefix = ""
                modifier = ""
                prv_tok_dep = ""
                prv_tok_text = ""

            ent2 = modifier + " " + prefix + " " + tok.text

            # Update the variable for the dependency tag for the previous token.
            prv_tok_dep = tok.dep_
            # print("Token Dep:" + tok.dep_)
            # Update the variable for the previous token in the sentence.
            prv_tok_text = tok.text
        # print(ent2)
    return [ent1.strip(), ent2.strip()]


for e in tqdm(textlist):
    ent_pairs.append(get_entities(e))

subjects = [i[0] for i in ent_pairs]
objects = [i[1] for i in ent_pairs]


def get_relation(sent):

    doc = nlp(sent)

    # Matcher class object
    matcher = Matcher(nlp.vocab)

    # Define the pattern.
    pattern = [
        [
            {'DEP': 'ROOT'},
            {'DEP': 'prep', 'OP': "?"},
            {'DEP': 'agent', 'OP': "?"},
            {'POS': 'ADJ', 'OP': "?"},
        ],
        [
            {'DEP': 'ROOT'},
            {'POS': 'DET', 'OP': "?"},
        ],
        [
            {'DEP': 'ROOT'},
            {'POS': 'ADJ', "OP": "?"},
            {"POS": "ADP", "OP": "?"}
        ],
        [
            {'DEP': 'ROOT'},
            {'DEP': 'prep', 'OP': "?"},
            {'DEP': 'agent', 'OP': "?"},
            {'POS': 'ADJ', 'OP': "?"}
        ],
        [
            {'ORTH': 'is'},
            {'ORTH': 'a'},
            {"POS": "NOUN", "OP": "?"},
            {"POS": "ADP", "OP": "+"}
        ]
    ]

    matcher.add("matching_1", pattern)

    matches = matcher(doc)
    k = len(matches) - 1

    span = doc[matches[k][1]: matches[k][2]]

    return(span.text)


doc = nlp(textlist[3])

for tok in doc:
    print(tok.text, " ", tok.dep_)

relations = [get_relation(i) for i in tqdm(textlist)]

df = pd.DataFrame({'source': subjects, 'edge': relations, 'target': objects})

# print(df)

# print(objects)
# df.to_csv('Data.csv', index=False)

print(os.system('python3 -m rdfizer -c ./config.ini'))

import rdflib

Out = rdflib.Graph()

res = Out.parse("triples.nt", format="ntriples")

Output = res.serialize(format = 'turtle').decode("utf-8")

print(Output)


## 

res = Out.query(
    """PREFIX ns1: <http://schema.org/> 
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?who
        WHERE { ?x ns1:name ?who .
            ?x rdf:type ?y .
            ?y rdfs:label "person" .
        }
    """
)

print(res.serialize(format="json").decode("utf-8"))

res = Out.query(
    """PREFIX ns1: <http://schema.org/> 
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?who
        WHERE { ?x ns1:name ?who .
            ?x rdf: about ?y .
            ?y rdfs: label "Artificial Intelligence" .
            }
    """
)

print(res.serialize(format="json").decode("utf-8"))