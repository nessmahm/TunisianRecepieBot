import logging

from langchain_groq import ChatGroq
from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()
from recepieModelFunctions import build_model_graph
import json

# Initialize clients

def define_model():
    global tavily
    global llm
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API"))
    groq_api = os.getenv("GROQ_API")
    llm = ChatGroq(temperature=0, model="llama3-70b-8192", api_key=groq_api)
def ask_the_bot(task):
  logging.info(f"Received task: {task}")
  define_model()
  graph = build_model_graph(llm,tavily)
  thread = {"configurable": {"thread_id": "1"},"recursion_limit": 50}
  for s in graph.stream({
      'task': task,
      "max_revisions": 3,
      "revision_number": 1,
  }, thread):
      print(s)

  s_json = json.dumps(s)
  data = json.loads(s_json)
  draft_text = data['relevance_filter']['filtered_draft']
  start_marker = "The final response is:"
  start_index = draft_text.find(start_marker)

  if start_index != -1:
      filtered_message = draft_text[start_index + len(start_marker):].strip()
      return filtered_message.replace("**", "")
  else:
      return "Could you please clarify your question or provide more context about what you're looking for?"
