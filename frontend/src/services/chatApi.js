// import axios from "axios";

// export const chatWithAgent = async (
//   customerId,
//   message,
//   conversationHistory = [],
// ) => {
//   const response = await axios.post("http://localhost:8000/api/chat", {
//     customer_id: customerId,
//     message,
//     conversation_history: conversationHistory,
//   });
//   return response.data;
// };

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

export const gethistory = async (customerId) => {
  const response = await axios.get(
    `http://localhost:8000/api/payload/${customerId}`,
  );
  return response.data;
};

export const getCustomerProfile = async (customerId, roleId = "1") => {
  const response = await axios.get(
    `http://localhost:8000/api/customer/${customerId}/${roleId}`,
  );
  return response.data;
};
