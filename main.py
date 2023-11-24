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
    "https://vois-frontend.vercel.app"  # Your deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
initial_question = "Act like a 20 year old boy, Akhil  studying in an engineering college. Who wants to buy a Vodafone tv and broadband service and calling Vodafone customer care agent. Amit's first question will be 'Hello, I'm looking to get a Vodafone services but not sure how to proceed. Can you help?'? always wait for the customer service agent to respond before typing your next messaged . you are not to assist with any question outside of providing your details and quesries that is related to your task"
goal = "Acquire vodafone tv and broadband service"
bot = ConversationBot(initial_question, goal)

class UserInput(BaseModel):
    user_message: str

@app.get("/initialize/")
async def initialize():
    return {"initial_question": bot.initial_question}

@app.post("/user_message/")
async def user_message(input: UserInput):
    if bot.is_end_goal_achieved():
        return {"bot_response": "The conversation goal has been achieved or the conversation was ended by the user."}

    bot.update_conversation_state("user", input.user_message)
    bot_response = bot.get_openai_response()
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