import os
import torch

from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    pipeline,
)

os.environ['HF_TOKEN'] = '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'

model_name = "meta-llama/Meta-Llama-3.1-8B"
device = 'cuda'
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
tokenizer.pad_token = tokenizer.unk_token
tokenizer.pad_token_id = tokenizer.unk_token_id

# Quantization configuration
compute_dtype = getattr(torch, "float16")
print('Compute type', compute_dtype)

bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
)

# Load the model and quantize it
model = AutoModelForCausalLM.from_pretrained(
          model_name,
          quantization_config=bnb_config,
          use_flash_attention_2=False, # set to True if you're using A100
          device_map={"": 0}, # device_map="auto" will cause a problem in the training
)
print('Model', model)

# Now you can use the model for inference
test_input = "what is Democracy"
input_ids = tokenizer.encode(test_input, return_tensors="pt")
output = model.generate(input_ids, max_length=256)
print(tokenizer.decode(output[0], skip_special_tokens=True))

pipeline_inst = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        use_cache=True,
        device_map="auto",
        max_length=256,
        do_sample=True,
        top_k=5,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
)

llm = HuggingFacePipeline(pipeline=pipeline_inst)

template = """<s>[INST] You are a respectful and helpful assistant,
respond always be precise, assertive and politely answer in few words conversational English.
Answer the question below from context below :
{question} [/INST] </s>
"""

def generate_response(question):
  prompt = PromptTemplate(template=template, input_variables=["question"])
  llm_chain = LLMChain(prompt=prompt, llm=llm)
  response = llm_chain.run({"question": question})
  print('response is:\n', response)
  return response

generate_response("Name the 3rd President of Kenya?")
generate_response("Tell me something interesting about Kenya?")

prompt = """ How does educating the citizen of Kenya help them know about their country and rights? """

generate_response(prompt) 
generate_response('What is 10+58')
generate_response('What is 11*58')
generate_response('How can democracy be hijacked?')

while True:
  prompt = input("Enter a prompt: ")
  generate_response(prompt)
