import sys
from crewai_customer_research.crew import CustomerOutreachCrew  # Make sure the path is correct
from crewai_customer_research.models.agent_input import AgentInput

def runAgent(inputs:AgentInput ):
    inputs_dict= inputs.model_dump()
    result = CustomerOutreachCrew().crew().kickoff(inputs=inputs_dict)
    return result
