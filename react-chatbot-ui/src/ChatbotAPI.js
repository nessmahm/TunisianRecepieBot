import axios from "axios";

const API = {
  GetChatbotResponse: async message => {
    try {
      const response = await axios.post("http://127.0.0.1:8000/predict", {
        prompt: message
      });

      return response.data.response;
    } catch (error) {
      console.error("Error while fetching chatbot response:", error);
      return "Sorry, something went wrong. Please try again.";
    }
  }
};

export default API;
