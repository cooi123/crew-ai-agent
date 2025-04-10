#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import json
import requests
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
from crewai_plus_lead_scoring.main import run
from crewai_customer_research.main import runAgent
load_dotenv()
app = Flask(__name__)

@app.route('/', methods=['GET'])
def default():
    return "Welcome to Studio Agents"

@app.route('/lead/analysis', methods=['POST'])
def leadAnalysis():
    if not request.json:
        result = {'statusCode': 400,'message':'Invalid data provided'}
        return Response(
            response=json.dumps(result.json_dict, indent=2),
            status=400,
            mimetype='application/json'
        )
    
    userInputs = request.json

    result = run(userInputs)

    headers = {
        "Content-Type": "application/json",
    }

    response = requests.post(userInputs["webhook_url"], headers=headers, data=json.dumps(result.json_dict, indent=2))

    return Response(
        response=json.dumps(result.json_dict, indent=2),
        status=response.status_code,
        mimetype='application/json'
    )

@app.route('/lead/createEmail', methods=['POST'])
def leadCreateEmail():
    if not request.json:
        result = {'statusCode': 400,'message':'Invalid data provided'}
        return Response(
            response=json.dumps(result.json_dict, indent=2),
            status=400,
            mimetype='application/json'
        )
    
    userInputs = request.json

    result = runAgent(userInputs)

    # headers = {
    #     "Content-Type": "application/json",
    # }

    # response = requests.post(userInputs["webhook_url"], headers=headers, data=json.dumps(result.json_dict, indent=2))

    return Response(
        response=json.dumps(result.json_dict, indent=2),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(host="localhost", port=os.environ.get("PORT"), debug=True)