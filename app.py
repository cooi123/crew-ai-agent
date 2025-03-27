#!/usr/bin/env python
import os
import json
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
from crewai_plus_lead_scoring.main import run
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
            status=200,
            mimetype='application/json'
        )
    
    userInputs = request.json

    result = run(userInputs)

    return Response(
        response=json.dumps(result.json_dict, indent=2),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(host="localhost", port=os.environ.get("PORT"), debug=True)