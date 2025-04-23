import sys
from crewai_primer_maker.crew import PrimerCrew  # Make sure the path is correct

def runAgentPrimer(inputs):
    print("Starting")
    result = PrimerCrew().crew().kickoff(inputs=inputs)
    return result
