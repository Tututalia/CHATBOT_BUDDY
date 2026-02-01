import React, { useState, useMemo ,useEffect} from 'react';
// Note: Assuming the file path is correct relative to this component.
import data from '../data/admin.json'; 
import { useAdminData } from '../AdminDataContext';



import { ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

// var { data } = useAdminData();

const getStatusClasses = (status) => {
  switch (status) {
    case 'New': return 'bg-blue-100 text-blue-800';
    case 'In Progress': return 'bg-yellow-100 text-yellow-800';
    case 'Complete': return 'bg-green-100 text-green-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

// Accept 'storeId' as a prop to filter the data
export default function StoreDetailsTable({ storeId }) { 

   var { records } = useAdminData();

   var data =records

  console.log("storeId",storeId.length==0 || storeId==undefined || storeId=="")
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'descending' });

   const [lastUpdated, setLastUpdated] = useState(Date.now());

   // 2. Use useEffect to set up the interval timer
   useEffect(() => {
     const intervalId = setInterval(() => {
       console.log("Checking for updates and forcing re-render...");
       // Update the state with the current timestamp to force the component to re-render
       setLastUpdated(Date.now()); 
       
       // If useAdminData has an explicit fetch function, call it here instead of setLastUpdated
       // e.g., if useAdminData returned { records, fetchData }, you'd call fetchData()
     }, 10000); // Check every 5 seconds

     // Cleanup function to stop the timer when the component unmounts
     return () => clearInterval(intervalId);
   }, []); // Empty dependency array ensures this runs once when mounted

  // 1. Filter transactions based on the storeId prop
  const filteredTransactions = useMemo(() => {
    // Ensure data.transactions is an array before filtering
    if (!data.transactions || !Array.isArray(data.transactions)) return [];
    if(storeId.length==0 || storeId==undefined || storeId=="")
    {
      return data.transactions;
    }else{
       return data.transactions.filter(transaction => transaction.storeId === storeId);

    }
      
 
  }, [storeId,lastUpdated]); // Dependency on storeId

  // 2. Enrich the *filtered* data
  const enrichedTransactions = useMemo(() => {
    return filteredTransactions.map(transaction => {
        const user = data.users.find(u => u.id === transaction.userId);
        const product = data.products.find(p => p.id === transaction.productId);
        return {
            ...transaction,
            userName: user ? user.name : 'Unknown User',
            productName: product ? product.name : 'Unknown Product',
            userAddress: user ? user.address : 'N/A',
            userPhone: user ? user.phone : 'N/A',
        };
    });
  }, [filteredTransactions]); // Dependency on filteredTransactions

  // 3. Sort the *enriched* data
  const sortedTransactions = useMemo(() => {
    let sortableItems = [...enrichedTransactions];
    sortableItems.sort((a, b) => {
      // Special sorting logic for dates
      if (sortConfig.key === 'date') {
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        if (dateA < dateB) return sortConfig.direction === 'ascending' ? -1 : 1;
        if (dateA > dateB) return sortConfig.direction === 'ascending' ? 1 : -1;
        return 0;
      }
      // General sorting for strings/numbers
      if (a[sortConfig.key] < b[sortConfig.key]) {
        return sortConfig.direction === 'ascending' ? -1 : 1;
      }
      if (a[sortConfig.key] > b[sortConfig.key]) {
        return sortConfig.direction === 'ascending' ? 1 : -1;
      }
      return 0;
    });
    return sortableItems;
  }, [enrichedTransactions, sortConfig]); // Dependency on enrichedTransactions

  const requestSort = (key) => {
    let direction = 'ascending';
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return null;
    return sortConfig.direction === 'ascending' ? <ChevronUpIcon className="w-4 h-4 ml-1 inline" /> : <ChevronDownIcon className="w-4 h-4 ml-1 inline" />;
  };

  const HeaderCell = ({ title, sortKey }) => (
    <th 
      onClick={() => requestSort(sortKey)}
      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
    >
      {title}
      <SortIcon columnKey={sortKey} />
    </th>
  );

  const storeName = useMemo(() => {
    if(!storeId || storeId.length === 0 || storeId === undefined || storeId === "") {
      return 'All Stores';
    }
    
    const store = data.storeKeepers.find(s => s.id === storeId);
    return store?.name || 'Unknown Store';
  }, [storeId, data.storeKeepers]);

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Transaction History for: {storeName}</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <HeaderCell title="ID" sortKey="id" />
              <HeaderCell title="Date" sortKey="date" />
              <HeaderCell title="User Name" sortKey="userName" />
              <HeaderCell title="Product" sortKey="productName" />
              <HeaderCell title="Qty" sortKey="qty" />
              <HeaderCell title="Mode" sortKey="mode" />
              <HeaderCell title="Status" sortKey="orderStatus" />
              <HeaderCell title="Amount" sortKey="amount" />
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Address</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedTransactions.map((transaction) => (
              <tr key={transaction.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{transaction.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(transaction.date).toLocaleDateString()}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{transaction.userName}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{transaction.productName}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{transaction.qty}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{transaction.mode}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClasses(transaction.orderStatus)}`}>
                    {transaction.orderStatus}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-semibold">
                  ₹{transaction.amount.toFixed(2)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">{transaction.userAddress}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{transaction.userPhone}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}