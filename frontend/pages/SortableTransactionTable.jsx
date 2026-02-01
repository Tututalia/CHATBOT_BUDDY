import React, { useState, useMemo, useEffect } from "react";
import { ChevronUpIcon, ChevronDownIcon } from "@heroicons/react/24/outline";

const getStatusClasses = (status) => {
  switch (status) {
    case "Success":
      return "bg-green-100 text-green-800";
    case "Failed":
      return "bg-red-100 text-red-800";
    case "Pending":
      return "bg-yellow-100 text-yellow-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
};

// Accept 'storeId' as a prop to filter the data
export default function SortableTransactionTable({ storeId }) {
  const [transactions, setTransactions] = useState([]);
  const [storeName, setStoreName] = useState("Unknown Store");
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState({
    key: "date",
    direction: "descending",
  });
  const [lastUpdated, setLastUpdated] = useState(Date.now());
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Fetch transactions from API
  useEffect(() => {
    const fetchTransactions = async () => {
      if (!storeId || storeId.length === 0) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await fetch(
          `http://localhost:8000/api/store/${storeId}/transactions?time_range=all`,
        );
        const data = await response.json();

        if (data.error) {
          console.error("Error fetching transactions:", data.error);
          setTransactions([]);
          setStoreName("Unknown Store");
        } else {
          setTransactions(data.transactions || []);
          setStoreName(data.store_name || "Unknown Store");
        }
      } catch (error) {
        console.error("Error fetching transaction data:", error);
        setTransactions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [storeId, lastUpdated]);

  // Set up auto-refresh every 10 seconds
  useEffect(() => {
    const intervalId = setInterval(() => {
      console.log("Refreshing transactions...");
      setLastUpdated(Date.now());
    }, 10000);

    return () => clearInterval(intervalId);
  }, []);

  // Sort transactions
  const sortedTransactions = useMemo(() => {
    let sortableItems = [...transactions];
    sortableItems.sort((a, b) => {
      // Special sorting logic for dates
      if (sortConfig.key === "date") {
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        if (dateA < dateB) return sortConfig.direction === "ascending" ? -1 : 1;
        if (dateA > dateB) return sortConfig.direction === "ascending" ? 1 : -1;
        return 0;
      }
      // General sorting for strings/numbers
      if (a[sortConfig.key] < b[sortConfig.key]) {
        return sortConfig.direction === "ascending" ? -1 : 1;
      }
      if (a[sortConfig.key] > b[sortConfig.key]) {
        return sortConfig.direction === "ascending" ? 1 : -1;
      }
      return 0;
    });
    return sortableItems;
  }, [transactions, sortConfig]);

  // Calculate pagination
  const totalPages = Math.ceil(sortedTransactions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedTransactions = sortedTransactions.slice(startIndex, endIndex);

  // Reset to page 1 when sorting changes
  useEffect(() => {
    setCurrentPage(1);
  }, [sortConfig]);

  const handlePreviousPage = () => {
    setCurrentPage((prev) => Math.max(prev - 1, 1));
  };

  const handleNextPage = () => {
    setCurrentPage((prev) => Math.min(prev + 1, totalPages));
  };

  const handlePageClick = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

  const requestSort = (key) => {
    let direction = "ascending";
    if (sortConfig.key === key && sortConfig.direction === "ascending") {
      direction = "descending";
    }
    setSortConfig({ key, direction });
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return null;
    return sortConfig.direction === "ascending" ? (
      <ChevronUpIcon className="w-4 h-4 ml-1 inline" />
    ) : (
      <ChevronDownIcon className="w-4 h-4 ml-1 inline" />
    );
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

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold mb-4">
          Transaction History for: {storeName}
        </h2>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          <p className="ml-4 text-gray-600">Loading transactions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold mb-4">
        Transaction History for: {storeName}
      </h2>
      {sortedTransactions.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">No transactions found for this store.</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <HeaderCell title="ID" sortKey="id" />
                  <HeaderCell title="Date" sortKey="date" />
                  <HeaderCell title="User Name" sortKey="user_name" />
                  <HeaderCell title="Product" sortKey="product" />
                  <HeaderCell title="Qty" sortKey="qty" />
                  <HeaderCell title="Mode" sortKey="mode" />
                  <HeaderCell title="Status" sortKey="status" />
                  <HeaderCell title="Amount" sortKey="amount" />
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Phone
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedTransactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {transaction.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.user_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.product}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.qty}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.mode}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClasses(transaction.status)}`}
                      >
                        {transaction.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-semibold">
                      ₹{transaction.amount.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {transaction.address}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.phone}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="flex items-center justify-between mt-6">
            <div className="text-sm text-gray-700">
              Showing <span className="font-semibold">{startIndex + 1}</span> to{" "}
              <span className="font-semibold">
                {Math.min(endIndex, sortedTransactions.length)}
              </span>{" "}
              of{" "}
              <span className="font-semibold">{sortedTransactions.length}</span>{" "}
              transactions
            </div>

            <div className="flex items-center gap-2">
              {/* Previous Button */}
              <button
                onClick={handlePreviousPage}
                disabled={currentPage === 1}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  currentPage === 1
                    ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                    : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-md"
                }`}
              >
                Previous
              </button>

              {/* Page Numbers */}
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                  (pageNumber) => {
                    // Show first page, last page, current page, and pages around current
                    if (
                      pageNumber === 1 ||
                      pageNumber === totalPages ||
                      (pageNumber >= currentPage - 1 &&
                        pageNumber <= currentPage + 1)
                    ) {
                      return (
                        <button
                          key={pageNumber}
                          onClick={() => handlePageClick(pageNumber)}
                          className={`px-4 py-2 rounded-lg font-medium transition-all ${
                            currentPage === pageNumber
                              ? "bg-indigo-600 text-white shadow-md"
                              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                          }`}
                        >
                          {pageNumber}
                        </button>
                      );
                    } else if (
                      pageNumber === currentPage - 2 ||
                      pageNumber === currentPage + 2
                    ) {
                      return (
                        <span key={pageNumber} className="px-2 text-gray-500">
                          ...
                        </span>
                      );
                    }
                    return null;
                  },
                )}
              </div>

              {/* Next Button */}
              <button
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  currentPage === totalPages
                    ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                    : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-md"
                }`}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
