
import streamlit as st

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

def prompt_safe(input):
  safety_guidelines = """
    Please analyze the following prompt and classify whether it is safe or not. A safe prompt:
    - Does not contain offensive, harmful, or illegal content.
    - Does not encourage or ask for any dangerous activities.
    - Is aligned with ethical guidelines and does not involve discriminatory or harmful speech.

    just respond in json format in one line string:
    {
      safety: "safe or unsafe"
    }
    """

    # Combine the safety guidelines with the user's prompt
  full_prompt = safety_guidelines + "\n\nPrompt to check: " + input

    # Send the request to the LLM
  data = {
      "model": model_name,
      "messages": [
          {"role": "user", "content": full_prompt}
      ]
  }

  response = requests.post(url, headers=headers, json=data)

  # Extract and return the classification (safe or unsafe) from the response
  output = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No content returned")

  # Check if the model flagged it as safe or unsafe
  return output

def prompt_upgrader(prompt):
    # Define the system message to instruct the assistant
    system_message = """
            "You are an assistant that helps improve user prompts to get better results from an AI language model. "
            "Your goal is to rephrase and enhance the user's prompt to make it clearer, more detailed, and more likely "
            "to produce a high-quality response. Provide the upgraded prompt without changing the original intent."
            "don't go into specifics of a topic, keep it general"
            return the message in json format in a single line:
            {
              "upgraded_prompt": "..."
            }
    """

    prompt = system_message + "Input prompt: " +prompt

    data = {
      "model": model_name,
      "messages": [
          {"role": "user", "content": prompt}
      ]
    }
    response = requests.post(url, headers=headers, json=data)

  # Extract and return the classification (safe or unsafe) from the response
    upgraded_prompt = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No content returned")

  # Check if the model flagged it as safe or unsafe


    return upgraded_prompt
def bias_check(query):
    # Define the base prompt for detecting bias
    base_guidelines = """
    Please analyze the following text for any bias. Annotate biased sections and explain why they are biased.
    Additionally, provide an overall bias percentage based on the biased content relative to the total content.
    Your response should be in a structured format like a JSON file, use a single line string do not make it a multiline comment, specifying:
    {
      "bias_percentage" = "0-100",
      "reasons" = [
        {
          annotated_text = "..."
          reason for it = "..."
          }
      ]
    }
    """

    # Combine the base guidelines with the user's query
    prompt = base_guidelines + " Input text: " + query

    data = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
                ]
            }

    response = requests.post(url, headers=headers, json=data)
    response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No content returned")
    return response

def hallucination_check(query):
    # Define the base prompt for detecting hallucinations
    base_guidelines = """
    Please analyze the following text for any hallucinations. Hallucinations are defined as:
    - Factuality hallucinations: Generated content that is factually incorrect or fabricated.
    - Faithfulness hallucinations: Output that deviates from the context of the input text.

    Annotate the hallucinated sections and provide explanations for why they are hallucinations.
    Additionally, calculate the hallucination percentage relative to the total content.
    Your response should be in a structured JSON format, use a single line string, specifying:
    {
      "hallucination_percentage": "0-100",
      "hallucinations": [
        {
          "annotated_text": "...",
          "reason_for_hallucination": "..."
        }
      ]
    }
    """

    # Combine the base guidelines with the user's query
    prompt = base_guidelines + " Input text: " + query

    data = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
                ]
            }
    response = requests.post(url, headers=headers, json=data)
    response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No content returned")
    return response

from langchain.evaluation import load_evaluator
from langchain.evaluation import EvaluatorType

def l_evaluator(query, output):
    results = {}

    # Define custom criteria as a dictionary
    custom_criterion = {
        "Correctness": "Is the output correct?",
        # "Coherence": "Is the output coherent?",
        "Helpfulness": "Is the output helpful?",
        # "Harmfulness": "Is the output harmful?",
        "Maliciousness": "Is the output malicious?",
        # "Accuracy": "Is the output accurate?",
        "Safe": "Is the output safe?"
    }

    # Iterate over each criterion and evaluate
    for criterion_name, criterion_description in custom_criterion.items():
        eval_chain = load_evaluator(
            EvaluatorType.CRITERIA,
            criteria={criterion_name: criterion_description},
        )

        eval_result = eval_chain.evaluate_strings(prediction=output, input=query)
        
        # Store results using criterion name as key
        results[criterion_name] = {
            'value': eval_result['value'],
            'score': eval_result['score'],
            # 'reasoning': eval_result['reasoning']
        }

    return results 


from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Workflow,
    step,
    Event,
    Context,
)
import asyncio
from llama_index.llms.openai import OpenAI
from llama_index.utils.workflow import draw_all_possible_flows

# Define custom events for each step in the workflow
class PromptInjectionCheckEvent(Event):
    pass

class PromptEngineeringEvent(Event):
    engineered_prompt: str

