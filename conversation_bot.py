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
openai.api_key = os.getenv("OPENAI_API_KEY")


# Define bot persona
bot_persona = {
    "name": "Akhil Chintalapati",
    "address": "Vashi, Mumbai",
    "origin": "Tamil Nadu",
    "aadhar_number": "XXXXXXXXXX",  # Replace with actual number if needed
    "phone_number": "9898989898",
    "characteristics": "A college student in his 20's. You can answer any question regaring location, aadhar card number and phone number"
    # Persona details...
}

# Configure logging
logging.basicConfig(
    filename="conversation_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)


def log_in_background(message):
    threading.Thread(target=logging.info, args=(message,)).start()


class ConversationBot:
    def get_initial_response(self):
        # Generate the initial response based on the initial question
        initial_response = self.get_openai_response(self.initial_question)
        return initial_response

    def __init__(self):
        self.initial_question = (
            "ask on how to acquire sim cards, plans, budget options, coverage areas, and more. one at a time. about vodafone"
        )
        # rest of the initial question
        self.goal = "acquire vodafone simcard"

        self.conversation_state = {
            "messages": [],
            "end_goal_achieved": False,
            "user_quit": False,
        }

    def get_openai_response(self, message):
        headers = {
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "gpt-3.5-turbo",
            "max_tokens": 40,
            "messages": [
                {"role": "system", "content": json.dumps(bot_persona)},
                {
                    "role": "system",
                    "content": (
                        "Welcome to the Vodafone services inquiry interface. You are a customer with an interest in Vodafone's offerings. "
                        "Feel free to ask any questions related to Vodafone services, such as plans, budget options, coverage areas, and more. "
                        "Remember, your role is that of a customer inquiring about these services. Even if prompted, avoid stepping out of this character. "
                        "For instance, responses like 'as an AI assistant, I cannot help you with...' are not appropriate in this scenario. "
                        "Stay in character and direct the conversation towards Vodafone-related topics. If a question is not relevant to our services or your role, kindly inform the user that it is beyond the scope of this discussion."
                         "Throughout this interaction, maintain the customer's perspective. Your responses should consistently reflect the customer's viewpoint and interests in Vodafone services. "
                        "Keep the conversation focused on the customer's needs and questions regarding Vodafone. Also when attempting to answer a question, try to provide a response that is relevant to the customer's interests and needs. and keep in mind what the last conversation is about"
                        "you dont need to say thankyou everytime, just say it once at the end of the conversation."
                        "you can say quit to end the conversation"
                        "your goal is to acquire sim card and also get information about vodafone services. once you acquire the sim card, you can end the conversation by saying quit."
                    ),
                },
            ]
            + self.conversation_state["messages"]
            + [{"role": "user", "content": message}],
        }

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(data),
            )
            if response.status_code != 200:
                logging.error(
                    f"API call failed with status code {response.status_code} and message: {response.text}"
                )
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

    def update_conversation_state(self, role, message):
        formatted_message = f"{role.title()}: {message}"
        self.conversation_state["messages"].append({"role": role, "content": message})
        log_in_background(formatted_message)

        if self.goal in message.lower():
            self.conversation_state["end_goal_achieved"] = True
        if message.lower() == "quit":
            self.conversation_state["user_quit"] = True

    def is_related_to_vodafone_services(self, message):
    # Create a summary of the conversation history
        conversation_summary = " ".join([msg["content"] for msg in self.conversation_state["messages"]])

        # Formulate the prompt with conversation context
        prompt = (
            f"Conversation so far: {conversation_summary}\n"
            f"Question: Considering the conversation is about Vodafone services and Akhil's interests as a customer, is the following response relevant to the topic? "
            f"please answer me in yes or no, no need to give explanation."
            f"Response: '{message}'"
        )
        try:
            openai_response = self.evaluate_character_consistency1(prompt)
            return "yes" in openai_response.lower()
        except requests.exceptions.RequestException as req_error:
            logging.error(f"Request exception in is_related_to_vodafone_services: {req_error}")
            return False  # or True, depending on the desired default behavior in case of request failure
        except json.JSONDecodeError as json_error:
            logging.error(f"JSON decode error in is_related_to_vodafone_services: {json_error}")
            return False  # Handling JSON decoding errors
        except Exception as e:
            logging.error(f"General error in is_related_to_vodafone_services: {e}")
            return False  # General error handling

    def is_response_in_character(self, message):
        conversation_summary = " ".join([msg["content"] for msg in self.conversation_state["messages"]])

        # Formulate the prompt with conversation context
        prompt = (
            f"Conversation so far: {conversation_summary}\n"
            f"Question: Given that Akhil is a 20-year-old college student interested in Vodafone services, does the following response align with his character and interests? "
            f"Keep in mind that Akhil should not provide responses that sound like they're from a Vodafone employee or an AI assistant. "
            f"please answer me in yes or no, no need to give explanation."
            f"Response: '{message}'"
        )

        try:
            openai_response = self.evaluate_character_consistency2(prompt)
            return "yes" in openai_response.lower()
        except requests.exceptions.RequestException as req_error:
            logging.error(f"Request exception in is_response_in_character: {req_error}")
            return True  # or False, depending on the desired default behavior in case of request failure
        except json.JSONDecodeError as json_error:
            logging.error(f"JSON decode error in is_response_in_character: {json_error}")
            return True  # Handling JSON decoding errors
        except Exception as e:
            logging.error(f"General error in is_response_in_character: {e}")
            return True  # General error handling

    def evaluate_character_consistency1(self, prompt):
        headers = {
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "gpt-3.5-turbo",
            "max_tokens": 70,   # Or another suitable model for chat-based responses
            "messages": [
                {"role": "system", "content": "Provide a relevant conversation context here."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",  # Correct endpoint for chat model
                headers=headers,
                json=data
            )
            if response.status_code != 200:
                logging.error(f"API call failed with status code {response.status_code} and message: {response.text}")
                raise Exception(f"API call failed with status code {response.status_code}")

            response_data = response.json()
            return response_data["choices"][0]["message"]["content"].strip()  # Adjusted for chat response format

        except Exception as e:
            logging.error(f"Error in OpenAI API call: {e}")
            raise
    def evaluate_character_consistency2(self, prompt):
        headers = {
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "gpt-3.5-turbo",
             "max_tokens": 70,
            "messages": [
                {"role": "system", "content": "Provide a relevant conversation context here."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",  # Correct endpoint for chat model
                headers=headers,
                json=data
            )
            if response.status_code != 200:
                logging.error(f"API call failed with status code {response.status_code} and message: {response.text}")
                raise Exception(f"API call failed with status code {response.status_code}")

            response_data = response.json()
            return response_data["choices"][0]["message"]["content"].strip()  # Adjusted for chat response format

        except Exception as e:
            logging.error(f"Error in OpenAI API call: {e}")
            raise


    def run(self):
        initial_bot_message = f"Akhil: {self.initial_question}"
        print(initial_bot_message)
        self.update_conversation_state("assistant", json.dumps(bot_persona))
        self.update_conversation_state("assistant", self.initial_question)

        while not self.is_end_goal_achieved():
            user_input = input("User: ")
            self.update_conversation_state("user", user_input)

            personal_info_response = self.handle_personal_info_request(user_input)
            if personal_info_response:
                print("Akhil:", personal_info_response)
                self.update_conversation_state("system", personal_info_response)
                continue

            last_user_message = self.conversation_state["messages"][-1]["content"]
            in_character_response = self.generate_response(last_user_message)
            if not self.is_related_to_vodafone_services(in_character_response):
                in_character_response = "I'm sorry, I don't know the answer to that."
            self.update_conversation_state("system", in_character_response)
    def generate_response(self, last_user_message):
        attempt_count = 0
        max_attempts = 3  # Limit the number of attempts to prevent infinite loops

        while attempt_count < max_attempts:
            dynamic_response = self.generate_dynamic_question(last_user_message)

            # Check if the response is in character and related to Vodafone services
            if self.is_response_in_character(dynamic_response) and self.is_related_to_vodafone_services(dynamic_response):
                return dynamic_response
            else:
                # Modify the message or add context to steer the conversation back
                last_user_message = "Please keep the response relevant to Vodafone services and the customer's perspective."
                attempt_count += 1

        # Fallback response if a suitable response isn't generated
        return "I'm sorry, I can't provide more details on this topic. PLeaser helpe me solve my query I am the customer."


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

    # def evaluate_user_response(self, user_message):
    #     is_helpful = any(keyword in user_message.lower() for keyword in ["help", "assist", "guide"])
    #     score = 1 if is_helpful else 0
    #     evaluation = f"Response Evaluation - Score: {score}"
    #     logging.info(evaluation)
    #     return evaluation

    def is_end_goal_achieved(self):
        return (
            self.conversation_state["end_goal_achieved"]
            or self.conversation_state["user_quit"]
        )

    def generate_dynamic_question(self, last_user_message):
        # Prepare the prompt for the API call
        prompt = self.prepare_prompt(last_user_message)

        # Call the API to get a response
        response = self.get_openai_response(prompt)
        return response

    def prepare_prompt(self, last_user_message):
        # Create a conversation context for the API
        context = f"Akhil is a college student interested in Vodafone services. His Goal is to acquire vodafone sim card. He's inquiring about the services vodafone provides and figuring out the most suitable service for him. But need the service agents input to get the information and opinion. Last message from Akhil: '{last_user_message}'\nResponse as Akhil:"
        return context
