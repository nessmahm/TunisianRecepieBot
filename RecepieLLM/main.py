from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from recepieModel import ask_the_bot
app = FastAPI()

# Enable CORS to allow your React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

class InputData(BaseModel):
    prompt: str

@app.post("/predict")
def get_prediction(data: InputData):
    result = ask_the_bot(data.prompt)  # Your model's response logic
    return {"response": result}
