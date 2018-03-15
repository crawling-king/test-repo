# -*- coding: utf-8 -*-
"""
Created on Fri Mar  9 15:36:36 2018

@author: SANTO
"""
import sqlite3
from rasa_nlu.converters import load_data
from rasa_nlu import training_data
from rasa_nlu.config import RasaNLUConfig
from rasa_nlu.model import Trainer

#using rasa-nlu to create interpreter in following block
args = {"pipeline":"spacy_sklearn"}
#configuration
config = RasaNLUConfig(cmdline_args = args)
#trainer
trainer = Trainer(config)
#load training data then train model to create interpreter
training_data = load_data("training_data.json")
interpreter = trainer.train(training_data)

responses = ["I'm sorry :( I couldn't find anything like that",
 '{} is a great hotel!',
 '{} or {} would work!',
 '{} is one option, but I know others too :)']

def negated_ents(phrase, ent_vals):
    ents = [e for e in ent_vals if e in phrase]
    ends = sorted([phrase.index(e)+len(e) for e in ents])
    start = 0
    chunks = []
    for end in ends:
        chunks.append(phrase[start:end])
        start = end
    result = {}
    for chunk in chunks:
        for ent in ents:
            if ent in chunk:
                if "not" in chunk or "n't" in chunk:
                    result[ent] = False
                else:
                    result[ent] = True
    return result


def find_hotels(params, neg_params):
    query = 'SELECT * FROM hotels'
    if len(params) > 0:
        filters = ["{}=?".format(k) for k in params] +                  ["{}!=?".format(k) for k in neg_params] 
        query += " WHERE " + " and ".join(filters)
    t = tuple(params.values())
    
    # open connection to DB
    conn = sqlite3.connect(r'C:\Users\SANTO\Downloads\hotels.db')
    # create a cursor
    c = conn.cursor()
    c.execute(query, t)
    return c.fetchall()

# Define the respond function
def respond(message, params, neg_params):
    # Extract the entities
    entities = interpreter.parse(message)["entities"]
    ent_vals = [e["value"] for e in entities]
    # Look for negated entities
    negated = negated_ents(message, ent_vals)
    for ent in entities:
        if ent["value"] in negated and negated[ent["value"]]:
            neg_params[ent["entity"]] = str(ent["value"])
        else:
            params[ent["entity"]] = str(ent["value"])
    # Find the hotels
    results = find_hotels(params, neg_params)
    names = [r[0] for r in results]
    n = min(len(results),3)
    # Return the correct response
    return responses[n].format(*names), params, neg_params

# Initialize params and neg_params
params = {}
neg_params = {}

# Pass the messages to the bot
for message in ["I want a cheap hotel", "but not in the north of town"]:
    print("USER: {}".format(message))
    response, params, neg_params = respond(message, params, neg_params)
    print("BOT: {}".format(response))