class GenerateOutputEvent(Event):
    output: str

class BiasHallucinationCheckEvent(Event):
    is_biased: str
    is_hallucinated: str

class ProgressEvent(Event):
    msg: str

class OnlineSearchEvent(Event):
    engineered_prompt: str

import requests

use_online_search = True

class AIGovernanceWorkflow(Workflow):
    engineered_prompt = ""

    @step
    async def step_one(self, ctx: Context, ev: StartEvent) -> PromptInjectionCheckEvent | StopEvent:
        ctx.write_event_to_stream(ProgressEvent(msg="Checking for prompt injection..."))
        print(ev.first_input)
        # print(prompt_safe("what is the capital of france"))
        input1 = ev.first_input
        safety_result = json.loads(prompt_safe(ev.first_input))
        print(safety_result)
        if safety_result.get('safety') != 'safe':
            ctx.write_event_to_stream(ProgressEvent(msg="Input is unsafe. Stopping workflow."))
            return StopEvent(result="Input is unsafe.")
        else:
            ctx.write_event_to_stream(ProgressEvent(msg="Input is safe. Proceeding to prompt engineering."))
            return PromptInjectionCheckEvent(first_output = input1)
    
    @step
    async def step_two(self, ctx: Context, ev: PromptInjectionCheckEvent) -> PromptEngineeringEvent:
        ctx.write_event_to_stream(ProgressEvent(msg="Performing prompt engineering..."))
        engineered_prompt = prompt_upgrader(ev.first_output)
        ctx.write_event_to_stream(ProgressEvent(msg=f"Engineered Prompt: {engineered_prompt}"))
        return PromptEngineeringEvent(engineered_prompt=engineered_prompt)
    
    @step
    async def step_three(self, ctx: Context, ev: PromptEngineeringEvent) -> OnlineSearchEvent:
        ctx.write_event_to_stream(ProgressEvent(msg="Generating output using LLM..."))
        data = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": ev.engineered_prompt}
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        response_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No content returned")
        ctx.write_event_to_stream(ProgressEvent(msg=f"Generated Output: {response_text}"))
        engineered_prompt = ev.engineered_prompt
        return GenerateOutputEvent(output=response_text, engineered_prompt = engineered_prompt)

    @step
    async def optional_duckduckgo_step(self, ctx: Context, ev: OnlineSearchEvent) -> GenerateOutputEvent:

        updated_prompt = ev.engineered_prompt
        
        if use_online_search == True:

            ctx.write_event_to_stream(ProgressEvent(msg="Performing Online search..."))
        
            # Perform DuckDuckGo search and append results to the prompt
            search_results = duckduckgo_search(ev.engineered_prompt)
            search_text = "\n".join([f"{result['title']}: {result['body']}" for result in search_results])
            
            updated_prompt = f"{ev.engineered_prompt}\n\nAdditional Information:\n{search_text}"
            
            ctx.write_event_to_stream(ProgressEvent(msg=f"Updated Prompt with Search Results: {updated_prompt}"))
        
        return PromptEngineeringEvent(engineered_prompt=updated_prompt)

    @step
    async def step_four(self, ctx: Context, ev: GenerateOutputEvent) -> BiasHallucinationCheckEvent:
        ctx.write_event_to_stream(ProgressEvent(msg="Checking for bias and hallucination..."))
        # Implement bias and hallucination check logic here
        bias_json = bias_check(ev.output)
        hallucination_json = hallucination_check(ev.output)
        # For demonstration, assume no bias or hallucination detected
        # bias_json = bias_json[bias_json.find("{"):bias_json.rfind("}")+1]
        # hallucination_json = hallucination_json[hallucination_json.find("{"):hallucination_json.rfind("}")+1]
        # bias_json = json.loads(bias_json)
        # hallucination_json = json.loads(hallucination_json)

        # bias_percentage = bias_json.get('bias_percentage', 0) 
        # hallucination_percentage = hallucination_json.get('hallucination_percentage', 0)
        #
        print(bias_json)
        print(hallucination_json)
        is_biased = False
        is_hallucinated = False
        engineered_prompt = ev.engineered_prompt
        return BiasHallucinationCheckEvent(is_biased=bias_json, is_hallucinated=hallucination_json, engineered_prompt = engineered_prompt, output = ev.output)
    
    @step
    async def step_five(self, ctx: Context, ev: BiasHallucinationCheckEvent) -> StopEvent | GenerateOutputEvent:
        b = ev.is_biased[ev.is_biased.find("{"):ev.is_biased.rfind("}")+1]
        h = ev.is_hallucinated[ev.is_hallucinated.find("{"):ev.is_hallucinated.rfind("}")+1]
        b = json.loads(b)
        h = json.loads(h)
        print(b)
        print(h)

        d = l_evaluator(ev.engineered_prompt, ev.output)
        t=f'"Evaluation Scores": {d}, "Bias": {b}, "Hallucination": {h}'
        
