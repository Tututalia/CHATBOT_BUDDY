import React from 'react'
// import data from '../data/admin.json'
import { useAdminData } from '../AdminDataContext';


export default function UserJourney() {
  var { records } = useAdminData();
  const { addTransaction } = useAdminData();
  


  var data = records

 

  

  console.log("records",records)

  const user = data.users.find(u => u.id === "u1")
  const productMap = {}
  user.purchases.forEach(pid => {
    if(productMap[pid]==undefined){
      productMap[pid]=1
    }else{
      productMap[pid]=productMap[pid]+1
    }
     
  })

  return (
    <div className="bg-[#0d0d0d] text-gray-200 font-sans text-[1.4vw] rounded-xl shadow p-6 shadow">
      <h2 className="text-lg font-semibold mb-4">User Journey — {user.name}</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.keys(productMap).map(pid => {
          const prod = data.products.find(p => p.id === pid)
          return (
            <div key={pid} className="border rounded-lg p-4 flex gap-4 items-center">
              <img src={prod.image} alt={prod.name} className="w-20 h-20 object-cover rounded" />
              <div>
                <div className="font-medium">{prod.name}</div>
                <div className="text-sm text-gray-500">₹{prod.price}</div>
                <div className="text-sm mt-2">Qty: <span className="font-semibold">{productMap[pid]}</span></div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
