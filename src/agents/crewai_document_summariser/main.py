import sys
from crewai_document_summariser.crew import DocumentSummariserCrew
from crewai_document_summariser.models.document_summariser_input import DocumentSummariserInputModel

def runSummarizerAgent(inputs:DocumentSummariserInputModel, **kwargs):
    
    print("Starting")
    result = DocumentSummariserCrew(inputs.document).crew().kickoff(inputs=inputs.model_dump())
    return result
