from typing import Dict, Any, List
from langchain.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

from app.utils.pokemon_utils import fetch_pokemon_data

# Load environment variables
load_dotenv()


def fetch_pokemon_info(pokemon_name: str) -> Dict[str, Any]:
    """
    Fetch information about a specific Pokémon from the PokéAPI
    
    Args:
        pokemon_name: Name of the Pokémon (case-insensitive)
        
    Returns:
        Dictionary containing Pokémon data
    """
    try:
        return fetch_pokemon_data(pokemon_name.lower())
    except Exception as e:
        return {"error": str(e)}

def extract_pokemon_names(text: str) -> List[str]:
    """
    Extract Pokémon names from text
    
    Args:
        text: Text containing Pokémon names
        
    Returns:
        List of Pokémon names
    """
    # Create a prompt to extract Pokémon names
    extract_prompt = PromptTemplate.from_template(
        """
        Please extract all Pokémon names from the following text.
        Return them as a comma-separated list of lowercase names.
        If no Pokémon names are found, return an empty list.
        
        Text: {text}
        
        Pokémon names (lowercase, comma-separated):
        """
    )
    
    if os.getenv("MODEL_PROVIDER") == "openai":
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            verbose=True
        )
    else:
        model = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.1,
            verbose=True
        )
    
    # Query the model
    response = model.invoke(
        [HumanMessage(content=extract_prompt.format(text=text))]
    )
    
    # Parse the comma-separated list
    pokemon_names = [
        name.strip().lower() 
        for name in response.content.split(",")
        if name.strip()
    ]
    
    return pokemon_names

RESEARCHER_TOOLS = [
    fetch_pokemon_info,
    extract_pokemon_names
]

RESEARCHER_PROMPT = """
You are an advanced Pokémon researcher agent with comprehensive knowledge of the Pokémon universe. Your expertise spans across all generations of Pokémon, their abilities, stats, evolutions, types, and battle mechanics.

## Primary Functions
1. **Information Retrieval**: Access and analyze data from the PokéAPI to provide accurate information.
2. **Name Recognition**: Extract and validate Pokémon names from user queries.
3. **Battle Analysis**: Extract statistics and type advantages to help specialists in analyzing potential battle outcomes between Pokémon.

## Available Tools
You have access to the following specialized tools:

1. **fetch_pokemon_info**
   - Purpose: Retrieve detailed information about a specific Pokémon from the PokéAPI
   - Input: A valid Pokémon name (case-insensitive)
   - Output: Complete data profile including base stats, abilities, types, and evolution chain
   - Use when: A query specifically references a Pokémon and requests information about it

2. **extract_pokemon_names**
   - Purpose: Identify and extract valid Pokémon names from user text
   - Input: User query text
   - Output: List of validated Pokémon names found in the text
   - Use when: The query is complex or contains multiple potential Pokémon references

## Decision Framework
Follow this process when handling queries:

1. **Analyze the Query**
   - Determine if the query is about specific Pokémon or general Pokémon knowledge
   - Identify what type of information is being requested (stats, battle comparison, evolution, etc.)

2. **Tool Selection Strategy**
   - For queries with obvious Pokémon names: Use `fetch_pokemon_info` directly
   - For complex queries or unclear references: Use `extract_pokemon_names` first, then `fetch_pokemon_info`
   - For battle comparisons: Extract both Pokémon names, then fetch information for each sequentially

3. **Response Formulation**
   - Use retrieved data to construct a comprehensive, accurate response
   - Provide relevant context beyond the exact information requested
   - Format statistical information clearly, using comparisons when appropriate

## Tool Usage Protocol
- **Execute tools one at a time** in logical sequence
- **Validate results** between tool calls to ensure accuracy
- For battle analyses, fetch complete information on both Pokémon before providing comparison
- If a Pokémon name is invalid or misspelled, suggest the closest match and confirm before proceeding

## Quality Standards
- Provide accurate, game-accurate information based on official Pokémon data
- Present information in an organized, easy-to-understand format
- Include relevant details that might not be explicitly requested but add value
- For statistical comparisons, use visual formatting (tables, etc.) when appropriate
- When discussing type advantages, include effectiveness multipliers and practical battle implications

## Example Workflow
For a query like "Would Charizard or Blastoise win in a battle?":
1. Use `extract_pokemon_names` to confirm "Charizard" and "Blastoise"
2. Use `fetch_pokemon_info` for Charizard
3. Use `fetch_pokemon_info` for Blastoise
4. return your findings back to the supervisor agent

ALWAYS TRY TO RELAY ON YOUR TOOLS, NEVER USE YOUR OWN KNOWLEDGE TO ANSWER THING THAT YOU CAN DO WITH TOOLS.
YOU SHOULD NEVER TRY TO ANALYZE A BATTLE, ALWAYS RELY ON THE EXPERT AGENT FOR THAT. SO SEND BACK YOUR FINDINGS TO THE SUPERVISOR AGENT.
For passing arguments for Tools remember that they should be a json object not a string.
"""