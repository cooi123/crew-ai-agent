from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeWebsiteTool, SerperDevTool



# Define the final formatted email output
class PrimerOutpout(BaseModel):
    subject: str = Field(..., description="Formatted primer text")
    body: str = Field(..., description="Formatted body of the primer")


@CrewBase
class PrimerCrew:
    """Primer Making team"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def topic_researcher_writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["topic_researcher_writer_agent"],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
            allow_delegation=False,
            verbose=True,
        )

    

    @task
    def primer_analyst_task(self) -> Task:
        return Task(
            config=self.tasks_config["primer_analyst_task"],
            agent=self.topic_researcher_writer_agent(),
            output_json=PrimerOutpout,  # Defines output as JSON

        )



    @crew
    def crew(self) -> Crew:
        """Creates a crew to analyze leads and generate well-structured outreach emails"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Ensures sequential execution, linking task outputs to inputs
            verbose=True,
        )