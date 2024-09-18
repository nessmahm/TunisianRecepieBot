
RESEARCH_PLAN_PROMPT = """
You are a culinary researcher tasked with providing information for writing a Tunisian recipe.
Generate a list of search queries to gather any relevant information about the requested dish or its traditional preparation.
Limit to 3 queries.
"""

DOCUMENT_ANALYSIS_PROMPT = """You are a recipe assistant tasked with extracting relevant information from the provided documents that containes tunisian recepies related to user question.\
This document containes a list of tunisian recepieces , its ingerediants and it's steps.\
Extract and list any details about the user question. \
Ensure that you include only relevant details to help answer the user question.\
This document containes a list of tunisian recepieces , its ingerediants and it's steps.\ i want you to read it and answer the user question
the user's question is : """


ROUNTING_NEXT_STEPT_PROMPT = """System You are an expert at determining the next step in a workflow based on the document analysis results.\
If the document search result contains a valid answer to the user's question, return answer_found.\
If the document search resultdoes not provide a sufficient answer, to continue with the 'research_plan' step to gather more information return not_found.\
you should reply with answer_found or not_found words.
This is the Document search result:
"""
HALLUCINATION_GRADER_PROMPT = """
You are tasked with reviewing the generated response for accuracy. Based on the search results and document analysis provided, evaluate if the generated response contains any hallucinations (fabricated or unsupported information).

Search results and documents:
{search_results}

Generated response:
{generated_response}

Does the response contain any hallucinations? Respond with 'no_hallucination' if everything is correct, otherwise specify 'hallucination_found' and explain the issues briefly.
"""
