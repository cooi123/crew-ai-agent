from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeWebsiteTool, SerperDevTool

# Define the expected JSON structure for the email task output
class EmailOutput(BaseModel):
    subject: str = Field(..., description="The email subject line")
    body: str = Field(..., description="The body of the outreach email")

# Define the final formatted email output
class FinalEmailOutput(BaseModel):
    subject: str = Field(..., description="Formatted subject line of the email")
    body: str = Field(..., description="Formatted body of the outreach email")


@CrewBase
class CustomerOutreachCrew:
    """Customer Outreach Crew using CRM Lead Info"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def customer_analysis_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["customer_analysis_agent"],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def pitch_email_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["pitch_email_agent"],
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def email_formatter_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["email_formatter_agent"],
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @task
    def customer_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["customer_analysis_task"],
            agent=self.customer_analysis_agent(),
        )

    @task
    def pitch_email_task(self) -> Task:
        return Task(
            config=self.tasks_config["pitch_email_task"],
            agent=self.pitch_email_agent(),
            output_json=EmailOutput,  # Defines output as JSON with subject and body
        )

    @task
    def email_formatting_task(self) -> Task:
        return Task(
            config=self.tasks_config["email_formatting_task"],
            agent=self.email_formatter_agent(),
            output_json=FinalEmailOutput,  # Defines output as the final formatted email
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