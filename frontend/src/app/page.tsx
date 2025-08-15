import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Cognix-AI</h1>
          <p className="text-gray-600">RAG Chat Platform</p>
        </div>
        
        <div className="space-y-4">
          <Link
            href="/login"
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors block text-center"
          >
            Login
          </Link>
          
          <Link
            href="/signup"
            className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 transition-colors block text-center"
          >
            Sign Up
          </Link>
        </div>
        
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Upload documents and chat with AI</p>
        </div>
      </div>
    </div>
  );
}