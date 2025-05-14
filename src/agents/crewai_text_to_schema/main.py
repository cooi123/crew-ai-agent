from .crew import SchemaProcessorCrew
from pydantic import BaseModel
from typing import Type

def runAgentTextToSchema(input_data: str, target_model: Type[BaseModel]) -> str:
    """
    Run the text to schema agent
    """
    crew = SchemaProcessorCrew(target_model=target_model)
    return crew.run(input_data)

