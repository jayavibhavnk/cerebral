import streamlit as st

# st.title("RAG Workflow Chatbot")
# st.write("This app runs a Retrieval-Augmented Generation workflow.")
# inp = st.text_input("Enter your query:")
from llama_index.utils.workflow import draw_all_possible_flows
import asyncio
from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Workflow,
    step,
    Event,
    Context,
)
import requests
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
)

from datasets import Dataset

import requests
import json

# API configuration
url = "https://llm.kindo.ai/v1/chat/completions"
api_key = "0e6746d7-fcb2-4bda-8f08-f489a3d95ec1-fa56966810a02357"
model_name = "azure/gpt-4o"

headers = {
    "api-key": api_key,
    "content-type": "application/json"
}

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# # Define custom events for each step in the workflow
class QueryEvent(Event):
    prompt: str

class RetrieveEvent(Event):
    retrieved_data: str

class GenerateResponseEvent(Event):
    response: str

class EvaluateResponseEvent(Event):
    scores: dict

class ProgressEvent(Event):
    msg: str

# Define the RAG Workflow class
class RAGWorkflow(Workflow):

    @step
    async def step_one(self, ctx: Context, ev: StartEvent) -> QueryEvent:
        ctx.write_event_to_stream(ProgressEvent(msg="Starting RAG workflow..."))
        prompt = ev.first_input
        return QueryEvent(prompt=prompt, directory = ev.directory)

    @step
    async def step_two(self, ctx: Context, ev: QueryEvent) -> RetrieveEvent:
        ctx.write_event_to_stream(ProgressEvent(msg="Retrieving relevant documents..."))
        # Load documents and create an index
        documents = SimpleDirectoryReader(ev.directory).load_data()
        index = VectorStoreIndex.from_documents(documents)
        
        # Perform a query on the index
        query_engine = index.as_query_engine()
        retrieved_data = query_engine.retrieve(ev.prompt)
        retrieved_data = [i.node.get_text() for i in retrieved_data]
        retrieved_data = "\n".join(retrieved_data)
        
        # ctx.write_event_to_stream(ProgressEvent(msg=f"Retrieved Data: {retrieved_data}"))
        return RetrieveEvent(retrieved_data=retrieved_data, prompt=ev.prompt)

    @step
    async def step_three(self, ctx: Context, ev: RetrieveEvent) -> GenerateResponseEvent:
        ctx.write_event_to_stream(ProgressEvent(msg="Generating response using LLM..."))
        data = {
            "model": "claude-3-haiku-20240307",
            "messages": [
                {"role": "user", "content": ev.retrieved_data + ev.prompt}
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        response_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No content returned")
        
        ctx.write_event_to_stream(ProgressEvent(msg=f"Generated Response: {response_text}"))
        return GenerateResponseEvent(response=response_text, prompt=ev.prompt, retrieved_data=ev.retrieved_data)

    @step
    async def step_four(self, ctx: Context, ev: GenerateResponseEvent) -> EvaluateResponseEvent:
        ctx.write_event_to_stream(ProgressEvent(msg="Evaluating response..."))

        # Prepare dataset for evaluation
        dataset = {
            'question': [ev.prompt],
            'answer': [ev.response],
            'contexts': [[ev.retrieved_data]]
        }
        
        dataset = Dataset.from_dict(dataset)

        # Evaluate using Ragas
        scores = evaluate(
            dataset=dataset,
            metrics=[
                faithfulness,
                answer_relevancy
            ]
        )
        
        ctx.write_event_to_stream(ProgressEvent(msg=f"Evaluation Scores: {scores}"))
        
        return EvaluateResponseEvent(scores=scores, prompt=ev.prompt, retrieved_data=ev.retrieved_data, ans=ev.response)

    @step
    async def step_five(self, ctx: Context, ev: EvaluateResponseEvent) -> StopEvent | GenerateResponseEvent:
        # Define thresholds for faithfulness and answer relevancy
        faithfulness_threshold = 0.8
        answer_relevancy_threshold = 0.6

        # Check if scores are satisfactory and decide whether to regenerate
        if ev.scores['faithfulness'] < faithfulness_threshold or ev.scores['answer_relevancy'] < answer_relevancy_threshold:
            ctx.write_event_to_stream(ProgressEvent(msg="Scores unsatisfactory. Regenerating response with improved prompt..."))

            # Provide feedback to LLM about what needs improvement
            feedback_prompt = (
                f"The previous response was not satisfactory. "
                f"Faithfulness score was {ev.scores['faithfulness']} (threshold: {faithfulness_threshold}), "
                f"and answer relevancy score was {ev.scores['answer_relevancy']} (threshold: {answer_relevancy_threshold}). "
                f"Please generate a more accurate and relevant response based on the provided context."
            )

            # Regenerate response with feedback
            data = {
                "model": "claude-3-haiku-20240307",
                "messages": [
                    {"role": "user", "content": feedback_prompt + "\n" + ev.retrieved_data}
                ]
            }
            response = requests.post(url, headers=headers, json=data)
            response_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No content returned")

            return await self.step_three(ctx, RetrieveEvent(retrieved_data=response_text))
        
        else:
            ctx.write_event_to_stream(ProgressEvent(msg="Output is acceptable. Completing workflow."))
            return StopEvent(result=[ev.ans, ev.scores])

async def main(input_text="Start the RAG workflow.", directory="data"):
    w = RAGWorkflow(timeout=60, verbose=True)
    handler = w.run(first_input=input_text, directory=directory)
    
    async for ev in handler.stream_events():
        if isinstance(ev, ProgressEvent):
            with st.expander(f"Agent Thinking 🤖 {ev.msg}", expanded=False):
                st.info(ev.msg)
    
    final_result, eval = await handler
    st.success("Final result:")
    st.text(final_result)

    draw_all_possible_flows(RAGWorkflow, filename="rag_workflow_new.html")
    
# Streamlit App Code

def run_workflow(inp):
    asyncio.run(main(inp, directory="data"))



st.title("RAG Workflow Chatbot")
st.write("This app runs a Retrieval-Augmented Generation workflow.")

st.sidebar.header("Customization Options")

show_workflow_diagram = st.sidebar.checkbox("Show Workflow Diagram", value=True)
show_retrieval_results = st.sidebar.checkbox("Show Retrieved Documents", value=False)

max_iterations = st.sidebar.number_input("Max Regeneration Attempts", min_value=1, max_value=10, value=3)

faithfulness_threshold = st.sidebar.slider("Faithfulness Threshold", 0.0, 1.0, 0.8, 0.1)
answer_relevancy_threshold = st.sidebar.slider("Answer Relevancy Threshold", 0.0, 1.0, 0.6, 0.1)

with st.sidebar.expander("Advanced Settings"):
    chunk_size = st.number_input("Document Chunk Size", min_value=100, max_value=1000, value=500)
    overlap = st.number_input("Chunk Overlap", min_value=0, max_value=100, value=50)

models = [
        "Claude 3.5 Sonnet (claude-3-5-sonnet-20240620)",
        "Claude 3 Haiku (claude-3-haiku-20240307)",
        "Claude 3 Opus (claude-3-opus-20240229)",
        "Claude 3 Sonnet (claude-3-sonnet-20240229)",
        "Command R (command-r)",
        "DeepSeek Coder 33B (deepseek-ai/deepseek-coder-33b-instruct)",
        "Gemini 1.5 Flash (gemini-1.5-flash)",
        "Gemini 1.5 Pro (gemini-1.5-pro)",
        "GPT-3.5 Turbo (azure/gpt-35-turbo-0125)",
        "GPT-4o (azure/gpt-4o)",
        "GPT-4o mini (azure/gpt-4o-mini)",
        "GPT-4 Turbo (azure/gpt-4-turbo)",
        "Granite 13B Chat v2 (watsonx/ibm/granite-13b-chat-v2)",
        "Llama 3.1 70B (groq/llama-3.1-70b-versatile)",
        "Llama 3 70B (groq/llama3-70b-8192)",
        "Mixtral (groq/mixtral-8x7b-32768)",
        "Qwen 2 72B Instruct (qwen/qwen2-72b-instruct)",
        "Saul Instruct V1 (huggingface/Saul-Instruct-v1)",
        "WhiteRabbitNeo 2.5 32B (Beta) (/models/WhiteRabbitNeo-33B-DeepSeekCoder)",
        "WhiteRabbitNeo 33B v1.7 (/models/WhiteRabbitNeo-33B-DeepSeekCoder)"
    ]

selected_model = st.sidebar.selectbox(
        "Choose a model",models)

UPLOAD_DIRECTORY = "data"

# Create the directory if it doesn't exist
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Streamlit file uploader
uploaded_file = st.file_uploader("Upload a file")

if uploaded_file is not None:
    # Get the file name
    file_name = uploaded_file.name
    # Full file path
    file_path = os.path.join(UPLOAD_DIRECTORY, file_name)

    # Check if the file already exists in the directory
    if os.path.exists(file_path):
        st.warning(f"File '{file_name}' already exists in the '{UPLOAD_DIRECTORY}' directory.")
    else:
        # Save the uploaded file to the directory
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File '{file_name}' has been uploaded and saved to '{UPLOAD_DIRECTORY}'.")


inp = st.text_input("Enter your query:")

if st.button('Run Workflow'):
    with st.spinner('Running workflow...'):
        run_workflow(inp)
    
    with open('rag_workflow_new.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    st.components.v1.html(html_content, height=800, scrolling=True)

