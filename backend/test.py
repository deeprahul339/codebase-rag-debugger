


from src.agent.agent import run_agent



repo_id = "github-com-deeprahul339-react-a11y-assignment"
user_question="What will be impacted if I remove handleCalculate?",
for event in run_agent(repo_id, user_question):
    print(event)


