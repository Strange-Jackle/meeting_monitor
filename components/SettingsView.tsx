import React from 'react';
import { User, Lock, CreditCard, Bell, Shield, Mail } from 'lucide-react';

const SettingsView: React.FC = () => {
  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Settings Navigation */}
          <div className="w-full md:w-64 space-y-1">
            <h2 className="text-xl font-bold text-gray-900 mb-6 px-3">Settings</h2>

            <button className="w-full flex items-center gap-3 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium">
              <User size={18} /> Account
            </button>
            <button className="w-full flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg text-sm font-medium transition-colors">
              <Lock size={18} /> Security
            </button>
            <button className="w-full flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg text-sm font-medium transition-colors">
              <CreditCard size={18} /> Plan & Billing
            </button>
            <button className="w-full flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg text-sm font-medium transition-colors">
              <Bell size={18} /> Notifications
            </button>
            <button className="w-full flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg text-sm font-medium transition-colors">
              <Shield size={18} /> Team
            </button>
          </div>

          {/* Settings Content */}
          <div className="flex-1 max-w-3xl">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="p-6 border-b border-gray-100">
                <h3 className="text-lg font-bold text-gray-900">Account Information</h3>
                <p className="text-sm text-gray-500">Manage your public profile and private details</p>
              </div>

              <div className="p-8 space-y-8">
                {/* Profile Photo */}
                <div className="flex items-center gap-6">
                  <img src="https://picsum.photos/100/100" alt="Profile" className="w-20 h-20 rounded-full object-cover" />
                  <div>
                    <button className="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">Change Avatar</button>
                    <p className="text-xs text-gray-400 mt-2">JPG, GIF or PNG. Max size of 800K</p>
                  </div>
                </div>

                {/* Form */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">First Name</label>
                    <input type="text" defaultValue="Brian" className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Last Name</label>
                    <input type="text" defaultValue="Hughes" className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div className="md:col-span-2 space-y-2">
                    <label className="text-sm font-medium text-gray-700">Username</label>
                    <div className="flex">
                      <span className="inline-flex items-center px-3 rounded-l-lg border border-r-0 border-gray-200 bg-gray-50 text-gray-500 text-sm">fusetheme.com/</span>
                      <input type="text" defaultValue="brianh" className="flex-1 px-4 py-2 border border-gray-200 rounded-r-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                    </div>
                  </div>
                  <div className="md:col-span-2 space-y-2">
                    <label className="text-sm font-medium text-gray-700">Bio</label>
                    <textarea rows={4} className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" defaultValue="Hey! This is Brian; husband, father and gamer. I'm mostly passionate about bleeding edge tech and chocolate!"></textarea>
                    <p className="text-xs text-gray-400">Brief description for your profile.</p>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-4 pt-6 border-t border-gray-100">
                  <button className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900">Cancel</button>
                  <button className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 shadow-sm shadow-blue-200">Save Changes</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;