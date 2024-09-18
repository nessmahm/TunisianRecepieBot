from langchain_groq import ChatGroq
from langchain_experimental.agents.agent_toolkits import create_csv_agent
import json
from langchain_core.pydantic_v1 import BaseModel
from tavily import TavilyClient
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langchain_core.messages import SystemMessage, HumanMessage
import os
from prompts import  DOCUMENT_ANALYSIS_PROMPT,RESEARCH_PLAN_PROMPT,ROUNTING_NEXT_STEPT_PROMPT,HALLUCINATION_GRADER_PROMPT
from dotenv import load_dotenv
load_dotenv()

def WRITER_PROMPT(user_question,search_results):
  return f"You are a Tunisian recipe assistant tasked with providing a direct and well-formatted answer to the user's question. \
          I will provide you with the search results, and you need to formulate the response in a clear and concise manner.\
          Please use this information to generate a response to the user's question.\
          The user's question is: {user_question}\
          The search results : {search_results}\
          "

class AgentState(TypedDict):
    task: str
    draft: str
    content: List[str]
    sources: List[str]
    revision_number: int
    max_revisions: int
    hallucination_check : str

class Queries(BaseModel):
    queries: List[str]


# Initialize clients
tavily = TavilyClient(api_key=os.getenv("TAVILY_API"))
groq_api=os.getenv("GROQ_API")
llm = ChatGroq(temperature=0, model="llama3-70b-8192", api_key=groq_api)

def read_documents_from_folder(folder_path):
    documents = []
    sources = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):  # You can add other file types here
            with open(os.path.join(folder_path, filename), 'r') as file:
                documents.append(file.read())
                sources.append(filename)
    return documents, sources

def research_plan_node(state: AgentState):
    content = state.get('content', [])
    queries = llm.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_PLAN_PROMPT+content[0]),
        HumanMessage(content=state['task'])
    ])
    sources = state.get('sources', [])

    print("****",queries)
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        for r in response['results']:
            content.append(r['content'])
            if 'source' in r:
                sources.append(r['source'])
            else:
                sources.append('Unknown source')
    return {"content": content, "sources": sources}

def document_analysis_node(state: AgentState):
    # Path to the folder containing company documents
    folder_path="/content/drive/MyDrive/TunisianKitchenLLM"
    documents, sources = read_documents_from_folder(folder_path)
    content = state.get('content', [])
    # Process each document using the model
    for document in documents:
        sections = document.split("\n\n")  # Example splitting by double newline
        for section in sections:
            messages = [
                SystemMessage(content=DOCUMENT_ANALYSIS_PROMPT+state['task']),
                HumanMessage(content=section)
            ]
            response = llm.invoke(messages)
            content.append(response.content)
    # Combine sources from document analysis
    all_sources = state.get('sources', [])
    all_sources.extend(sources)

    return {"content": content, "sources": all_sources}
def agent_for_document_analysis_node(state: AgentState):
    content = state.get('content', [])
    csv_file_path="./translated_tunisian_recepies.csv"
    agent = create_csv_agent(llm, csv_file_path, verbose=False, allow_dangerous_code=True)
    agent_response = agent.invoke(DOCUMENT_ANALYSIS_PROMPT+state['task'])
    content.append(agent_response['output'])
    all_sources = state.get('sources', [])
    all_sources.append("csv_tunisian_recepies")
    return {"content": content, "sources": all_sources}

def generation_node(state: AgentState):
    content = "\n\n".join(state.get('content', []) )
    sources = "\n".join( state.get('sources', []))
    user_message = HumanMessage(
        content=f"{state['task']}")
    messages = [
        SystemMessage(
            content=WRITER_PROMPT(user_question=state["task"],search_results=content)
        ),
        user_message
    ]
    response = llm.invoke(messages)
    return {
        "draft": response.content,
        "revision_number": state.get("revision_number", 1) + 1
    }
def hallucination_grader_node(state):
    content = "\n\n".join(state.get('content', []) )
    generated_response = state.get('draft', "")
    # Construct the hallucination grader prompt
    messages = [
        SystemMessage(content=HALLUCINATION_GRADER_PROMPT.format(
            search_results=content,
            generated_response=generated_response
        )),
        HumanMessage(content="Does the response contain hallucinations?")
    ]

    # Invoke the model to assess for hallucinations
    response = llm.invoke(messages)
    if 'hallucination_found' in response.content:
        return {"hallucination_check": "hallucination_found"}
    else:
        return {"hallucination_check": "no_hallucination"}

def should_continue(state):
    if state["revision_number"] > state["max_revisions"]:
        return END
    return "hallucination_grader"

def decide_next_step(state):
  content = state.get('content', [])
  messages = [
        SystemMessage(content=ROUNTING_NEXT_STEPT_PROMPT+content[0]),
        HumanMessage(content=state['task'])
    ]
  response = llm.invoke(messages)
  response_content = response.content if hasattr(response, 'content') else ""
  if response_content == 'answer_found':
        return "generate"
  else:
        return "research_plan"

def decide_next_step_after_grading(state):
    if state.get('hallucination_check') == 'no_hallucination':
        return "generate"
    else:
        return "research_plan"

def build_model_graph():
    builder = StateGraph(AgentState)
    builder.add_node("generate", generation_node)
    builder.add_node("research_plan", research_plan_node)
    builder.add_node("document_analysis", agent_for_document_analysis_node)
    builder.add_node("hallucination_grader", hallucination_grader_node)
    builder.set_entry_point("document_analysis")

    builder.add_conditional_edges(
        "document_analysis",
        decide_next_step,
        {
            "generate": "generate",
            "research_plan": "research_plan"
        }
    )

    builder.add_conditional_edges(
        "generate",
        should_continue,
        {END: END,
         "hallucination_grader": "hallucination_grader"}
    )
    builder.add_conditional_edges(
        "hallucination_grader",
        decide_next_step_after_grading,
        {
            "generate": "generate",
            "research_plan": "research_plan"
        }
    )
    builder.add_edge("research_plan", "generate")
    # builder.add_edge("reflect", "generate")
    graph = builder.compile()
    return graph
def ask_the_bot(task):
  graph = build_model_graph()
  thread = {"configurable": {"thread_id": "1"}}
  for s in graph.stream({
      'task':task,
      "max_revisions": 3,
      "revision_number": 1,
  }, thread):
      print(s)

  s_json = json.dumps(s)
  data = json.loads(s_json)
  draft_text = data['generate']['draft']
  return draft_text
