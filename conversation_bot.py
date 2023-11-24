from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import threading
import requests
import json
import openai
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Use the environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')


# Define bot persona
bot_persona = {
    "name": "Akhil Chintalapati",
    "address": "Vashi, Mumbai",
    "origin": "Tamil Nadu",
    "aadhar_number": "XXXXXXXXXX",  # Replace with actual number if needed
    "phone_number": "9898989898",
    "characteristics": "A college student in his 20's. You can answer any question regaring location, adhar chrd and phone number"
    # Persona details...
}

# Configure logging
logging.basicConfig(filename='conversation_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

def log_in_background(message):
    threading.Thread(target=logging.info, args=(message,)).start()

class ConversationBot:
    def __init__(self, initial_question, goal):
        self.initial_question = initial_question
        self.goal = goal.lower()
        self.conversation_state = {
            "messages": [
                {"role": "customer", "content": json.dumps(bot_persona)},
                {"role": "customer", "content": "Hello, I'd like to know more about Vodafone services."},
                {"role": "customer", "content": ""}

            ],
            "end_goal_achieved": False,
            "user_quit": False
        }

    def get_openai_response(self):
        headers = {
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": self.conversation_state["messages"]
        }

        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(data))
            if response.status_code != 200:
                logging.error(f"API call failed with status code {response.status_code} and message: {response.text}")
                return "Sorry, I encountered an error with the API call."

            response_data = response.json()
            if "choices" not in response_data or not response_data["choices"]:
                logging.error("No 'choices' field in the API response.")
                return "Sorry, I encountered an error with the response format."

            bot_message = response_data["choices"][0]["message"]["content"]
            if not bot_message.strip():
                logging.info("Received empty response from API")
                return "I'm not sure how to respond to that. Could you clarify or ask something else?"

            return bot_message

        except Exception as e:
            logging.error(f"Error in calling OpenAI API: {e}")
            return "Sorry, I encountered an error. Could you repeat that?"

    def handle_personal_info_request(self, user_message):
        lower_case_message = user_message.lower()
        if "name" in lower_case_message:
            return f"My name is {bot_persona['name']}. I'm interested in Vodafone services."
        elif "address" in lower_case_message:
            return f"I live in {bot_persona['address']}, and I want to know about Vodafone's coverage here."
        elif "aadhar"  in lower_case_message:
            return f"My Aadhar card number is {bot_persona['aadhar_number']}."
        elif "phone number" in lower_case_message:
            return f"My phone number is {bot_persona['phone_number']}."
        return None
    # manual generation of dynamic question
    # def generate_dynamic_question(self, last_user_message):
    #     if "SIM card" in last_user_message:
    #         return "Could you tell me about the different types of Vodafone SIM cards available?"
    #     elif "plan" in last_user_message or "package" in last_user_message:
    #         return "I'd like to know more about Vodafone's plans and packages."
    #     else:
    #         return "Can you provide more details about Vodafone services?"

    def update_conversation_state(self, role, message):
        # Keep the role as 'customer', don't change it to 'customer'
        formatted_message = f"{role.title()}: {message}"
        self.conversation_state["messages"].append({"role": role, "content": message})
        log_in_background(formatted_message)

        if self.goal in message.lower():
            self.conversation_state["end_goal_achieved"] = True
        if message.lower() == "quit":
            self.conversation_state["user_quit"] = True

    def is_related_to_vodafone_services(self, message):
            return "vodafone" in message.lower()
    def is_response_in_character(self, message):
        # Add more robust checks here
        if "I can help you" in message or "I can assist you" in message:
            return False  # This sounds like an assistant's response
        # Add more checks as necessary
        return True

    def run(self):
        initial_bot_message = f"Akhil: {self.initial_question}"
        print(initial_bot_message)
        self.update_conversation_state("system", json.dumps(bot_persona))
        self.update_conversation_state("system", self.initial_question)

        while not self.is_end_goal_achieved():
            user_input = input("User: ")
            self.update_conversation_state("user", user_input)

            personal_info_response = self.handle_personal_info_request(user_input)
            if personal_info_response:
                print("Akhil:", personal_info_response)
                self.update_conversation_state("customer", personal_info_response)
                continue

            last_user_message = self.conversation_state["messages"][-1]["content"]
            dynamic_response = self.generate_dynamic_question(last_user_message)
            print("Akhil:", dynamic_response)
            self.update_conversation_state("customer", dynamic_response)

    def generate_response(self, last_user_message):
        # Loop until a valid, in-character response is generated
        while True:
            dynamic_response = self.generate_dynamic_question(last_user_message)
            if self.is_response_in_character(dynamic_response):
                return dynamic_response
            else:
                # Modify last_user_message or add context to steer the conversation
                last_user_message = "As a customer, I'm wondering, " + last_user_message
    def handle_personal_info_request(self, user_message):
        lower_case_message = user_message.lower()
        if "name" in lower_case_message:
            return f"My name is {bot_persona['name']}."
        elif "address" in lower_case_message:
            return f"I'm currently living in {bot_persona['address']}, but I'm originally from {bot_persona['origin']}."
        elif "aadhar" in lower_case_message:
            return f"My Aadhar card number is {bot_persona['aadhar_number']}."
        elif "phone number" in lower_case_message:
            return f"My phone number is {bot_persona['phone_number']}."
        return None

    def __init__(self, initial_question, goal):
        self.initial_question = initial_question
        self.goal = goal.lower()
        self.conversation_state = {
            "messages": [{"role": "system", "content": initial_question}],
            "end_goal_achieved": False,
            "user_quit": False
        }

    def get_openai_response(self):
        headers = {
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": self.conversation_state["messages"]
        }

        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(data))

            if response.status_code != 200:
                logging.error(f"API call failed with status code {response.status_code} and message: {response.text}")
                return "Sorry, I encountered an error with the API call."

            response_data = response.json()

            if "choices" not in response_data or not response_data["choices"]:
                logging.error("No 'choices' field in the API response.")
                return "Sorry, I encountered an error with the response format."

            bot_message = response_data["choices"][0]["message"]["content"]
            if not bot_message.strip():
                logging.info("Received empty response from API")
                return "I'm not sure how to respond to that. Could you clarify or ask something else?"

            return bot_message

        except Exception as e:
            logging.error(f"Error in calling OpenAI API: {e}")
            return "Sorry, I encountered an error. Could you repeat that?"

    def evaluate_user_response(self, user_message):
        is_helpful = any(keyword in user_message.lower() for keyword in ["help", "assist", "guide"])
        score = 1 if is_helpful else 0
        evaluation = f"Response Evaluation - Score: {score}"
        logging.info(evaluation)
        return evaluation
    def is_end_goal_achieved(self):
        return self.conversation_state["end_goal_achieved"] or self.conversation_state["user_quit"]


    def update_conversation_state(self, role, message):
        # Keep the role as 'customer', don't change it to 'customer'
        formatted_message = f"{role.title()}: {message}"
        self.conversation_state["messages"].append({"role": role, "content": message})
        log_in_background(formatted_message)

        if self.goal in message.lower():
            self.conversation_state["end_goal_achieved"] = True
        if message.lower() == "quit":
            self.conversation_state["user_quit"] = True


    def generate_dynamic_question(self, last_user_message):
        # Prepare the prompt for the API call
        prompt = self.prepare_prompt(last_user_message)

        # Call the API to get a response
        response = self.get_openai_response(prompt)
        return response

    def prepare_prompt(self, last_user_message):
        # Create a conversation context for the API
        context = f"Akhil is a college student interested in Vodafone services. He's inquiring about them. Last message from Akhil: '{last_user_message}'\nResponse as Akhil:"
        return context



def run(self):
        initial_bot_message = f"Akhil: {self.initial_question}"
        print(initial_bot_message)
        self.update_conversation_state("customer", json.dumps(bot_persona))
        self.update_conversation_state("customer", self.initial_question)

        while not self.is_end_goal_achieved():
            user_input = input("User: ")
            self.update_conversation_state("customer", user_input)

            personal_info_response = self.handle_personal_info_request(user_input)
            if personal_info_response and self.is_response_in_character(personal_info_response):
                print("Akhil:", personal_info_response)
                self.update_conversation_state("customer", personal_info_response)
                continue

            last_user_message = self.conversation_state["messages"][-1]["content"]
            in_character_response = self.generate_response(last_user_message)
            print("Akhil:", in_character_response)
            self.update_conversation_state("customer", in_character_response)
