import sys
from crewai_plus_lead_scoring.crew import CrewaiPlusLeadScoringCrew
from crewai import LLM


def run(inputs):
    # Replace with your inputs, it will automatically interpolate any tasks and agents information
    # inputs= {
    #     "company": "IBM",
    #     "product_name": "IBM Watson",
    #     "product_description": "IBM Watson is a cognitive computing platform that uses natural language processing, machine learning, and deep learning to analyze vast amounts of data and answer questions in a way that mimics human understanding",
    #     "icp_description": "The ideal customer for IBM Watson is a mid-sized to large enterprise in industries such as healthcare, finance, retail, manufacturing, or government, seeking AI-powered solutions to enhance decision-making, automate workflows, and drive innovation. These organizations often face challenges in managing vast amounts of data, optimizing customer interactions, and implementing predictive analytics. Key decision-makers include CIOs, CTOs, data scientists, and business analysts who require advanced AI, natural language processing, and machine learning capabilities to improve operational efficiency and customer experiences. IBM Watson is best suited for tech-driven, data-heavy businesses looking for scalable and intelligent automation solutions on a global scale.",
    #     "form_response": [
    #         {
    #             "question": "Give a score for your experince?",
    #             "answer":"9/10, very satisfied"
    #         }
    #     ],
    # }
    model = LLM(model="ollama/llama3.2:latest", base_url="http://localhost:11434")

    result = CrewaiPlusLeadScoringCrew(model=model).crew().kickoff(inputs=inputs)
    
    # CrewaiPlusLeadScoringCrew().crew().train(inputs=inputs)
        

    # except Exception as e:
    #     raise Exception(f"An error occurred while training the crew: {e}")
    
    # CrewaiPlusLeadScoringCrew().crew().replay(task_id=sys.argv[1])

    # except Exception as e:
    #     raise Exception(f"An error occurred while replaying the crew: {e}")

    # CrewaiPlusLeadScoringCrew().crew().test(n_iterations=int(1), eval_llm='gpt-3.5-turbo', inputs=inputs)


    return result

    # except Exception as e:
    #     raise Exception(f"An error occurred while replaying the crew: {e}")


# def train():
#     """
#     Train the crew for a given number of iterations.
#     """
#     inputs = {
#         "company": "IBM",
#         "product_name": "IBM Watson",
#         "product_description": "IBM Watson is a cognitive computing platform that uses natural language processing, machine learning, and deep learning to analyze vast amounts of data and answer questions in a way that mimics human understanding",
#         "icp_description": "The ideal customer for IBM Watson is a mid-sized to large enterprise in industries such as healthcare, finance, retail, manufacturing, or government, seeking AI-powered solutions to enhance decision-making, automate workflows, and drive innovation. These organizations often face challenges in managing vast amounts of data, optimizing customer interactions, and implementing predictive analytics. Key decision-makers include CIOs, CTOs, data scientists, and business analysts who require advanced AI, natural language processing, and machine learning capabilities to improve operational efficiency and customer experiences. IBM Watson is best suited for tech-driven, data-heavy businesses looking for scalable and intelligent automation solutions on a global scale.",
#         "form_response": [
#             {
#                 'question': "Give a score for your experince?",
#                 'answer':'9/10, very satisfied'
#             }
#         ]
#     }
#     try:
#         CrewaiPlusLeadScoringCrew().crew().train(
#             n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
#         )

#     except Exception as e:
#         raise Exception(f"An error occurred while training the crew: {e}")


# def replay():
#     """
#     Replay the crew execution from a specific task.
#     """
#     try:
#         CrewaiPlusLeadScoringCrew().crew().replay(task_id=sys.argv[1])

#     except Exception as e:
#         raise Exception(f"An error occurred while replaying the crew: {e}")


# def test():
#     """
#     Test the crew execution and returns the results.
#     """
#     inputs = {
#         "company": "IBM",
#         "product_name": "IBM Watson",
#         "product_description": "IBM Watson is a cognitive computing platform that uses natural language processing, machine learning, and deep learning to analyze vast amounts of data and answer questions in a way that mimics human understanding",
#         "icp_description": "The ideal customer for IBM Watson is a mid-sized to large enterprise in industries such as healthcare, finance, retail, manufacturing, or government, seeking AI-powered solutions to enhance decision-making, automate workflows, and drive innovation. These organizations often face challenges in managing vast amounts of data, optimizing customer interactions, and implementing predictive analytics. Key decision-makers include CIOs, CTOs, data scientists, and business analysts who require advanced AI, natural language processing, and machine learning capabilities to improve operational efficiency and customer experiences. IBM Watson is best suited for tech-driven, data-heavy businesses looking for scalable and intelligent automation solutions on a global scale.",
#         "form_response": [
#             {
#                 'question': "Give a score for your experince?",
#                 'answer':'9/10, very satisfied'
#             }
#         ]
#     }
#     try:
#         CrewaiPlusLeadScoringCrew().crew().test(
#             n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs
#         )

#     except Exception as e:
#         raise Exception(f"An error occurred while replaying the crew: {e}")
