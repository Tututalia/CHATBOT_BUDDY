import axios from "axios";

export const chatWithAgent = async (
  customerId,
  message,
  conversationHistory = [],
) => {
  const response = await axios.post("http://localhost:8000/api/chat", {
    customer_id: customerId,
    message,
    conversation_history: conversationHistory,
  });
  return response.data;
};
