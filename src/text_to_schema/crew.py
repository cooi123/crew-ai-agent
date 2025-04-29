from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel
from typing import Dict, Any, Type, Optional, TypeVar, Generic

class TextInput(BaseModel):
    """Model for raw text input"""
    raw_text: str
    schema_description: Optional[str] = None
T = TypeVar("T", bound=BaseModel)

@CrewBase
class SchemaProcessorCrew(Generic[T]):
    """Crew for processing unstructured text into structured schema"""
    def __init__(self, target_model: Type[T], schema_description: Optional[str] = None):
        # Store your custom parameters
        self.target_model = target_model
        
        if not schema_description:
            schema_description = self._generate_schema_description(target_model)
        
        self.schema_description = schema_description
    
    def _generate_schema_description(self, model: Type[T]) -> str:
        """
        Generate a description of fields to extract from the model
        """
        schema_dict = model.model_json_schema()
        fields = []
        
        # Get field descriptions from schema
        for field_name, field_info in schema_dict.get('properties', {}).items():
            description = field_info.get('description', '')
            field_type = field_info.get('type', '')
            
            if description:
                fields.append(f"- {field_name}: {description} ({field_type})")
            else:
                fields.append(f"- {field_name}: ({field_type})")
        
        return "\n".join(fields)

    @agent
    def schema_agent(self) -> Agent:
        """
        Create an agent for processing text into the target schema
        """
        return Agent(
            config=self.agents_config["schema_processor_agent"],
            tools=[],
            allow_delegation=False,
            verbose=True,
        )
    
    @task
    def schema_task(self) -> Task:
        """
        Create a task for the schema agent
        """
        return Task(
            config=self.tasks_config["process_text_task"],
            agent=self.schema_agent(),
            output_pydantic=self.target_model,
        )
    
    @crew
    def crew(self) -> Crew:
        """
        Create a crew for processing text into the target schema
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )   
    
    def run(self, input_data: str) -> T:
        """
        Run the crew with the provided input data
        
        Args:
            input_data: Dictionary containing the input data for the crew
        """
        # Create an instance of the crew
        crew_instance = self.crew()
        input = {'raw_text': input_data, 'schema': self.schema_description}
        # Run the crew with the input data
        result = crew_instance.kickoff(inputs=input)
        return result.pydantic
    