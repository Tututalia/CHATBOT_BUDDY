import React, { createContext, useState, useContext } from 'react';
// Import the initial static data
import initialAdminData from './data/admin.json';

// 1. Create the Context
const AdminDataContext = createContext();

// 2. Create a custom hook to easily consume the context
export const useAdminData = () => useContext(AdminDataContext);

// 3. Create the Provider Component
export const AdminDataProvider = ({ children }) => {
  // Use useState to manage the data dynamically
  const [records, setRecords] = useState(initialAdminData);

  const addTransaction = (newTransaction) => {
    setRecords((prevData) => ({
      ...prevData,
      // Update only the transactions array
      transactions: [...prevData.transactions, newTransaction],
    }));
    // You could also add logic here to update storeStats, users purchases list, etc.
  };

  const addPurchaseToUser = (userId, purchaseId) => {
    setRecords(prevData => ({
      ...prevData,
      users: prevData.users.map(user => {
        if (user.id === userId) {
          // Return a NEW user object with an updated purchases array
          return {
            ...user,
            purchases: [...user.purchases, purchaseId]
          };
        }
        // Return the original user object if it doesn't match the ID
        return user;
      })
    }));
  };

   const updateTransactionStatus = (transactionId, newStatus) => {
    setRecords(prevData => ({
      ...prevData,
      transactions: prevData.transactions.map(transaction => {
        // Check if the current transaction matches the ID we want to update
        if (transaction.id === transactionId) {
          // Return a NEW transaction object with the updated status
          return {
            ...transaction,
            orderStatus: newStatus
          };
        }
        // Return the original transaction object if it doesn't match the ID
        return transaction;
      })
    }));
  };

  

  // Function to add a new record
  // const addRecord = (newRecord) => {
  //   setRecords((prevRecords) => [...prevRecords, newRecord]);
  // };

  // The value provided to consuming components
  const value = {
    records,
    addTransaction,
    addPurchaseToUser,
    updateTransactionStatus
  };

  return (
    <AdminDataContext.Provider value={value}>
      {children}
    </AdminDataContext.Provider>
  );
};