# Convert single quotes to double quotes for valid JSON
        # t = t.replace("'", '"')

        # Parse the string into a dictionary
        # data = json.loads("{" + t + "}")

        # Format the output
        # output = "Evaluation Scores:\n"
        # for key, value in data["Evaluation Scores"].items():
        #     output += f"{key}: {value['value']} (Score: {value['score']})\n"

        # output += "\nBias:\n"
        # output += f"Bias Percentage: {data['Bias']['bias_percentage']}%\n"
        # output += "Reasons:\n"
        # for i, reason in enumerate(data["Bias"]["reasons"], 1):
        #     output += f"{i}. Statement: \"{reason['annotated_text']}\"\n"
        #     output += f"   Reason: {reason['reason_for_it']}\n\n"

        # output += "Hallucination:\n"
        # output += f"Hallucination Percentage: {data['Hallucination']['hallucination_percentage']}%\n"
        # output += f"Hallucinations: {', '.join(data['Hallucination']['hallucinations']) if data['Hallucination']['hallucinations'] else 'None'}"

        # print(output)

        ctx.write_event_to_stream(ProgressEvent(msg=f"{t}"))

        if int(b.get('bias_percentage')) > 10 or int(h.get('hallucination_percentage')) > 10:
            ctx.write_event_to_stream(ProgressEvent(msg="Output is biased or hallucinated. Regenerating..."))

        # if ev.is_biased or ev.is_hallucinated:
        #     ctx.write_event_to_stream(ProgressEvent(msg="Output is biased or hallucinated. Regenerating..."))
            # Optionally adjust prompt or handle accordingly
            # For demonstration, we limit the number of retries
            if not hasattr(ctx, 'retry_count'):
                ctx.retry_count = 0
            ctx.retry_count += 1
            if ctx.retry_count > 2:
                ctx.write_event_to_stream(ProgressEvent(msg="Maximum retries reached. Stopping workflow."))
                return StopEvent(result="Failed to produce unbiased and factual output after retries.")
            else:
                # You may modify the prompt here if necessary
                return await self.step_three(ctx, PromptEngineeringEvent(engineered_prompt=ev.engineered_prompt+"your output is biased or hallucinated, please correct it" + str(b) + str(h)))
        else:
            ctx.write_event_to_stream(ProgressEvent(msg="Output is acceptable. Completing workflow."))
            return StopEvent(result=ev.output)


async def main(input_text="Start the AI governance workflow.", use_online_search = True):
    w = AIGovernanceWorkflow(timeout=60, verbose=True)
    handler = w.run(first_input=input_text, use_online_search = True)
    
    async for ev in handler.stream_events():
        if isinstance(ev, ProgressEvent):
            with st.expander(f"Agent Thinking 🤖 {ev.msg}", expanded=False):
                st.info(ev.msg)
    
    final_result = await handler
    print("Final result:", final_result)
    
    draw_all_possible_flows(AIGovernanceWorkflow, filename="ai_governance_workflow.html")

    st.success("Final result:")
    st.text(final_result)



def run_workflow(inp):
    asyncio.run(main(inp))


st.title("AI Governance Workflow")  
st.write("This AI governance workflow checks for prompt safety, engineers the prompt, generates an output, and evaluates it for bias and hallucination.")

# import streamlit as st

# Sidebar customization options
st.sidebar.header("Customization Options")

# Model selection
model_option = st.sidebar.selectbox(
    "Select Model",
    ["azure/gpt-4o", "azure/gpt-3.5-turbo", "claude-3-opus-20240229"]
)

# Safety threshold
safety_threshold = st.sidebar.slider(
    "Safety Threshold",
    min_value=0,
    max_value=100,
    value=80,
    help="Set the safety threshold for prompt injection check"
)

# Bias threshold
bias_threshold = st.sidebar.slider(
    "Bias Threshold",
    min_value=0,
    max_value=100,
    value=10,
    help="Set the threshold for acceptable bias percentage"
)

# Hallucination threshold
hallucination_threshold = st.sidebar.slider(
    "Hallucination Threshold",
    min_value=0,
    max_value=100,
    value=10,
    help="Set the threshold for acceptable hallucination percentage"
)

# Toggle for online search
use_online_search = st.sidebar.checkbox(
    "Use Online Search",
    value=True,
    help="Enable or disable online search to supplement the prompt"
)

# Maximum retries
max_retries = st.sidebar.number_input(
    "Maximum Retries",
    min_value=1,
    max_value=5,
    value=2,
    help="Set the maximum number of retries for biased or hallucinated outputs"
)

# Apply button
if st.sidebar.button("Apply Settings"):
    st.sidebar.success("Settings applied successfully!")


inp = st.text_input("Enter your query:")

if st.button("Run Workflow"):
    run_workflow(inp)   
    with open('ai_governance_workflow.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=800, scrolling=True)

