import sys
from crewai_customer_research.crew import CustomerOutreachCrew  # Make sure the path is correct

def runAgent(inputs):
    result = CustomerOutreachCrew().crew().kickoff(inputs=inputs)
    return result
