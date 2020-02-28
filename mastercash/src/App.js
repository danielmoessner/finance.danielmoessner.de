import React from "react";

function App() {
  return (
    <div class="bg-white rounded-lg p-6">
      <img
        class="h-16 w-16 rounded-full mx-auto"
        src="https://randomuser.me/api/portraits/women/17.jpg"
        alt="test"
      />
      <div class="text-center">
        <h2 class="text-lg">Erin Lindford</h2>
        <div class="text-purple-500">Customer Support</div>
        <div class="text-gray-600">erinlindford@example.com</div>
        <div class="text-gray-600">(555) 765-4321</div>
      </div>
    </div>
  );
}

export default App;
