from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
# from crewai_tools import RagTool
from src.agent_tools.astra_db_ragging_tool import AstradbVectorSearchTool



@CrewBase
class DocumentSummariserCrew():
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, document_url):
        # self.rag_tool = RagTool()
        # self.rag_tool.add(data_type="web_page",url=document_url)
        self.astra_rag_tool = AstradbVectorSearchTool( collection_name="document_summariser")
 
    @agent
    def summariser_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["document_summariser_agent"],
            tools=[],
            allow_delegation=False,
            verbose=True,
        )
    
    @task
    def summariser_task(self) -> Task:
        """
        Create a task for the schema agent
        """
        return Task(
            config=self.tasks_config["process_text_task"],
            agent=self.summariser_agent(),
            tools= [self.astra_rag_tool],
        )
    
    @crew
    def crew(self) -> Crew:
        """

        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )   
    
    