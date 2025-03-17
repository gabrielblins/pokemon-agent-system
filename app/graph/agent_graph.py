from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph
import os
import json
from dotenv import load_dotenv
from app.agents.supervisor import SUPERVISOR_PROMPT, SUPERVISOR_TOOLS
from app.agents.researcher import RESEARCHER_PROMPT, RESEARCHER_TOOLS
from app.agents.pokemon_expert import EXPERT_PROMPT, EXPERT_TOOLS
from app.agents.visualizer import VISUALIZER_PROMPT, VISUALIZER_TOOLS
from langchain.globals import set_verbose, set_debug
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langsmith import traceable


# Load environment variables
load_dotenv()

if os.getenv("DEBUG", "false").lower() == "true":
    set_verbose(True)
    set_debug(True)


def create_agent_graph(
    model_provider: str = "openai", model_name: str = "gpt-4o-mini"
) -> StateGraph:
    """
    Create the agent graph

    Args:
        model_name: Name of the LLM model to use

    Returns:
        Configured CompiledStateGraph
    """

    if model_provider == "openai":
        llm = ChatOpenAI(
            model=model_name,
            temperature=0.1 if not model_name.startswith("o") else None,
            verbose=True,
        )

    elif model_provider == "groq":
        llm = ChatGroq(model=model_name, temperature=0.2, verbose=True)

    researcher = create_react_agent(
        model=llm, tools=RESEARCHER_TOOLS, name="researcher", prompt=RESEARCHER_PROMPT
    )
    expert = create_react_agent(
        model=llm, tools=EXPERT_TOOLS, name="expert", prompt=EXPERT_PROMPT
    )
    visualizer = create_react_agent(
        model=llm, tools=VISUALIZER_TOOLS, name="visualizer", prompt=VISUALIZER_PROMPT
    )

    workflow = create_supervisor(
        agents=[researcher, expert, visualizer],
        model=llm,
        prompt=SUPERVISOR_PROMPT,
        tools=SUPERVISOR_TOOLS,
    )

    return workflow.compile()


@traceable
def process_question(question: str) -> Dict[str, Any]:
    """
    Process a question through the agent graph

    Args:
        question: User's question

    Returns:
        Final response
    """

    provider = os.getenv("MODEL_PROVIDER", "openai")
    model_name = os.getenv("MODEL_NAME", "o3-mini")

    graph = create_agent_graph(model_provider=provider, model_name=model_name)

    initial_state = {"messages": [("user", question)]}

    state = graph.invoke(initial_state)

    try:
        response = state["messages"][-1].content
    except AttributeError:
        if isinstance(state["messages"][-1], str):
            response = state["messages"][-1]
        elif isinstance(state["messages"][-1], tuple):
            response = state["messages"][-1][1]
        else:
            response = {"error": "Unexpected message format"}

    if isinstance(response, str):
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]

        response = response.strip()
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            response = {"error": "Invalid JSON response"}

    return response


if __name__ == "__main__":
    # Example usage
    question = "Who would win in a battle, will be Pikachu or Charizard?"
    # question = "explain me the stats of Pikachu"
    # question = "What is the best counter for Charizard?"
    response = process_question(question)
    print(response)
