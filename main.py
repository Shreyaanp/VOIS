from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from conversation_bot import ConversationBot  # Assuming your class is in conversation_bot.py
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:3000",  # Localhost for development
    "https://vois.shreyaan.work"  # Your deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

bot = ConversationBot()  # Instantiates the ConversationBot class

class UserInput(BaseModel):
    user_message: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/initialize/")
async def initialize():
    initial_response = bot.get_initial_response()
    bot.update_conversation_state("assistant", initial_response)
    return {"initial_question": bot.initial_question}

@app.post("/user_message/")
async def user_message(input: UserInput):
    if bot.is_end_goal_achieved():
        return {"bot_response": "The conversation goal has been achieved or the conversation was ended by the user."}

    user_message = input.user_message  # Extract the user message
    bot.update_conversation_state("user", user_message)

    # Handle personal info requests directly or generate a response
    personal_info_response = bot.handle_personal_info_request(user_message)
    if personal_info_response:
        bot_response = personal_info_response
    else:
        bot_response = bot.generate_response(user_message)  # Generate response using the new method

    bot.update_conversation_state("system", bot_response)
    return {"bot_response": bot_response}

@app.get("/check_goal/")
async def check_goal():
    return {"end_goal_achieved": bot.is_end_goal_achieved()}

@app.post("/end_conversation/")
async def end_conversation():
    bot.conversation_state["user_quit"] = True
    return {"message": "Conversation ended by user."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
