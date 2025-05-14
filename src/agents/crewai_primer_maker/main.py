from .crew import PrimerCrew  # Make sure the path is correct

def runAgentPrimer(inputs, **kwargs):
    
    print("Starting")
    result = PrimerCrew().crew().kickoff(inputs=inputs)
    return result
