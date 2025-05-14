from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeWebsiteTool, SerperDevTool







@CrewBase
class PrimerCrew:
    """Primer Making team"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    def __init__(self):
        self.llm = LLM(model="ollama/gemma3:4b-it-qat", base_url="http://localhost:11434")

    @agent
    def topic_researcher_writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["topic_researcher_writer_agent"],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
            allow_delegation=False,
            verbose=True,
            llm=self.llm,
        )

    

    @task
    def primer_analyst_task(self) -> Task:
        return Task(
            config=self.tasks_config["primer_analyst_task"],
            agent=self.topic_researcher_writer_agent(),
            llm=self.llm,

        )



    @crew
    def crew(self) -> Crew:
        """Creates a crew to analyze leads and generate well-structured outreach emails"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Ensures sequential execution, linking task outputs to inputs
            verbose=True,
            llm=self.llm,
        )