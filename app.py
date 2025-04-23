#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import json
import requests
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
#from crewai_plus_lead_scoring.main import run
#from crewai_customer_research.main import runAgent
from crewai_primer_maker.main import runAgentPrimer
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)
#cors = CORS(app, resources={r"/*": {"origins": "*"}})

# @app.route('/', methods=['GET'])
# def default():
#     return "Welcome to Studio Agents"

# @app.route('/lead/analysis', methods=['POST'])
# def leadAnalysis():
#     if not request.json:
#         result = {'statusCode': 400,'message':'Invalid data provided'}
#         return Response(
#             response=json.dumps(result.json_dict, indent=2),
#             status=400,
#             mimetype='application/json'
#         )
    
#     #userInputs = request.json
#     userInputs = {
#         'topic': 'Banking'
#     }
#     runAgentPrimer().crew().kickoff(inputs=userInputs)
#     result = runAgentPrimer(userInputs)

#     headers = {
#         "Content-Type": "application/json",
#     }

#     response = requests.post(userInputs["webhook_url"], headers=headers, data=json.dumps(result.json_dict, indent=2))

#     return Response(
#         response=json.dumps(result.json_dict, indent=2),
#         status=response.status_code,
#         mimetype='application/json'
#     )

# @app.route('/lead/createEmail', methods=['POST'])
# def leadCreateEmail():
#     if not request.json:
#         result = {'statusCode': 400,'message':'Invalid data provided'}
#         return Response(
#             response=json.dumps(result.json_dict, indent=2),
#             status=400,
#             mimetype='application/json'
#         )
    
#     userInputs = request.json

#     result = runAgent(userInputs)

#     # headers = {
#     #     "Content-Type": "application/json",
#     # }

#     # response = requests.post(userInputs["webhook_url"], headers=headers, data=json.dumps(result.json_dict, indent=2))

#     return Response(
#         response=json.dumps(result.json_dict, indent=2),
#         status=200,
#         mimetype='application/json'
#     )


@app.route('/consultant/primer', methods=['POST'])
def consultantCreatePrimer():
    if not request.json:
        result = {'statusCode': 400,'message':'Invalid data provided'}
        return Response(
            response=json.dumps(result.json_dict, indent=2),
            status=400,
            mimetype='application/json'
        )
    
    userInputs = request.json
    print(userInputs)
    #userInputs = {"topic":"internet banking"}

    result = runAgentPrimer(userInputs)
    headers = {
        "Content-Type": "application/json",
    }
    print("End Analysis")
    print(result)
    #response_data = {'result': result}
    #return json.dumps(result.json_dict)

    #response = requests.post(userInputs["webhook_url"], headers=headers, data=json.dumps(result.json_dict, indent=2))

    return Response(
        response=json.dumps(result.json_dict, indent=2),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(host="localhost", port=os.environ.get("PORT",8000), debug=True)
    #app.run(host="localhost", port=8001, debug=True)

    