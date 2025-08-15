export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Manage your chats and documents</p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat List */}
          <div className="lg:col-span-1 bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Your Chats</h2>
            <div className="space-y-3">
              <div className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <h3 className="font-medium">Sample Chat 1</h3>
                <p className="text-sm text-gray-500">2 hours ago</p>
              </div>
              <div className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <h3 className="font-medium">Sample Chat 2</h3>
                <p className="text-sm text-gray-500">1 day ago</p>
              </div>
            </div>
            <button className="w-full mt-4 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">
              New Chat
            </button>
          </div>
          
          {/* Chat Interface */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
            <div className="flex flex-col h-96">
              <div className="flex-1 border rounded-lg p-4 mb-4 overflow-y-auto">
                <p className="text-gray-500 text-center">Select a chat to start messaging</p>
              </div>
              
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Type your message..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}